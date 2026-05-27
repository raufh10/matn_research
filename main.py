import os
import sys
import asyncio
import logging
import httpx
import uvicorn
from fastapi import FastAPI, Request, Depends, Response, status

from src.telegram.auth import verify_telegram_webhook
from src.telegram.message import TelegramMessagePayload, format_agent_response
from src.agent.engine import run_agent_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("matn_research.main")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

if not TELEGRAM_TOKEN:
  logger.critical("CRITICAL: TELEGRAM_TOKEN environment variable is missing! Exiting execution.")
  sys.exit(1)

app = FastAPI(title="Waraqat Research Bot Server")

async def send_message_to_telegram(chat_id: int, text: str) -> None:
  """Formats and transmits the agent's response back to the specified Telegram chat."""
  safe_text = format_agent_response(text)
  async with httpx.AsyncClient() as client:
    try:
      response = await client.post(
        f"{TELEGRAM_API_URL}/sendMessage",
        json={
          "chat_id": chat_id,
          "text": safe_text,
          "parse_mode": "MarkdownV2"
        },
        timeout=10.0
      )
      if response.status_code != 200:
        logger.error(f"Telegram API Error [{response.status_code}]: {response.text}")
    except Exception as e:
      logger.error(f"Failed to transmit network message to Telegram: {str(e)}")

# =====================================================================
# PRODUCTION MODE: WEBHOOK ROUTING VIA FASTAPI
# =====================================================================
@app.post("/webhook", dependencies=[Depends(verify_telegram_webhook)])
async def handle_webhook_update(request: Request):
  """Handles inbound production webhook updates from Telegram via an authenticated POST endpoint."""
  payload_dict = await request.json()
  parsed_msg = TelegramMessagePayload.parse_update(payload_dict)

  if parsed_msg and parsed_msg.text:
    agent_output = await run_agent_pipeline(parsed_msg.text)
    await send_message_to_telegram(parsed_msg.chat_id, agent_output)

  return Response(status_code=status.HTTP_200_OK)

# =====================================================================
# DEVELOPMENT MODE: ASYNC LONG POLLING ENGINE
# =====================================================================
async def run_development_polling():
  """Runs a long-polling loop to fetch updates from Telegram during local development."""
  logger.info("Initializing Local Development Engine: Using Long-Polling Mode.")

  async with httpx.AsyncClient() as client:
    await client.get(f"{TELEGRAM_API_URL}/deleteWebhook")

  offset = 0
  async with httpx.AsyncClient(timeout=30.0) as client:
    while True:
      try:
        response = await client.get(f"{TELEGRAM_API_URL}/getUpdates", params={"offset": offset, "timeout": 20})
        if response.status_code != 200:
          await asyncio.sleep(5)
          continue

        updates = response.json().get("result", [])
        for update in updates:
          offset = update.get("update_id") + 1
          parsed_msg = TelegramMessagePayload.parse_update(update)

          if parsed_msg and parsed_msg.text:
            logger.info(f"Local poll received update message from chat ID {parsed_msg.chat_id}")
            agent_output = await run_agent_pipeline(parsed_msg.text)
            await send_message_to_telegram(parsed_msg.chat_id, agent_output)
      except asyncio.CancelledError:
        break
      except Exception as e:
        logger.error(f"Polling connection failure: {str(e)}")
        await asyncio.sleep(5)

# =====================================================================
# APP ENTRY INTERFACE ORCHESTRATION
# =====================================================================
def main():
  """Evaluates the runtime environment setting and kicks off either the webhook server or local polling."""
  if ENVIRONMENT == "production":
    logger.info("Starting production ASGI server layout on port 8000...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
  else:
    try:
      asyncio.run(run_development_polling())
    except KeyboardInterrupt:
      logger.info("Local development pooling stopped manually.")

if __name__ == "__main__":
  main()
