"""EU Safety Gate alerts. No permitted public JSON endpoint was confirmed (the portal's internal API refuses plain
requests), so it is searched through the read-only Research Agent like a person would, when that service is set up.
An EU alert is a cross-border signal, never a JAPAC confirmed recall by itself.
"""
from engine.sources.adapters.research_fallback import Adapter as Research


class Adapter(Research):
    pass
