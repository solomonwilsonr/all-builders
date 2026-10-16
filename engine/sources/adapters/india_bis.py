"""BIS product certification (CRS registration / ISI licence). BIS offers public lookups for people (bis.gov.in, the
BIS Care app) but no automation API, so SafeShelf reports a claimed R-number or licence as "not verified" with the
lookup link. It never calls a mark fake because it could not check it.
"""
from engine.sources.adapters.unavailable import Unavailable

LOOKUP = "https://www.bis.gov.in/bis-apps/?lang=en"


class Adapter(Unavailable):
    reason = "BIS has no automation API; verify the R-number in the BIS Care app or on bis.gov.in"
