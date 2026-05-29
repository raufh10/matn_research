import os
from agents import Agent, handoff
from src.agent.tools import load_sharh_tools
from src.agent.guardrails import waraqat_relevance_guardrail

all_tools = load_sharh_tools()
scholar_agents = []

# ---------------------------------------------------------------------
# 1. SPECIALISTS: 1 Agent Per Waraqat Tool (terminal — no handoffs)
# ---------------------------------------------------------------------
for tool in all_tools:
  volume_name = tool.name.replace("read_", "")
  formatted_volume = volume_name.replace("_", " ").title()

  volume_scholar = Agent(
    name=f"Waraqat_Chapter_{volume_name.split('_')[-1]}_Expert",
    handoff_description=(
      f"Expert for text, definitions, or commentaries in Chapter {formatted_volume}."
    ),
    instructions=(
      f"You are a scholar specializing in Al Waraqat Chapter {formatted_volume}. "
      f"Always call `{tool.name}` first to read the source text before answering. "
      "Provide deep, text-based explanations grounded in the retrieved content. "
      "Do not hand off or escalate — answer fully and conclude your response. "
      "Always respond in English by default. Arabic source text may be quoted as-is, "
      "but all explanations, definitions, and commentary must be in English."
    ),
    tools=[tool],
  )

  scholar_agents.append(volume_scholar)

# ---------------------------------------------------------------------
# 2. SPECIALIST: Administrative Bot Assistant (terminal — no handoffs)
# ---------------------------------------------------------------------
admin_assistant_agent = Agent(
  name="Waraqat_Bot_Admin",
  handoff_description=(
    "Handles greetings, usage guides, help requests, and general system overviews."
  ),
  instructions=(
    "You are the Waraqat bot assistant. Help users with available commands, "
    "file listings, and how to navigate the system. "
    "If the user asks an academic or textual question about Waraqat content, "
    "politely inform them to ask about a specific volume directly — "
    "do NOT forward, escalate, or attempt any handoff. "
    "Always respond in English by default."
  ),
)

# ---------------------------------------------------------------------
# 3. ROOT ORCHESTRATOR: Triage Agent with Guardrail
# ---------------------------------------------------------------------
all_handoff_targets = scholar_agents + [admin_assistant_agent]

triage_agent = Agent(
  name="Waraqat_Layout_Router",
  instructions=(
    "You are the routing agent for the Waraqat research bot. "
    "Your only job is to read the user's message and hand off to the correct agent.\n\n"
    "Routing rules:\n"
    "- Academic, textual, or definition questions → hand off to the matching volume expert.\n"
    "- Greetings, help requests, system questions, or feature overviews → hand off to Waraqat_Bot_Admin.\n"
    "- If the volume is unclear, route to Waraqat_Bot_Admin.\n"
    "- Never answer academic questions yourself — always delegate to a specialist.\n"
    "Always respond in English by default."
  ),
  handoffs=all_handoff_targets,
  input_guardrails=[waraqat_relevance_guardrail],
)
