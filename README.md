# Backtest Baby

## Inspiration
We were up for a technical challenge at **Hack Princeton** and wanted to fully show the powers and capabilities of AI agents. We also looked at [Alpaca](https://www.ycombinator.com/companies/alpaca), a YC startup that provides stock and crypto API brokerage services. Our goal was to build on this idea and provide users with more than just data — we wanted to offer data, a research agent to help build strategies, and an agent that runs tests in a sandbox environment to validate them. What would normally take hours can now be done in a minute.

## What It Does
We offer **three main agentic services**:

1. **Strategy Builder & Backtester** – Describe a strategy or thesis in natural language. The agent understands, builds, and backtests it against historical data and benchmarks across multiple simulations, returning performance metrics and graphs.  
2. **Research Agent** – Chat with an agent that crawls the web, scrapes sites, and performs complex natural language queries on **X** to gather the latest financial news.  
3. **Signal Agent** – Define signal conditions for monitoring. Once a signal triggers, the agent automatically analyzes it and reports findings in real time.

Together, these services help users **develop and test trading strategies faster than ever before.**

## How We Built It
- **Dedalus SDK** was used to orchestrate AI agents and workflows.  
- **X API** was integrated for real-time financial news and signal data.  
- Agents used **yfinance** and in-process code execution for backtesting.  
- We built **MCP servers** for web search, scraping, and a custom **X MCP server** for complex research queries.  
- Finally, we designed a **webhook-like architecture** to push real-time signals from X into Dedalus agents, allowing live analysis.

## Challenges We Ran Into
1. **Webhooks:** X does not provide webhook endpoints without an enterprise subscription.  
2. **Invocation Limits:** Dedalus agents typically require direct user input to run, not event-based signals.  

To overcome this, we engineered a **custom webhook-like workaround** to handle signal-based agent invocations.

## Accomplishments We're Proud Of
- Building a **fault-tolerant backtesting pipeline** that orchestrates four services within one agent using smart tool chaining in Dedalus.  
- Implementing **real-time signal analysis** with a creative workaround to bypass API and SDK limitations.

## What We Learned
- How to design and implement a **custom backtesting engine** from scratch.  
- How to **chain AI tools** effectively to perform multi-step, domain-specific tasks.  
- That even complex workflows can be automated efficiently through **agentic reasoning and orchestration**.

## What's Next for Backtest Baby
- Expanding to include **Monte Carlo simulations** and **complex signal definitions**.  
- Integrating more **data sources** for richer backtesting and research.  
- Connecting with **Alpaca’s brokerage API** to enable **live trading** directly from validated strategies.

## Built With
- **Claude**  
- **Dedalus**  
- **Grok**  
- **MongoDB**  
- **Next.js**  
- **OpenAI**  
- **Python**
