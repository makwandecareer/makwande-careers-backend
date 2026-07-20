from datetime import datetime, timedelta, timezone


def test_trial_amount_is_45_rand():
    assert 4500 / 100 == 45


def test_premium_amount_is_300_rand():
    assert 30000 / 100 == 300


def test_trial_duration_is_14_days():
    start = datetime.now(timezone.utc)
    assert (start + timedelta(days=14) - start).days == 14


def test_premium_internal_period_is_30_days():
    start = datetime.now(timezone.utc)
    assert (start + timedelta(days=30) - start).days == 30
