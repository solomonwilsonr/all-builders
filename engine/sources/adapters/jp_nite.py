"""NITE product accident information (Japan). The site answers plain HTTP, but no documented query interface or terms
for automated use were found (checked 16 Oct 2026), so it is not queried: coverage says "not supported" for it.
CAA's recall site carries the recalls NITE's accident reports lead to.
"""
from engine.sources.adapters.unavailable import Unavailable


class Adapter(Unavailable):
    reason = "NITE's accident database has no documented query interface or automated-use terms yet"
