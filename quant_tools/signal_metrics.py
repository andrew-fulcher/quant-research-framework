import numpy as np
import pandas as pd


def information_coefficient(signal, forward_returns):
    """
    Calculate the daily cross-sectional Spearman information coefficient.

    Parameters
    ----------
    signal : pd.DataFrame
        Signal values for each asset and date.

    forward_returns : pd.DataFrame
        Subsequent returns for each asset and date.

    Returns
    -------
    pd.Series
        Daily cross-sectional information coefficients.
    """

    ic = pd.Series(index=signal.index, dtype=float)

    for date in signal.index:
        signal_today = signal.loc[date]
        future_return = forward_returns.loc[date]

        valid = signal_today.notna() & future_return.notna()

        if valid.sum() < 2:
            continue

        signal_rank = signal_today[valid].rank()
        return_rank = future_return[valid].rank()

        ic.loc[date] = signal_rank.corr(return_rank)

    return ic.dropna()


def information_coefficients_by_horizon(
    signal, prices, horizons=(1, 5, 10, 20)
):
    """
    Summarize cross-sectional IC across several forward-return horizons.
    """

    results = {}

    for horizon in horizons:
        forward_returns = prices.shift(-horizon) / prices - 1

        ic = information_coefficient(signal, forward_returns)

        results[horizon] = {
            "Mean IC": ic.mean(),
            "IC Std": ic.std(ddof=1),
            "IC t-stat": (
                ic.mean()
                / (ic.std(ddof=1) / np.sqrt(len(ic)))
            ),
            "Observations": len(ic),
        }

    summary = pd.DataFrame(results).T
    summary.index.name = "Forward Return Horizon"

    return summary


def quantile_forward_returns(
    signal, prices, horizons=(1, 5, 10, 20), n_quantiles=5
):
    """
    Calculate mean forward returns by signal quantile.
    """

    results = {}

    for horizon in horizons:
        forward_returns = prices.shift(-horizon) / prices - 1

        daily_quantile_returns = []

        for date in signal.index:
            signal_today = signal.loc[date]
            future_return = forward_returns.loc[date]

            valid = signal_today.notna() & future_return.notna()

            signal_today = signal_today[valid]
            future_return = future_return[valid]

            if len(signal_today) < n_quantiles:
                continue

            signal_rank = signal_today.rank(method="first")

            quantiles = pd.qcut(
                signal_rank,
                q=n_quantiles,
                labels=range(1, n_quantiles + 1)
            )

            daily_returns = (
                future_return
                .groupby(quantiles, observed=True)
                .mean()
            )

            daily_quantile_returns.append(daily_returns)

        daily_quantile_returns = pd.DataFrame(daily_quantile_returns)

        results[horizon] = daily_quantile_returns.mean()

    summary = pd.DataFrame(results).T

    summary.columns = [
        f"Q{i}" for i in range(1, n_quantiles + 1)
    ]

    summary.index.name = "Forward Horizon"

    return summary


def extreme_rank_forward_returns(
    signal, prices, horizons=(1, 5, 10, 20), n_quantiles=5
):
    """
    Compare the most extreme signal ranks with the remainder
    of their respective extreme quantiles.
    """

    results = {}

    for horizon in horizons:
        forward_returns = prices.shift(-horizon) / prices - 1

        observations = []

        for date in signal.index:
            signal_today = signal.loc[date]
            future_return = forward_returns.loc[date]

            valid = signal_today.notna() & future_return.notna()

            signal_today = signal_today[valid]
            future_return = future_return[valid]

            if len(signal_today) < n_quantiles:
                continue

            signal_rank = signal_today.rank(method="first")

            quantiles = pd.qcut(
                signal_rank,
                q=n_quantiles,
                labels=range(1, n_quantiles + 1)
            )

            top_stock = signal_today.idxmax()
            bottom_stock = signal_today.idxmin()

            top_quantile = quantiles[quantiles == n_quantiles].index
            bottom_quantile = quantiles[quantiles == 1].index

            rest_of_top = top_quantile.drop(top_stock)
            rest_of_bottom = bottom_quantile.drop(bottom_stock)

            observations.append({
                "Top Rank": future_return[top_stock],
                f"Rest of Q{n_quantiles}":
                    future_return[rest_of_top].mean(),
                "Bottom Rank": future_return[bottom_stock],
                "Rest of Q1":
                    future_return[rest_of_bottom].mean(),
            })

        results[horizon] = pd.DataFrame(observations).mean()

    summary = pd.DataFrame(results).T
    summary.index.name = "Forward Horizon"

    return summary