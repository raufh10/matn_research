import os
import secrets
from fastapi import Header, HTTPException, status

TELEGRAM_SECRET_TOKEN = os.getenv("TELEGRAM_SECRET_TOKEN")

def verify_telegram_webhook(
  x_telegram_bot_api_secret_token: str = Header(None, alias="X-Telegram-Bot-API-Secret-Token")
) -> bool:

  if not TELEGRAM_SECRET_TOKEN:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Server configuration error: Webhook token missing from host environment."
    )

  if (
    not x_telegram_bot_api_secret_token or
    not secrets.compare_digest(x_telegram_bot_api_secret_token, TELEGRAM_SECRET_TOKEN)
  ):
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Unauthorized request origin. Webhook token validation failed."
    )

  return True
