"""Runs one browser-use search in its own Python environment (/opt/bu in the image): browser-use pins an older
google-genai than the Research Agent uses, so the two never share one environment.

    echo '{"task": "...", "domains": [...], "executable": "...", "max_steps": 12, "model": "...", "project": "..."}' \
        | /opt/bu/bin/python bu_runner.py

Prints one JSON line: {"status", "notices", "steps", "steps_taken"}. Only research/browser_use_agent.py calls it.
"""
import asyncio
import json
import sys

from browser_use import Agent, BrowserProfile, ChatGoogle
from pydantic import BaseModel


class Notice(BaseModel):
    title: str
    url: str = ""
    date: str = ""
    models_named: list[str] = []
    hazard: str = ""
    covers_this_model: str = "maybe"


class Findings(BaseModel):
    status: str  # found | not_found | blocked
    notices: list[Notice] = []


async def main(args: dict) -> dict:
    steps: list = []

    def on_step(state, output, n):
        goal = getattr(getattr(output, "current_state", None), "next_goal", None) or getattr(output, "next_goal", "")
        steps.append({"n": n, "action": "browser_use", "say": str(goal)[:200], "url": getattr(state, "url", "")})

    llm = ChatGoogle(model=args["model"], vertexai=True, project=args["project"], location="global")
    profile = BrowserProfile(headless=True, allowed_domains=args["domains"],
                             **({"executable_path": args["executable"]} if args.get("executable") else {}))
    agent = Agent(task=args["task"], llm=llm, browser_profile=profile, output_model_schema=Findings, use_judge=False,
                  max_actions_per_step=3, step_timeout=90, register_new_step_callback=on_step)
    history = await agent.run(max_steps=args.get("max_steps", 12))
    raw = history.final_result()
    try:
        found = Findings.model_validate_json(raw) if raw else Findings(status="error")
    except ValueError:
        found = Findings(status="error")
    return {**found.model_dump(), "steps": steps, "steps_taken": len(history.history)}


if __name__ == "__main__":
    result = asyncio.run(main(json.loads(sys.stdin.read())))
    sys.stdout.write("\n" + json.dumps(result) + "\n")
