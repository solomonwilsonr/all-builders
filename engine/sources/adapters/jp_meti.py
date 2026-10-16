"""METI product-safety recall notices (Japan). meti.go.jp answers 403 to automated requests from SafeShelf's network
(checked 16 Oct 2026). CAA's recall site lists METI's notices under 参照情報, so they are reached through jp_caa.
"""
from engine.sources.adapters.unavailable import Unavailable


class Adapter(Unavailable):
    reason = "meti.go.jp refuses automated requests (403)"
