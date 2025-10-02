import pytest

from backtest.portfolio import Portfolio


def test_portfolio_executes_target_weight_signal():
    portfolio = Portfolio(cash=1000.0)

    # First bar, target 50% allocation at price 10 => buy 50 shares costing 500
    signal = {"target_weight": 0.5}
    bar = {"close": 10.0, "date": "2024-01-01"}

    orders = portfolio.generate_orders(signal, bar)
    fills = portfolio.execute_orders(orders, bar)
    portfolio.update(fills, bar)

    assert pytest.approx(portfolio.cash) == 500.0
    assert pytest.approx(portfolio.quantity) == 50.0
    assert portfolio.history[-1]["value"] == pytest.approx(1000.0)

    # Next bar price rises to 12, target weight 0.0 => sell everything
    signal2 = {"target_weight": 0.0}
    bar2 = {"close": 12.0, "date": "2024-01-02"}
    orders2 = portfolio.generate_orders(signal2, bar2)
    fills2 = portfolio.execute_orders(orders2, bar2)
    portfolio.update(fills2, bar2)

    assert pytest.approx(portfolio.cash) == 1100.0  # 50 shares * 12 + 500 cash
    assert pytest.approx(portfolio.quantity) == 0.0
    assert portfolio.history[-1]["value"] == pytest.approx(1100.0)


def test_portfolio_handles_zero_price_gracefully():
    portfolio = Portfolio(cash=1000.0)
    signal = {"target_weight": 1.0}
    bar = {"close": 0.0, "date": "2024-01-01"}

    orders = portfolio.generate_orders(signal, bar)
    # price zero should result in zero qty (avoid division by zero)
    assert orders == [{"qty": 0.0, "price": 0.0}]

    fills = portfolio.execute_orders(orders, bar)
    portfolio.update(fills, bar)
    assert portfolio.cash == pytest.approx(1000.0)
    assert portfolio.quantity == pytest.approx(0.0)
    assert portfolio.history[-1]["value"] == pytest.approx(1000.0)
