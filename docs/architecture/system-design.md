# System Design

## Overview

Scout AI uses a three-layer architecture:

1. React Native Android app for the share-intent entry point and report UX
2. Fastify API gateway for orchestration, caching, watchlist, and client-friendly endpoints
3. FastAPI intelligence service for product parsing, review harvesting, price modeling, and summarization

## Why this split works

- Mobile stays lightweight and focused on user experience
- Fastify keeps API latency low and provides a clean seam for auth, rate limits, and analytics later
- FastAPI is a natural home for scraping, NLP, and async enrichment tasks

## Data flow

1. Mobile receives a listing URL from Android share intent or manual paste.
2. Mobile sends the URL to `POST /v1/analysis`.
3. API gateway checks Redis or in-memory cache using a normalized URL hash.
4. On a cache miss, the gateway calls the AI service.
5. AI service builds a report with:
   - product identity
   - source evidence
   - pricing insight
   - verdict
   - alternatives
6. Gateway stores the response for reuse and returns it to the app.

## Marketplace adapter strategy

- A registry resolves the incoming URL to a known marketplace adapter
- Each adapter can hold domain matching, category hints, selectors, and pricing rules
- Unknown stores fall back to a generic adapter instead of failing hard
- This keeps support for stores like Amazon, Flipkart, Ajio, Myntra, Nykaa, Croma, Reliance Digital, and others maintainable over time

## Suggested production hardening

- Replace memory repositories with PostgreSQL-backed tables
- Use a background queue for slow scraping workloads
- Add auth and user profiles
- Add observability via OpenTelemetry and structured logs
- Introduce daily price snapshots through scheduled jobs
- Add abuse protection around URL ingestion and outbound scraping

## Mobile design decisions

- Bottom tabs for retained-value areas like history and watchlist
- Dedicated analysis screen with staged progress updates
- Report screen centered on a single verdict card, then supporting evidence
- Shared theme tokens for spacing, colors, radii, and typography
