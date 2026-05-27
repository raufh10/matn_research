import os
from agents import Agent, handoff
from src.agent.tools import load_sharh_tools
from src.agent.guardrails import waraqat_relevance_guardrail

all_tools = load_sharh_tools()
scholar_agents = []

# ---------------------------------------------------------------------
# 1. SPECIALISTS: 1 Agent Per Waraqat Tool
# ---------------------------------------------------------------------
for tool in all_tools:
  volume_name = tool.name.replace("read_", "")
  formatted_volume = volume_name.replace("_", " ").title()

  volume_scholar = Agent(
    name=f"Waraqat_{volume_name.split('_')[-1]}_Expert",
    handoff_description=f"Expert for text, definitions, or commentaries in {formatted_volume}.",
    instructions=(
      f"You are a scholar for {formatted_volume}. Always call `{tool.name}` "
      "first to read the text before answering. Provide deep, text-based explanations."
    ),
    tools=[tool]
  )

  scholar_agents.append(volume_scholar)


# ---------------------------------------------------------------------
# 2. SPECIALIST: Administrative Bot Assistant
# ---------------------------------------------------------------------
admin_assistant_agent = Agent(
  name="Waraqat_Bot_Admin",
  handoff_description="Handles greetings, usage guides, help requests, and general system overviews.",
  instructions=(
    "Help the user with commands, available files, and navigation. Forward "
    "academic questions back to the triage system."
  )
)

# ---------------------------------------------------------------------
# 3. ROOT ORCHESTRATOR: Triage Agent with Guardrail
# ---------------------------------------------------------------------
all_handoff_targets = [handoff(s) for s in scholar_agents] + [handoff(admin_assistant_agent)]

triage_agent = Agent(
  name="Waraqat_Layout_Router",
  instructions=(
    "Route requests based on handoff descriptions:\n"
    "- Text/academic questions go to the specific volume expert.\n"
    "- Greetings, system help, or features go to Waraqat Bot Admin."
  ),
  handoffs=all_handoff_targets,
  input_guardrails=[waraqat_relevance_guardrail]
)

