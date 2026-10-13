from datetime import UTC, date, datetime

from bench import backtest as bt


def rv(day: str, text: str = "fine", user: str = "u") -> dict:
    ts = int(datetime.fromisoformat(day).replace(tzinfo=UTC).timestamp() * 1000)
    return {"timestamp": ts, "text": text, "user_id": f"{user}{day}{text}", "parent_asin": "A"}


def hazard(severity: str = "high", experience: str = "own_experience") -> dict:
    return {"hazard": True, "experience": experience, "severity": severity}


def test_only_reviews_before_the_recall_and_none_mentioning_it():
    reviews = [rv("2023-01-01"), rv("2023-07-06", "melted"), rv("2023-02-01", "saw the recall notice")]
    assert [r["text"] for r in bt.usable(reviews, date(2023, 7, 6))] == ["fine"]


def test_fixed_alarm_needs_three_inside_90_days():
    assert bt.first_alarm([date(2023, 1, 1), date(2023, 2, 1), date(2023, 5, 1)]) is None
    assert bt.first_alarm([date(2023, 1, 1), date(2023, 2, 1), date(2023, 3, 1)]) == date(2023, 3, 1)


def test_safeshelf_alarm_dedupes_and_needs_own_experience():
    reviews = [rv("2023-01-01", "melted on day one"), rv("2023-01-02", "Melted on day one!", "v"),
               rv("2023-01-03", "heard it explodes"), rv("2023-01-04", "port burned")]
    labels = {bt.rid(reviews[0]): hazard(), bt.rid(reviews[1]): hazard(),
              bt.rid(reviews[2]): hazard(experience="hearsay"), bt.rid(reviews[3]): hazard()}
    params = {"k": 2, "min_severity": "medium", "min_rate": 0.0}
    assert bt.safeshelf_alarm(reviews, labels, params) == date(2023, 1, 4)  # the copy and the hearsay don't count
    assert bt.safeshelf_alarm(reviews, labels, {**params, "k": 3}) is None


def test_safeshelf_alarm_respects_rate():
    reviews = [rv(f"2023-01-{d:02d}", f"ok {d}") for d in range(1, 29)] + [rv("2023-02-01", "fire"),
                                                                          rv("2023-02-02", "smoke")]
    labels = {bt.rid(reviews[-1]): hazard(), bt.rid(reviews[-2]): hazard()}
    assert bt.safeshelf_alarm(reviews, labels, {"k": 2, "min_severity": "low", "min_rate": 50.0}) == date(2023, 2, 2)
    assert bt.safeshelf_alarm(reviews, labels, {"k": 2, "min_severity": "low", "min_rate": 100.0}) is None


def test_summary_counts_leads_and_false_alarms():
    units = [{"kind": "recall", "cutoff": date(2023, 7, 6), "alarm": {"m": date(2023, 4, 27)}},
             {"kind": "recall", "cutoff": date(2023, 7, 6), "alarm": {"m": None}},
             {"kind": "control", "cutoff": date(2023, 7, 6), "alarm": {"m": date(2023, 1, 1)}},
             {"kind": "control", "cutoff": date(2023, 7, 6), "alarm": {"m": None}}]
    assert bt.summarise(units, "m") == {"recalls_flagged": "1/2", "median_lead_weeks": 10.0,
                                        "false_alarm_rate": 0.5, "false_alarms": "1/2"}


def test_split_is_stable_and_uses_both_halves():
    ids = [f"cpsc:{n}" for n in range(20000, 20040)]
    assert {bt.split(i) for i in ids} == {"train", "test"}
    assert [bt.split(i) for i in ids] == [bt.split(i) for i in ids]


def test_prefilter_is_wider_than_keywords():
    assert bt.KEYWORDS.search("it melted") and bt.PREFILTER.search("it melted")
    assert not bt.KEYWORDS.search("gets hot") and bt.PREFILTER.search("gets hot")
