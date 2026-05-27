from pydantic import BaseModel, Field
from agents import (
  Agent,
  GuardrailFunctionOutput,
  RunContextWrapper,
  Runner,
  TResponseInputItem,
  input_guardrail,
)

class WaraqatEvaluationOutput(BaseModel):
  is_relevant: bool = Field(
    ..., 
    description="True if relevant to Matn Al-Waraqat, Usul al-Fiqh, or its Sharh commentaries."
  )
  reasoning: str = Field(
    ..., 
    description="Brief technical explanation of relevance check."
  )

guardrail_checker_agent = Agent(
  name="Waraqat Relevance Evaluator",
  instructions=(
    "You are a strict academic filter. Evaluate if a user's query is explicitly "
    "seeking information, explanations, tools, or analysis regarding 'Matn Al-Waraqat' "
    "(by Imam Al-Juwayni) or its commentaries (Sharh).\n\n"
    "Set `is_relevant` to False if the query is unrelated general chat, coding, math, or other fields."
  ),
  output_type=WaraqatEvaluationOutput,
)

@input_guardrail
async def waraqat_relevance_guardrail(
  ctx: RunContextWrapper[None],
  agent: Agent,
  input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
  result = await Runner.run(guardrail_checker_agent, input, context=ctx.context)
  eval_report = result.final_output
  is_irrelevant = not eval_report.is_relevant

  return GuardrailFunctionOutput(
    output_info=eval_report,
    tripwire_triggered=is_irrelevant,
  )
