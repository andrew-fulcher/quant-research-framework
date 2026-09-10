# Quantitative Research and Backtesting Framework

A reusable Python framework for researching cross-sectional trading signals,
constructing portfolios, and evaluating strategy performance.

The project develops a daily portfolio backtester with explicit treatment of
weight drift, rebalancing, turnover, and transaction costs, together with
tools for benchmark-relative performance analysis and cross-sectional signal
diagnostics.

A 20-day momentum strategy is used as the first research application of the
framework. The purpose of the project is not to present the momentum rule as
a production-ready trading strategy, but to demonstrate a structured
quantitative research workflow that can be extended to more sophisticated
signals and models.

## Repository Structure

```text
quant_project/
├── quant_tools/
│   ├── __init__.py
│   ├── data_updater.py
│   ├── backtester.py
│   ├── performance.py
│   └── signal_metrics.py
│
├── notebooks/
│   ├── momentum_strategy.ipynb
│   └── backtester_validation.ipynb
│
├── README.md
├── requirements.txt
└── .gitignore
```

## Backtester Design

The backtester operates on two main inputs:

- a DataFrame of forward asset returns;
- a DataFrame of desired portfolio target weights.

Each row represents one trading period. A complete target-weight row instructs
the backtester to rebalance to those weights at the start of the period, while
an entirely `NaN` row means that no rebalance is performed and the existing
portfolio is retained.

Between rebalances, asset returns cause portfolio weights to drift naturally.
When a new target is supplied, trades are therefore calculated relative to
the current drifted portfolio weights rather than the previous target weights.

The engine separately records:

- pre-rebalance and post-rebalance weights;
- traded notional;
- conventional one-way turnover;
- transaction costs;
- gross and net returns;
- portfolio equity;
- drawdowns and summary performance statistics.

Transaction costs are modelled as a fixed proportional cost per dollar traded.
In this project, these costs are treated as externally funded expenses rather
than being deducted from invested portfolio capital. The final economic value
is therefore calculated as gross portfolio value minus accumulated trading
costs.

The accounting logic is independently checked in
`backtester_validation.ipynb` using hand-calculable examples.

## Momentum Research Example

The framework is demonstrated using a 20-day cross-sectional momentum signal
applied to a diversified set of large-cap US equities.

At each market open, stocks are ranked by their trailing 20-day open-to-open
return. The original strategy invests entirely in the highest-ranked stock,
while alternative portfolio constructions and passive benchmarks are used for
comparison.

The analysis includes:

- strategy performance and drawdown analysis;
- comparison with SPY, NVDA, and an equal-weight portfolio;
- benchmark-relative statistics including beta, alpha, tracking error, and
  information ratio;
- cross-sectional information coefficients over 1-, 5-, 10-, and 20-day
  forward-return horizons;
- momentum-quintile analysis;
- extreme-rank analysis;
- comparison of Rank-1 and Top-5 momentum portfolios.

The main empirical result is that the full momentum ranking shows little
monotonic cross-sectional predictive power, while historical outperformance
is concentrated more strongly in the single highest-ranked stock.

This comes with substantial concentration risk, volatility, drawdowns, and
transaction costs, so the strategy should be interpreted as a research
example rather than a production-ready trading system.

## Key Findings

Using the expanded stock universe and a starting portfolio value of $10,000:

- The Rank-1 momentum strategy finishes at approximately $111,666, with a
  CAGR of 44.3%.
- This performance comes with high risk: annualized volatility is about
  50.2% and maximum drawdown is approximately -61.5%.
- The passive equal-weight portfolio finishes at approximately $48,086 with
  lower volatility and a higher Sharpe ratio than the momentum strategy.
- SPY finishes at approximately $25,891 over the same evaluation period.
- The Rank-1 strategy incurs approximately $63,846 in cumulative transaction
  costs under the project's fixed-cost model.
- Cross-sectional Spearman information coefficients are approximately zero
  over 1-, 5-, 10-, and 20-day forward-return horizons, indicating little
  evidence of a broad monotonic momentum effect.
- Momentum-quintile returns are U-shaped: both extreme momentum groups
  outperform the middle quintiles.
- The single highest-ranked momentum stock consistently outperforms the
  remainder of the highest-momentum quintile across the tested horizons.
- A diversified Top-5 momentum portfolio reduces volatility and drawdown,
  but also reduces return and Sharpe ratio substantially.

Overall, the results suggest that the strong historical performance of the
Rank-1 strategy is associated with a concentrated extreme-rank effect rather
than a general cross-sectional momentum relationship.

## Limitations and Assumptions

The results in this repository should be interpreted as a research
demonstration rather than evidence of a production-ready trading strategy.

Important limitations include:

- The stock universe is a fixed set of currently prominent large-cap US
  equities. This introduces survivorship and selection bias because the
  historical universe is not reconstructed through time.
- The analysis is entirely in-sample. No separate training, validation, or
  out-of-sample test period is used.
- Signals and trades are assumed to be implemented approximately at the market
  open using open-price data.
- The execution model does not include bid-ask spreads, slippage, latency,
  market impact, or order-book dynamics.
- Transaction costs are represented by a fixed proportional cost per dollar
  traded and are treated as externally funded expenses.
- The Rank-1 momentum strategy is highly concentrated and therefore exposed to
  substantial idiosyncratic risk.
- Multi-day forward-return observations overlap, so longer-horizon signal
  diagnostics should not be treated as statistically independent observations.
- The analysis does not neutralize sector exposure, market beta, volatility,
  or other common risk factors.
- The relatively small cross-sectional universe limits the precision of the
  signal diagnostics.

These limitations mean that historical performance should not be interpreted
as an estimate of expected live-trading performance.

## Installation and Usage

### 1. Clone the repository

Clone the repository and move into the project directory:

    git clone <repository-url>
    cd quant_project

### 2. Create a virtual environment

On macOS or Linux:

    python3 -m venv .venv
    source .venv/bin/activate

On Windows:

    python -m venv .venv
    .venv\Scripts\activate

### 3. Install dependencies

    pip install -r requirements.txt

### 4. Run the notebooks

Open the project in VS Code or Jupyter and run:

- `notebooks/backtester_validation.ipynb` to verify the backtester accounting;
- `notebooks/momentum_strategy.ipynb` to reproduce the momentum research
  example.

The notebooks import reusable functionality from the `quant_tools` package.

Historical market data are downloaded and updated through
`quant_tools/data_updater.py`.

The updater stores data in the project's local `data/` directory, which is
created automatically if it does not already exist. No machine-specific path
configuration is required.