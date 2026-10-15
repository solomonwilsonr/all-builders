import datetime

import pytest

from engine.recall_catalog import card, filters, hazard_types, page_numbers


def test_hazard_types_by_keyword():
    assert hazard_types("The lithium-ion battery can explode or ignite, posing fire and burn hazards.") == ["fire_burn"]
    assert hazard_types("Small parts can detach and pose a choking hazard.") == ["choking"]
    assert hazard_types("Undeclared allergen (peanut).") == ["chemical"]
    assert hazard_types("Inadequate creepage distance - risk of electric shock") == ["electric_shock"]


def test_serious_injury_alone_is_not_a_mechanical_hazard():
    """Most notices end "risk of serious injury": only the mechanism counts."""
    assert hazard_types("Fire hazard; risk of serious injury or death.") == ["fire_burn"]
    assert hazard_types("Does not meet the mandatory standard. Risk of serious injury.") == ["other"]


def test_lead_is_a_word_not_part_of_leading():
    assert hazard_types("Paint contains lead above the limit.") == ["chemical"]
    assert hazard_types("A loose clamp, leading to loss of steering.") == ["other"]


def test_card_flattens_the_notice():
    row = {"id": "cpsc:1", "authority": "CPSC", "country": "United States", "notice_date": datetime.date(2026, 9, 24),
           "title": "Power Banks Recalled", "hazard": "Can overheat.", "url": "https://cpsc.gov/x",
           "scope_json": {"Products": [{"Name": "Power bank", "Model": "PB-1", "NumberOfUnits": "About 100"}],
                          "Manufacturers": [{"Name": "Maker Ltd"}], "Importers": [{"Name": ""}],
                          "Images": [{"URL": "https://cpsc.gov/a.png", "Caption": "Front"}, {"URL": None}]}}
    out = card(row)
    assert out["notice_date"] == "2026-09-24" and out["hazard_types"] == ["fire_burn"]
    assert out["products"] == [{"name": "Power bank", "model": "PB-1", "description": "", "units": "About 100"}]
    assert out["companies"] == ["Maker Ltd"]
    assert out["images"] == [{"url": "https://cpsc.gov/a.png", "caption": "Front"}]
    assert out["source"] == "CPSC" and out["action"] == ""


def test_every_word_of_q_must_match_and_wildcards_are_literal():
    where, args = filters({"q": "power 50%"})
    assert where.count("ILIKE") == 6
    assert args[:3] == ["%power%"] * 3 and args[3] == r"%50\%%"


def test_filters_reject_bad_values():
    for bad in ({"hazard_type": "radiation"}, {"from": "last week"}, {"q": "x" * 101}):
        with pytest.raises(ValueError):
            filters(bad)
    for bad in ({"page": "0"}, {"per_page": "51"}, {"page": "two"}):
        with pytest.raises(ValueError):
            page_numbers(bad)
    assert page_numbers({}) == (1, 24)


def test_authority_list_is_upper_cased():
    _, args = filters({"authority": "accc, caa"})
    assert args == [["ACCC", "CAA"]]
