"""Example custom adapter. Import this module before using entrypoint custom_capitals."""
from agentbench_lite.agents import register_agent

@register_agent("custom_capitals")
def capitals_agent(task_input: str, settings: dict) -> str:
    mapping = {"france": "Paris", "japan": "Tokyo"}
    for country, capital in mapping.items():
        if country in task_input.lower():
            return capital
    return "I don't know."
