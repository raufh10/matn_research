import logging
from agents import Runner, InputGuardrailTripwireTriggered
from src.agent.handoffs import triage_agent

# Setup engine logger
logger = logging.getLogger("matn_research.engine")

async def run_agent_pipeline(user_query: str) -> str:
  """
  Executes the core multi-agent research pipeline.
  
  Takes an incoming raw message from Telegram, runs it through the pre-execution 
  input guardrails via the Triage Agent, routes it to the appropriate specialist,
  and safely handles any tripwire flags.
  
  Args:
    user_query (str): The raw incoming chat string from the user.
    
  Returns:
    str: The markdown-formatted response string meant for the end user.
  """
  try:
    logger.info(f"Processing query through research engine: '{user_query[:50]}...'")
    
    # Run the query through the orchestration pipeline (includes Triage -> Specialists + Tools)
    result = await Runner.run(triage_agent, input=user_query)
    
    # Return the final derived response text
    return result.final_output or "I'm sorry, I was unable to generate an analytical response for that query."

  except InputGuardrailTripwireTriggered:
    logger.warning(f"Guardrail Tripwire Triggered for query: '{user_query}'")
    # Custom graceful fallback text when the input evaluation agent rejects the query
    return (
      "⚠️ **Access Denied / Request Blocked**\n\n"
      "This system is strictly dedicated to the academic study of **Matn Al-Waraqat** "
      "and its commentaries (*Sharhs*). Your query was flagged as unrelated. "
      "Please rephrase your question to target Islamic Jurisprudence (*Usul al-Fiqh*) frameworks."
    )

  except Exception as e:
    logger.error(f"Unexpected execution failure in engine pipeline: {str(e)}")
    return "❌ An internal engine error occurred while processing your research request."

