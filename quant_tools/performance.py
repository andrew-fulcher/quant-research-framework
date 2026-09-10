import numpy as np
import pandas as pd


def benchmark_analysis(strategy_returns, benchmark_returns, annualization=252):
    """
    Calculate benchmark-relative performance statistics.

    Parameters
    ----------
    strategy_returns : pd.Series
        Period returns of the strategy.

    benchmark_returns : pd.Series
        Period returns of the benchmark.

    annualization : int
        Number of periods per year. Default is 252.

    Returns
    -------
    pd.Series
        Correlation, beta, annualized alpha,
        tracking error, and information ratio.
    """

    #align the two return series and remove missing values.
    data = pd.concat(
        [strategy_returns, benchmark_returns],
        axis=1,
        keys=["strategy", "benchmark"]
    ).dropna()

    strategy = data["strategy"]
    benchmark = data["benchmark"]

    #active return relative to benchmark.
    active_returns = strategy - benchmark

    #correlation.
    correlation = strategy.corr(benchmark)

    #market beta.
    beta = strategy.cov(benchmark) / benchmark.var()

    #alpha under the current zero-risk-free-rate assumption.
    period_alpha = strategy.mean() - beta * benchmark.mean()

    annualized_alpha = period_alpha * annualization

    #annualized tracking error.
    tracking_error = active_returns.std(ddof=1) * np.sqrt(annualization)

    #information ratio.
    information_ratio = (
        active_returns.mean()
        / active_returns.std(ddof=1)
        * np.sqrt(annualization)
    )

    return pd.Series({
        "Correlation": correlation,
        "Beta": beta,
        "Annualized Alpha": annualized_alpha,
        "Tracking Error": tracking_error,
        "Information Ratio": information_ratio,
    })