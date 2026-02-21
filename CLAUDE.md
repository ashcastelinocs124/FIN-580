# Trading Strategy

## Project Overview
Investopedia trading competition for a Fundamental Investments class. Initial 3-week competition (Starbucks gift card prize), but team decided to optimize for the full 2-2.5 month duration since the professor is teaching other topics for the remaining time. US stocks assumed (professor didn't specify geography). $5 course pack required for case studies.

## Team
- **Ash (Ashleyn Castelino)** - Assignment 1.1: Trading agent/system (has prior Investopedia experience from investment club)
- **Blazio (Blasio)** - Assignment 1.2: UI production system
- **Hamzah** - Assignment 1.3: LinkedIn post
- **Keshav (Kesha)** - Collaborator on quant research projects, wants to backtest strategy with the professor

## Setup
- Shared Gmail account so all team members can execute trades independently
- Shared GitHub repo with assignment folders per assignment (assignment one, assignment two, etc.)
- Ash sets up the Investopedia account (experienced from investment club competitions)

## Portfolio Allocation
- **20% safety**: Google + one large non-tech company (to avoid overexposure to tech)
- **80% small cap**: Key differentiator from other teams who will all pick large caps

## Investment Thesis

### Tech Sector
- Recent selloff driven by: SaaS companies dipping from Anthropic/AI releases, AI spending concerns
- **Small cap tech > large cap** - better opportunities post-selloff
- Data center infrastructure remains promising
  - **ANET (Arista Networks)**: Cloud connectivity / AI data center company. Jumped $132 -> $148 in one day
  - Massive global investment in data center infrastructure (including India)
- No major tech earnings during competition timeframe (limits catalysts)
- Utility sector also worth watching: "The narrative has shifted from who builds the AI to how do we keep the lights on"

### Commodities - Copper Mining
- US classified copper as a **national security priority**
- Government actively investing in copper infrastructure
- Used in AI data centers AND EVs - structural demand story
- Look at copper mining stocks specifically (can't buy ETFs on the platform yet)

### Commodities - Oil & Gas
- Oil prices down, weekly decline expected
- Russia shadow fleet issues may impact global oil pricing
- Iran geopolitical risk still priced in
- Worth looking at energy stocks at current low prices

### Macro Themes
- **K-shaped economy**: Gap between rich and poor expanding
  - Benefits both discount retailers (poor side) AND luxury spending (rich side, e.g. Macy's)
  - Both high-end and low-end recording profits = K-shape confirmation
  - Affects Fed rate decisions: GDP looks good on surface but low-income consumers are hurting
  - Jerome Powell has spoken about K-shaped economy multiple times
  - Not a 3-week play, better as 1-2 month strategy
- Key economic data to monitor:
  - **ISM Manufacturing**: Recent print 52.6, up from 47 in December (big 5-point jump). January was strong due to post-holiday inventory reorder cycle. February print unlikely to be as surprising
  - **Consumer confidence index**
  - **ADP employment / private payrolls**: Non-farm payrolls came in better than expected, so ADP unlikely to be bad
  - **PCE inflation update**
- Feb 16: Markets closed for President's Day

## AI-Powered Research Approach
- Build agentic system with multiple sub-agents:
  - **Research agent**: Fundamental analysis
  - **Technical analysis agent**: Small cap opportunities, post-selloff recovery analysis
  - **Sector-specific agents**: Data centers, copper mining, oil/gas
  - **Debate agent** (`/debate`): Bull vs Bear format - spawns parallel subagents with live web research to argue for/against any trade, then a Judge synthesizes a verdict with conviction score and position sizing
  - **Investment workflow** (`/invest`): End-to-end pipeline — auto-runs debate first, gets user approval + catalyst input, then runs full research pipeline with macro/sector/stock scoring. Sonnet for research agents, Opus for synthesis.
- Feed investment thesis to AI, get stock recommendations back, then team makes final buy/sell decisions
- Using Claude (Ash has Claude Max plan + Claude Code)

## Quant Research Projects (with Keshav)

### Whale Trader Connection Model
- Connect big players (whales) in prediction markets (Polymarket) to big players in financial markets
- Corporations above a certain capital threshold must **publicly disclose trades by law**
- Find common trading patterns between Polymarket activity and hedge fund disclosures
- Shortlist matching hedge funds, find connected politicians, use those connections for trading signals
- High-stakes research project with significant return potential

### Geopolitical Trading Algorithm
- Focus on **major geopolitical events** (not small product launches like iPhone releases)
- Map politician -> donor -> hedge fund relationships
- Use election data (US elections constantly happening at all levels)
- Find politicians' donor data, connect donors to hedge funds
- Hedge funds' mandatory trade disclosures reveal trading patterns
- Build **context graph** connecting political events to trading patterns
- "Build it out bottom up, make money top down"
- Data sources: Polymarket API, hedge fund disclosures, political donor data
- Example: Nancy Pelosi's husband is a hedge fund manager with "great returns" - connecting those dots at scale

## Platform Constraints
- Currently stocks only
- Waiting for platform to open additional asset classes: gold, crypto
- Can't buy ETFs yet
- Crypto selloff was significant - opportunity when platform allows it

## Meeting Log

### Feb 4, 2026 - Geopolitical Data Analysis & Polymarket Trading Strategy
- Outlined geopolitical trading algorithm concept
- Discussed connecting Polymarket whales to hedge fund trading patterns
- Proposed context graph architecture for politician-donor-hedge fund relationships
- Identified Polymarket API and hedge fund disclosures as primary data sources

### Feb 9, 2026 - Trading Strategy Research
- Discussed whale trader connection model in more detail
- Hedge funds legally required to disclose trades publicly
- Professor (for quant research) was a no-show to the meeting
- Keshav wants to backtest the trading strategy with the professor

### Feb 12, 2026 - Trading Strategy Project Planning (Ash, Blazio, Hamzah)
- Set up shared Gmail/Investopedia account plan
- Portfolio allocation decided: 20% safety / 80% small cap
- Assignment distribution: 1.1 (Ash - agent), 1.2 (Blazio - UI), 1.3 (LinkedIn post)
- GitHub repo with assignment folders planned
- Class is only 3 weeks of trading, then professor teaches other material for remaining 2 months
- Evening coordination call scheduled at 8 PM

### Feb 15, 2026 - Investment Strategy for Tech, Oil, and Copper (Ash, Hamzah)
- Shifted strategy from 3-week optimization to 2-2.5 month horizon
- Tech: small caps over large caps, data center infra (ANET jumped $132->$148)
- Commodities: copper (national security, AI/EV demand), oil/gas (geopolitical risk plays)
- Macro: K-shaped economy theme, key economic indicators mapped out
- ISM Manufacturing print 52.6 (up from 47 in Dec) - strong but unlikely to surprise again
- Next steps: deploy AI agents for stock research, await platform opening to gold/crypto
- Agreed to focus on stocks with both short-term catalysts AND long-term structural trends

## Completed Work

### Oversold Small-Cap Tech Screener (`oversold_screener.py`) - Feb 20, 2026
- Built single-file Python screener using `yfinance` + `tabulate` for post-selloff opportunity detection
- Computes 7 oversold signals per ticker: RSI<30, Fwd PE<15, below 200MA, MACD bullish divergence, analyst Buy rating, positive forward earnings, declining volume on down days
- Outputs three colourised tables (technical overview, fundamentals/volume, score ranking) plus a key-takeaways summary section
- Supports custom tickers via CLI args (`python oversold_screener.py ANET SMCI TEAM`)
- Default watchlist: ANET, INOD, MOD, PATH, DOCU, INTU, TEAM, NBIS, SMCI, CRDO, VRT

### Multi-Agent Macro Research Pipeline (`/research` skill) - Feb 20, 2026
- Built 3-layer Claude Code skill: Macro (14 factors) -> Sector (parallel, with sensitivity maps) -> Stock Scoring (parallel, 12-point)
- Sector-aware macro alignment scoring (0-3 points) using Macro Sensitivity Maps (5 default sectors)
- Long-only, small-cap focused, respects 20/80 portfolio allocation with dry powder tracking
- Integrates with `oversold_screener.py` for technical data (factors 1-6)
- Supports 3 invocation modes: `/research` (full), `/research tech copper` (sectors), `/research ANET CRDO` (tickers)
- Design doc: `docs/plans/2026-02-20-macro-research-agent-design.md`

### Portfolio Backtesting Engine (`backtest.py`) - Feb 20, 2026
- Single-file backtesting engine using `yfinance` + `tabulate` + `numpy`
- Simulates buy-and-hold portfolio with configurable weights, benchmarks against S&P 500 (SPY)
- Metrics: total return, annualized return, Sharpe ratio, Sortino ratio, max drawdown, beta, alpha, win rate
- Outputs: performance scorecard, per-ticker breakdown, ASCII equity curve, drawdown chart, monthly returns heatmap, verdict summary
- CLI: `python backtest.py --tickers ANET,FCX --weights 0.6,0.4 --period 2y` or `--start/--end` for date range
- Importable: `from backtest import backtest; results = backtest(["ANET"], period="1y")`
- Validated: macro strategy (ANET,FCX,SCCO,XOM,CTRA,WMT,GOOGL) returned +109% vs SPY +42% over 2y, Sharpe 1.92
