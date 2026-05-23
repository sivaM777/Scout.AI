# Product Requirements

## Vision

Scout AI helps shoppers decide whether a product is worth buying by turning scattered internet research into a single, fast, trustworthy decision report.

## Primary user problem

People waste time jumping between product listings, YouTube reviews, Reddit threads, and price trackers. They need a faster way to answer:

- Is this product actually good?
- Are the problems minor or deal-breakers?
- Is the current price worth it?
- Is there a better alternative at the same budget?

## MVP goals

- Accept product links from Android share intent and manual paste across many e-commerce apps
- Extract or infer product identity from a raw listing URL
- Aggregate review signals from community and editorial sources
- Produce an AI verdict with pros, cons, confidence, and a plain-language recommendation
- Show price context and a lowest-price snapshot
- Save recent reports and let users add products to a watchlist

## Success metrics

- Share-to-first-report completion under 20 seconds for cached products
- At least 40 percent of users save a product or revisit history
- More than 60 percent of generated reports include at least three distinct source types

## User experience principles

- Fast: the app should feel responsive even when scraping takes time
- Transparent: every verdict should point back to visible evidence
- Calm: clean surfaces, simple hierarchy, and low-friction actions
- Helpful: always suggest the next best action, not just a score

## Core journeys

### Share intent journey

1. User taps Share in Amazon or Flipkart.
2. User chooses Scout AI.
3. App opens directly into an analysis flow.
4. Progress UI explains what the system is doing.
5. User receives a report with verdict, price context, and alternatives.

### Manual research journey

1. User opens the app from the launcher.
2. User pastes a URL.
3. User receives the same structured report and can save it or track it.

## Marketplace strategy

- Support major Indian and global marketplaces through a registry-based adapter layer
- Treat pricing as marketplace-specific and review research as product-centric
- Always keep a generic fallback parser so new stores still work in a graceful, lower-confidence mode

## Extra features added for a more professional product

- Smart alternatives section with better-rated products in a similar range
- Watchlist with target price notes
- Source ledger that shows what the AI considered
- Recent research history for repeat sessions
- Friendly fallback mode that still renders a demo report if the backend is unavailable during development
