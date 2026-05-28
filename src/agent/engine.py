import logging
from agents import Runner, InputGuardrailTripwireTriggered
from src.agent.handoffs import triage_agent

logger = logging.getLogger("matn_research.engine")

async def run_agent_pipeline(user_query: str) -> str:
  """Processes a user query through the triage router and safely handles any guardrail trips."""
  try:
    logger.info(f"Processing query through research engine: '{user_query[:50]}...'")

    result = await Runner.run(triage_agent, input=user_query)
    return result.final_output or "I'm sorry, I was unable to generate an analytical response for that query."

  except InputGuardrailTripwireTriggered:
    logger.warning(f"Guardrail Tripwire Triggered for query: '{user_query}'")
    return (
      "⚠️ **Access Denied / Request Blocked**\n\n"
      "This system is strictly dedicated to the academic study of **Matn Al-Waraqat** "
      "and its commentaries (*Sharhs*). Your query was flagged as unrelated. "
      "Please rephrase your question."
    )

  except Exception as e:
    logger.error(f"Unexpected execution failure in engine pipeline: {str(e)}")
    return "❌ An internal engine error occurred while processing your research request."
