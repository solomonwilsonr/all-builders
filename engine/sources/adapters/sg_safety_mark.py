"""Singapore SAFETY Mark registry for the controlled goods categories. No documented machine interface or terms for
automated lookups were found (checked 16 Oct 2026). A missing SAFETY Mark only matters for controlled goods: the
scope check never treats it as a violation for other products.
"""
from engine.sources.adapters.unavailable import Unavailable

# The controlled goods families that need a SAFETY Mark (Consumer Protection (Safety Requirements) Regulations).
CONTROLLED = ("adaptor", "adapter", "charger", "power bank", "extension", "plug", "socket", "kettle", "rice cooker",
              "iron", "hair dryer", "heater", "fan", "air conditioner", "refrigerator", "washing machine",
              "television", "microwave", "induction", "lamp", "light", "vacuum")


def is_controlled(category: str | None, title: str | None = None) -> bool:
    text = f"{category or ''} {title or ''}".replace("_", " ").lower()
    return any(word in text for word in CONTROLLED)


class Adapter(Unavailable):
    reason = "the SAFETY Mark registry has no documented machine interface yet"
