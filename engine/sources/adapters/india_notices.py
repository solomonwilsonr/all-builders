"""India: CCPA recall orders and safety notices, and BIS search-and-seizure raids, from Press Information Bureau
releases (data/load_india_notices.py fetches and stores them; this adapter answers from that stored copy).

India has no public recall database, so the coverage list says exactly that next to whatever these notices show. A
seizure or safety notice is never a recall of the shopper's product: it can only raise a potential concern.
"""
from engine.sources.adapters.stored_notices import Adapter as Stored


class Adapter(Stored):
    authorities = ("CCPA", "BIS")
