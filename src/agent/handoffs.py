from agents import Agent, handoff
from src.agent.tools import all_tools
from src.agent.guardrails import waraqat_relevance_guardrail

# 1. SPECIALIST: Core Waraqat Research Scholar
# Handles academic and textual queries using the dynamic markdown tools.
research_scholar_agent = Agent(
  name="Waraqat Scholar",
  handoff_description="Specialist for deep academic analysis, meanings, definitions, and explanations regarding Matn Al-Waraqat or its Sharh texts.",
  instructions=(
    "You are an expert Islamic Jurisprudence (Usul al-Fiqh) researcher specializing in Al-Juwayni's Matn Al-Waraqat.\n"
    "Use your available read_waraqat tools to fetch the actual text of the commentaries before answering. "
    "Provide rigorous, clear explanations of textual terms."
  ),
  tools=all_tools,
  input_guardrails=[waraqat_relevance_guardrail]
)

# 2. SPECIALIST: Administrative Bot Assistant
# Handles meta-questions, instructions on how to use the bot, and basic greetings.
admin_assistant_agent = Agent(
  name="Waraqat Bot Admin",
  handoff_description="Specialist for greetings, bot commands, usage guides, help requests, and overview descriptions of this system.",
  instructions=(
    "You are the structural coordinator of this research bot interface.\n"
    "Help the user understand how to run queries, list what files are currently available (waraqat_1 through waraqat_5), "
    "and politely forward them to the Waraqat Scholar if they ask textual or academic jurisprudence questions."
  )
)

# 3. ROOT ORCHESTRATOR: Homework & Research Triage Agent
# Inspects user intent first, delegating the full chat turn ownership to the correct agent.
triage_agent = Agent(
  name="Waraqat Layout Router",
  instructions=(
    "Analyze the incoming user request. Match it to the single best specialist agent "
    "based strictly on their handoff descriptions:\n"
    "- If they want academic explanation, translation, or commentary on a text section -> handoff to Waraqat Scholar.\n"
    "- If they are saying hello, asking how to use the bot, or seeking a list of features -> handoff to Waraqat Bot Admin."
  ),
  handoffs=[
    research_scholar_agent,
    handoff(admin_assistant_agent)
  ]
)

