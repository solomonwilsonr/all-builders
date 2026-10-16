"""Live official sources (implementation plan v2.2, workstream A): one adapter per regulator or registry, a planner that
picks the sources for a shopper's country, and a coverage list that says what was checked, when, and how.

    from engine.sources import planner
    result = planner.investigate(SourceQuery(brand="Anker", model="A1263", market_country="IN"))

A source that cannot be reached is reported as unavailable, never as "no recall": missing evidence is not safety.
"""
