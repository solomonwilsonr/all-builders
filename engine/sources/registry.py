"""The source registry (data/source_registry_japac.yaml): which official sources exist, how they may be reached, under
what terms, and which ones answer for each market. Adapters are loaded from here, so a source whose access is not
verified simply never runs.
"""
import importlib
import os
from functools import lru_cache
from pathlib import Path

import yaml

PATH = Path(os.environ.get("SAFESHELF_SOURCE_REGISTRY",
                           Path(__file__).resolve().parents[2] / "data" / "source_registry_japac.yaml"))
RUNNABLE = {"verified"}  # plus key_required with its key set, and browser_only with the Research Agent configured


@lru_cache(maxsize=1)
def load() -> dict:
    data = yaml.safe_load(PATH.read_text())
    data["by_id"] = {s["id"]: s for s in data["sources"]}
    return data


def source(source_id: str) -> dict:
    return load()["by_id"][source_id]


def all_sources() -> list[dict]:
    return load()["sources"]


def market(code: str | None) -> dict:
    return load()["markets"].get((code or "").upper(), {})


def market_name(code: str | None) -> str:
    return market(code).get("name") or (code or "unknown market")


def local_sources(code: str | None) -> list[str]:
    return list(market(code).get("local", []))


def global_sources() -> list[str]:
    return list(load().get("global", []))


def runnable(entry: dict) -> tuple[bool, str]:
    """(may this adapter run here, why not in plain words)."""
    status = entry["access_status"]
    if os.environ.get(f"SAFESHELF_DISABLE_{entry['id'].upper()}") == "1":
        return False, "switched off on this server"
    if status in RUNNABLE:
        return True, ""
    if status == "key_required":
        key = entry.get("key_env")
        return (True, "") if key and os.environ.get(key) else (False, f"needs an API key ({key}) that is not set up")
    if status == "browser_only":
        if os.environ.get("SAFESHELF_RESEARCH_URL"):
            return True, ""
        return False, "only searchable in a browser, and the Research Agent is not configured here"
    if status == "blocked":
        return False, f"the site refuses automated requests (checked {entry.get('checked_at')}); a person needs to look"
    if status == "unverified":
        return False, "access method and terms not verified yet, so SafeShelf does not query it"
    return False, "no automated access exists; a person can check it by hand"


def adapter(source_id: str):
    """The adapter instance for a source (module named in the registry, class Adapter)."""
    entry = source(source_id)
    module = importlib.import_module(entry["adapter"])
    return module.Adapter(entry)
