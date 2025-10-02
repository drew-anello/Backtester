import pytest

from strategies.mean_reversion import MeanReversionStrategy


def test_mean_reversion_requires_valid_parameters():
    with pytest.raises(ValueError):
        MeanReversionStrategy(lookback=1, entry_z=1.5, exit_z=0.5)

    with pytest.raises(ValueError):
        MeanReversionStrategy(lookback=20, entry_z=0.0, exit_z=0.5)

    with pytest.raises(ValueError):
        MeanReversionStrategy(lookback=20, entry_z=1.0, exit_z=1.0)

    with pytest.raises(ValueError):
        MeanReversionStrategy(lookback=20, entry_z=1.0, exit_z=1.1)


def test_mean_reversion_enters_and_exits_long():
    strat = MeanReversionStrategy(lookback=4, entry_z=1.0, exit_z=0.5)

    prices = [100, 99, 98, 97]  # build history; std > 0
    for price in prices:
        signal = strat.on_bar({"close": price})
    # Last bar should trigger long (z around -1.34)
    assert signal["target_weight"] == 1.0

    # Move back toward mean so z rises above -exit threshold
    exit_signal = strat.on_bar({"close": 100})
    assert exit_signal["target_weight"] == 0.0


def test_mean_reversion_handles_flat_prices():
    strat = MeanReversionStrategy(lookback=3, entry_z=1.5, exit_z=0.5)
    outputs = [strat.on_bar({"close": 100.0}) for _ in range(5)]
    assert all(out["target_weight"] == 0.0 for out in outputs)
