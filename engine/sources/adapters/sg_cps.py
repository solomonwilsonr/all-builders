"""Singapore's Consumer Product Safety Office recalls and alerts. The site answers 403 to plain HTTP and headless
browsers from SafeShelf's network (checked 15 and 16 Oct 2026). Older CPSO notices (to 2022) are in the stored copy
from OECD GlobalRecalls; newer ones need a person to look until an authorised feed exists.
"""
from engine.sources.adapters.unavailable import Unavailable


class Adapter(Unavailable):
    reason = "consumerproductsafety.gov.sg refuses automated requests (403)"
