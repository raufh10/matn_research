import os
from agents import function_tool

# Ensure path calculations resolve correctly relative to root layout directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SHARHS_DIR = os.path.join(BASE_DIR, "sharhs")

def create_sharh_tool(file_name: str):
  """
  Factory function to dynamically build and register isolated function tools
  for reading specific Matn Al-Waraqat commentaries.
  """
  file_path = os.path.join(SHARHS_DIR, file_name)
  base_name = os.path.splitext(file_name)[0]  # e.g., 'waraqat_1'
  
  def tool_implementation() -> str:
    try:
      with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
    except FileNotFoundError:
      return f"Error: Commentary file {file_name} could not be located."

  # Dynamically assign native metadata properties so the SDK parses them properly
  tool_implementation.__name__ = f"read_{base_name}"
  tool_implementation.__doc__ = f"Retrieve full text commentary and research records from {file_name}."

  # Wrap with the official openai-agents function_tool decorator
  return function_tool(tool_implementation)


# ---------------------------------------------------------------------
# Dynamic Tool Registry Layout Generation
# ---------------------------------------------------------------------
all_tools = []

if os.path.exists(SHARHS_DIR):
  # Sort files numerically so tool arrays load deterministically
  for f_name in sorted(os.listdir(SHARHS_DIR)):
    if f_name.startswith("waraqat_") and f_name.endswith(".md"):
      tool_instance = create_sharh_tool(f_name)
      all_tools.append(tool_instance)
      
      # Expose tools globally inside module namespace for engine imports
      globals()[tool_instance.__name__] = tool_instance

