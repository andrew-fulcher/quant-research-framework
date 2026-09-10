import numpy as np
import pandas as pd


#the model of this backtest is that we assume there is separate money
#available to settle trading costs.
#
#this means trading costs do not reduce the amount invested in the
#portfolio. Instead, they are recorded separately and deducted when
#measuring overall net performance.

def backtest(asset_returns, target_weights, initial_capital=10_000,
             cost_per_side=0.001, annualization=252):

    #=========================================================
    #1. copy and organize inputs
    #=========================================================

    #make copies so as not to alter the originals.
    #sort indices in case dates are not already chronological.
    asset_returns = asset_returns.copy().sort_index()
    target_weights = target_weights.copy().sort_index()

    #check that the respective sets of assets are the same.
    if set(asset_returns.columns) != set(target_weights.columns):
        raise ValueError(
            "asset_returns and target_weights must contain the same assets."
        )

    #ensure columns are in the same order.
    target_weights = target_weights[asset_returns.columns]

    #give target_weights the same set of dates as asset_returns.
    #this may introduce NaNs.
    target_weights = target_weights.reindex(asset_returns.index)

    #check for rows in target_weights that are incomplete.
    #each row should either contain:
    #- weights for every asset, or
    #- NaN for every asset, meaning no rebalance instruction.
    partial_rows = (
        target_weights.notna().any(axis=1)
        & ~target_weights.notna().all(axis=1)
    )

    if partial_rows.any():
        bad_dates = target_weights.index[partial_rows]

        raise ValueError(
            f"Target-weight rows must be complete or entirely NaN. "
            f"Partial rows found on: {list(bad_dates[:5])}"
        )

    #identify asset-return rows containing no missing entries.
    valid_rows = asset_returns.notna().all(axis=1)

    #remove invalid rows from both objects.
    asset_returns = asset_returns.loc[valid_rows]
    target_weights = target_weights.loc[valid_rows]

    #check that we haven't filtered out everything
    if len(asset_returns) == 0:
        raise ValueError("No valid return observations remain.")

    #store valid dates.
    dates = asset_returns.index

    #=========================================================
    #2. create containers for results
    #=========================================================

    #portfolio returns before trading costs.
    gross_returns = pd.Series(index=dates, dtype=float)

    #portfolio returns after accounting for trading costs.
    net_returns = pd.Series(index=dates, dtype=float)

    #total amount bought + sold as a fraction of portfolio value.
    traded_notional = pd.Series(index=dates, dtype=float)

    #one-way proportion of the portfolio reallocated.
    turnover = pd.Series(index=dates, dtype=float)

    #trading costs as a fraction of portfolio value.
    transaction_cost_fraction = pd.Series(index=dates, dtype=float)

    #trading costs as dollar amounts.
    transaction_costs = pd.Series(index=dates, dtype=float)

    #portfolio value immediately before the possible trade.
    equity_before_trade = pd.Series(index=dates, dtype=float)

    #gross portfolio value after the period's asset returns.
    #trading costs are NOT deducted from this.
    equity_curve = pd.Series(index=dates, dtype=float)

    #record whether a target-weight instruction was supplied.
    rebalance_instruction = pd.Series(False, index=dates, dtype=bool)

    #actual portfolio weights immediately before possible rebalance.
    pre_rebalance_weights = pd.DataFrame(
        index=dates, columns=asset_returns.columns, dtype=float
    )

    #portfolio weights immediately after possible rebalance.
    post_rebalance_weights = pd.DataFrame(
        index=dates, columns=asset_returns.columns, dtype=float
    )

    #=========================================================
    #3. initial state
    #=========================================================

    #initially we hold no risky assets, so we are 100% cash.
    current_weights = pd.Series(0.0, index=asset_returns.columns)

    #current gross portfolio value.
    equity = float(initial_capital)

    #=========================================================
    #4. walk forward through time
    #=========================================================

    for date in dates:

        #returns for each asset from the current trading time
        #to the next trading time.
        period_returns = asset_returns.loc[date]

        #record portfolio value before any possible trade.
        equity_before_trade.loc[date] = equity

        #record actual weights before any possible rebalance.
        pre_rebalance_weights.loc[date] = current_weights

        #target weights for the current date.
        target_row = target_weights.loc[date]

        #an all-non-NaN row means we have a rebalance instruction.
        should_rebalance = target_row.notna().all()

        rebalance_instruction.loc[date] = should_rebalance

        #-----------------------------------------------------
        #rebalance if instructed
        #-----------------------------------------------------

        if should_rebalance:

            #ensure target weights are floats.
            desired_weights = target_row.astype(float)

            #changes required in each asset weight.
            weight_change = desired_weights - current_weights

            #total risky-asset notional bought + sold.
            traded_fraction = weight_change.abs().sum()

            #cash is implicit in the risky-asset weights.
            current_cash = 1.0 - current_weights.sum()
            desired_cash = 1.0 - desired_weights.sum()

            #one-way portfolio turnover.
            portfolio_turnover = 0.5 * (
                traded_fraction + abs(desired_cash - current_cash)
            )

            #trading cost as a fraction of portfolio value.
            cost_fraction = (cost_per_side * traded_fraction)

            #these are the weights we hold during this period.
            weights_held = desired_weights

        else:

            #no rebalance instruction means no trading.
            traded_fraction = 0.0
            portfolio_turnover = 0.0
            cost_fraction = 0.0

            #continue holding existing positions.
            weights_held = current_weights.copy()

        #-----------------------------------------------------
        #record trading activity
        #-----------------------------------------------------

        traded_notional.loc[date] = traded_fraction
        turnover.loc[date] = portfolio_turnover
        transaction_cost_fraction.loc[date] = cost_fraction

        #fees are calculated on the portfolio value at the
        #time at which the trade occurs.
        transaction_costs.loc[date] = (equity * cost_fraction)

        post_rebalance_weights.loc[date] = weights_held

        #-----------------------------------------------------
        #calculate portfolio return
        #-----------------------------------------------------

        #weighted return across all assets.
        gross_return = (weights_held * period_returns).sum()

        gross_returns.loc[date] = gross_return

        #economic return after accounting for the externally
        #paid transaction cost.
        #
        #this does NOT determine portfolio growth because the
        #trading fee is not being paid out of the portfolio.
        net_return = (gross_return - cost_fraction)

        net_returns.loc[date] = net_return

        #-----------------------------------------------------
        #update portfolio value
        #-----------------------------------------------------

        #only asset returns change the invested portfolio value.
        equity *= (1.0 + gross_return)

        equity_curve.loc[date] = equity

        #-----------------------------------------------------
        #update portfolio weights for next trading time
        #-----------------------------------------------------

        gross_growth = 1.0 + gross_return

        #protect against portfolio value reaching zero or less.
        if gross_growth <= 0:
            raise ValueError(
                f"Portfolio value became non-positive "
                f"during the period beginning {date}."
            )

        #allow relative asset-price movements to change the
        #portfolio weights naturally.
        #
        #these become pre_rebalance_weights on the next
        #iteration.
        current_weights = (
            weights_held * (1.0 + period_returns) / gross_growth
        )

    #=========================================================
    #5. performance statistics
    #=========================================================

    #value of the investment portfolio itself.
    final_portfolio_value = equity_curve.iloc[-1]

    #total amount paid externally in trading costs.
    total_transaction_costs = transaction_costs.sum()

    #economic value after subtracting all externally paid fees.
    net_equity_curve = (equity_curve - transaction_costs.cumsum())

    #the net value after trading costs
    final_value = net_equity_curve.iloc[-1]

    #net total return after trading costs.
    total_return = (final_value / initial_capital - 1.0)

    #each row represents one trading period.
    years = len(net_returns) / annualization

    #cagr based on net final value.
    if years > 0 and final_value > 0:
        cagr = (
            (final_value / initial_capital) ** (1.0 / years)
            - 1.0
        )
    else:
        cagr = np.nan

    #volatility based on period-by-period economic returns
    #after transaction costs.
    period_volatility = net_returns.std(ddof=1)

    annualized_volatility = (
        period_volatility * np.sqrt(annualization)
    )

    #sharpe ratio, currently assuming a zero risk-free rate.
    if period_volatility > 0:
        sharpe_ratio = (
            net_returns.mean()
            / period_volatility
            * np.sqrt(annualization)
        )
    else:
        sharpe_ratio = np.nan

    #drawdowns based on economic value after transaction costs.
    running_max = net_equity_curve.cummax().clip(lower=initial_capital)

    drawdown = (net_equity_curve / running_max - 1.0)

    max_drawdown = drawdown.min()

    #number of dates on which actual trading occurred.
    num_trade_days = int((traded_notional > 1e-12).sum())

    #number of dates on which the strategy supplied
    #a target-weight instruction.
    num_rebalance_instructions = int(rebalance_instruction.sum())

    #=========================================================
    #6. return results
    #=========================================================

    return {

        #portfolio/equity information
        "equity_curve": equity_curve,
        "net_equity_curve": net_equity_curve,
        "equity_before_trade": equity_before_trade,

        #returns
        "gross_returns": gross_returns,
        "net_returns": net_returns,

        #weights
        "pre_rebalance_weights": pre_rebalance_weights,
        "post_rebalance_weights": post_rebalance_weights,
        "target_weights": target_weights,

        #trading instructions/activity
        "rebalance_instruction": rebalance_instruction,
        "traded_notional": traded_notional,
        "turnover": turnover,

        #trading costs
        "transaction_cost_fraction": transaction_cost_fraction,
        "transaction_costs": transaction_costs,
        "total_transaction_costs": total_transaction_costs,

        #risk information
        "drawdown": drawdown,

        #summary values
        "initial_capital": initial_capital,
        "final_portfolio_value": final_portfolio_value,
        "final_value": final_value,
        "total_return": total_return,
        "cagr": cagr,
        "annualized_volatility": annualized_volatility,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "num_trade_days": num_trade_days,
        "num_rebalance_instructions": num_rebalance_instructions,
        "cost_per_side": cost_per_side,
    }