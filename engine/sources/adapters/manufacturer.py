"""Manufacturer-authorised recall feeds. None is signed up yet: a feed is added here only with the manufacturer's
written permission, with its domain in the registry's allowlist.
"""
from engine.sources.adapters.unavailable import Unavailable


class Adapter(Unavailable):
    reason = "no manufacturer has authorised a feed yet"
