import os
from typing import List, Callable
from agents import function_tool

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHAPTERS_DIR = os.path.join(BASE_DIR, "chapters")

def create_sharh_tool(file_name: str) -> Callable:

  file_path = os.path.join(CHAPTERS_DIR, file_name)
  base_name = os.path.splitext(file_name)[0]

  def tool_implementation() -> str:
    try:
      with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
    except FileNotFoundError:
      return f"Error: Chapter file {file_name} could not be located."

  tool_implementation.__name__ = f"read_{base_name}"
  tool_implementation.__doc__ = f"Retrieve full text commentary and research records from {file_name}."

  return function_tool(tool_implementation)

def load_sharh_tools() -> List[Callable]:
  tools = []

  if not os.path.exists(CHAPTERS_DIR):
    return tools

  for f_name in sorted(os.listdir(CHAPTERS_DIR)):
    if f_name.startswith("waraqat_") and f_name.endswith(".md"):
      tool_instance = create_sharh_tool(f_name)
      tools.append(tool_instance)

  return tools
