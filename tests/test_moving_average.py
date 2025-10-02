import pytest

from strategies.moving_average import MovingAverageCross


def test_moving_average_cross_basic_signal():
    strat = MovingAverageCross(short_window=2, long_window=3)

    bars = [
        {"close": 100.0},
        {"close": 101.0},
        {"close": 102.0},
        {"close": 101.0},
    ]

    outputs = [strat.on_bar(bar) for bar in bars]
    # First long_window - 1 bars should produce zero target because not enough history
    assert outputs[0]["target_weight"] == 0.0
    assert outputs[1]["target_weight"] == 0.0

    # Third bar: short SMA (101.5) > long SMA (~101.0) => long signal
    assert outputs[2]["target_weight"] == 1.0

    # Fourth bar: short SMA (101.5) > long SMA (~101.33) => still long
    assert outputs[3]["target_weight"] == 1.0


@pytest.mark.parametrize(
    "prices,expected",
    [
        ([100, 100, 100], [0.0, 0.0, 0.0]),  # flat market never crosses
        ([100, 99, 98, 97, 96], [0.0, 0.0, 0.0, 0.0, 0.0]),  # down trend stays out
    ],
)
def test_moving_average_cross_does_not_false_positive(prices, expected):
    strat = MovingAverageCross(short_window=2, long_window=3)
    outputs = [strat.on_bar({"close": float(p)}) for p in prices]
    assert [out["target_weight"] for out in outputs] == expected


def test_moving_average_cross_requires_valid_windows():
    with pytest.raises(ValueError):
        MovingAverageCross(short_window=0, long_window=5)

    with pytest.raises(ValueError):
        MovingAverageCross(short_window=5, long_window=5)

    with pytest.raises(ValueError):
        MovingAverageCross(short_window=7, long_window=4)


def test_moving_average_cross_signal_flips_to_zero():
    strat = MovingAverageCross(short_window=2, long_window=3)
    # go long first
    strat.on_bar({"close": 100.0})
    strat.on_bar({"close": 101.0})
    assert strat.on_bar({"close": 102.0})["target_weight"] == 1.0

    # price drops enough so short SMA < long SMA
    assert strat.on_bar({"close": 98.0})["target_weight"] == 0.0
