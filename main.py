import os
import sys
import asyncio
import logging
import httpx
import uvicorn
from fastapi import FastAPI, Request, Depends, Response, status

# Import from your internal layout structures
from src.telegram.auth import verify_telegram_webhook
from src.telegram.message import TelegramMessagePayload, format_agent_response
from src.agent.engine import run_agent_pipeline

# Configure global logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("matn_research.main")

# Load configuration tokens
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
IS_PRODUCTION = os.getenv("PRODUCTION", "false").lower() in ("true", "1", "yes")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

if not TELEGRAM_TOKEN:
  logger.critical("CRITICAL: TELEGRAM_TOKEN environment variable is missing! Exiting execution.")
  sys.exit(1)

# Initialize FastAPI instance for Production Webhook layout
app = FastAPI(title="Waraqat Research Bot Server")

async def send_message_to_telegram(chat_id: int, text: str) -> None:
  """
  Helper dependency that acts as the single transmission gateway 
  for dispatching structural responses back to Telegram.
  """
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
  """
  Production inbound HTTP POST target endpoint. Automatically protected 
  by your auth header verification dependency check.
  """
  payload_dict = await request.json()
  parsed_msg = TelegramMessagePayload.parse_update(payload_dict)
  
  if parsed_msg and parsed_msg.text:
    # Run the core agent logic and capture the output
    agent_output = await run_agent_pipeline(parsed_msg.text)
    # Forward result to delivery function
    await send_message_to_telegram(parsed_msg.chat_id, agent_output)

  return Response(status_code=status.HTTP_200_OK)

# =====================================================================
# DEVELOPMENT MODE: ASYNC LONG POLLING ENGINE
# =====================================================================
async def run_development_polling():
  """
  Long-polling loop runner that continuously fetches system updates 
  directly from Telegram without requiring external public ingress hooks.
  """
  logger.info("Initializing Local Development Engine: Using Long-Polling Mode.")
  
  # Remove any pre-existing production webhook configuration on Telegram's servers
  async with httpx.AsyncClient() as client:
    await client.get(f"{TELEGRAM_API_URL}/deleteWebhook")
  
  offset = 0
  async with httpx.AsyncClient(timeout=30.0) as client:
    while True:
      try:
        # Request new telemetry batches sequentially
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
  """
  Evaluates environmental variables and orchestrates execution layout targets.
  """
  if IS_PRODUCTION:
    logger.info("Starting production ASGI server layout on port 8000...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
  else:
    try:
      asyncio.run(run_development_polling())
    except KeyboardInterrupt:
      logger.info("Local development pooling stopped manually.")

if __name__ == "__main__":
  main()

