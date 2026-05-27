from pydantic import BaseModel, Field
import telegramify_markdown

class TelegramMessagePayload(BaseModel):
  """Parses only the vital properties needed from an incoming nested Telegram update event."""
  chat_id: int = Field(..., alias="chat_id")
  text: str | None = Field(None, alias="text")

  @classmethod
  def parse_update(cls, update_data: dict):
    """Extracts structural chat data and skips non-message events like edits or inline queries."""
    message = update_data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text")

    if not chat_id:
      return None

    return cls(chat_id=chat_id, text=text)

def format_agent_response(raw_text: str) -> str:
  """Converts standard agent Markdown strings into safe Telegram-compatible MarkdownV2 strings."""
  if not raw_text:
    return ""

  return telegramify_markdown.markdownify(raw_text)
