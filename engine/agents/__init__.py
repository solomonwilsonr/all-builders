"""SafeShelf agents (M9), built with Google's Agent Development Kit and served by the API itself.

- concierge.py   Shelf Chat: an LlmAgent that reads stored evidence through tools, and the Safer Alternative Finder
- pipeline.py    Investigate: PageReader -> five checks in a ParallelAgent -> verdict set by code -> VerdictWriter
- copilot.py     Regulator report: evidence pack + pre-filled incident report; never submitted by code
- shopper.py     Shopper Agent: picks the next thing to open on the shopper's page; the extension carries it out
- research.py    Research Agent client: a headless browser on Cloud Run (research/) checks official recall sites
- a2a.py         The Concierge as an A2A agent, with its agent card
- guard.py       Safety rules every agent shares: click blocklist, answer wording, evidence IDs
- runtime.py     Models on Vertex, the per-request run record (steps, evidence IDs, trace) and the ADK runner

Verdict colours are always set by code; Gemini only gathers, picks and writes.
"""
