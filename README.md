# Scout AI

Scout AI is an Android-first shopping assistant that lets users share product links from many shopping apps, then returns an AI-guided verdict, source-backed review summary, price context, and save-for-later tracking.

This repository is structured like a delivery-ready MVP:

- `apps/mobile`: React Native Android app with share-intent support and a polished research report UX.
- `services/api-gateway`: Fastify orchestration layer for caching, history, and watchlist endpoints.
- `services/ai-engine`: FastAPI intelligence service for product parsing, review aggregation, price modeling, and summarization.
- `packages/shared`: Shared TypeScript contracts used by mobile and Node services.
- `docs`: Product and architecture notes that explain the delivery approach.

## Marketplace coverage

The intelligence service is designed around a marketplace adapter registry. This means the app can support major shopping sites such as Amazon, Flipkart, Ajio, Myntra, Nykaa, Tata CLiQ, Meesho, Croma, Reliance Digital, Vijay Sales, Snapdeal, JioMart, FirstCry, H&M, Zara, Best Buy, eBay, plus unknown stores through a generic fallback parser.

## Product extras included

- Manual paste flow in addition to Android share intent
- Watchlist and price-drop target support
- Source transparency cards so users can inspect why a verdict was generated
- AI-powered alternative suggestions for safer buying decisions
- Recent research history to make the app feel sticky and useful beyond a one-time lookup
- Live Reddit owner-discussion search and YouTube transcript-backed review signals
- SQLite-backed price snapshot storage inside the AI service for accumulating real price history over time

## Local setup

The current workspace is already set up for Android + Python development. To run everything locally:

1. On a fresh machine, install Node.js, Java 17+, Android Studio, Android SDK, and Python 3.11+.
2. Run `npm.cmd install` from the repository root.
3. Start the AI service with a Python virtual environment in `services/ai-engine`.
4. Start the Fastify gateway with `npm.cmd run dev:api`.
5. Run the mobile app with `npm.cmd run dev:android`.

## Free hosting profile

This repo now includes a no-cost Render deployment profile in [`render.yaml`](render.yaml). It runs the Fastify gateway and the FastAPI intelligence service inside a single free Render web service using [`services/api-gateway/Dockerfile.render-free`](services/api-gateway/Dockerfile.render-free).

Use this profile if you do not want any paid infrastructure yet:

1. Push the repository to GitHub, GitLab, or Bitbucket.
2. In Render, create a new Blueprint from the repository root.
3. Keep the generated web service on the free plan.
4. Add your Groq key for `LLM_API_KEY` when Render prompts for it.
5. For Android release builds, pass the deployed backend URL as `SCOUT_API_BASE_URL`, for example: `cd apps/mobile/android && .\\gradlew assembleRelease -PSCOUT_API_BASE_URL=https://<service-name>.onrender.com`.

Tradeoffs of the free profile:

- Free Render web services spin down after 15 minutes of inactivity, so the first request after idle time can be slow.
- Cache, history, and watchlist data stay in memory only, so they reset after redeploys or restarts.
- Groq can stay free only while your usage remains within the current Groq free-tier limits.
- The new AI-service SQLite price history is durable locally, but on free Render it still sits on ephemeral disk and can reset after instance replacement or redeploy.
- The Android app itself is not "hosted"; publish the APK/AAB through Google Play internal testing or closed testing.

## GitHub-ready setup

The repo now includes a GitHub validation workflow at [`.github/workflows/ci.yml`](.github/workflows/ci.yml). When you push to GitHub, it will:

- install the Node workspaces
- typecheck the shared, API, and mobile projects
- build the backend packages
- install the Python AI dependencies
- compile the AI service package to catch import and syntax issues

If Git is not installed on your computer yet, install Git for Windows first. Then, if this folder is not yet a Git repository, initialize and push it with:

1. `git init -b main`
2. `git add .`
3. `git commit -m "Initial Scout AI platform"`
4. `git remote add origin <your-github-repo-url>`
5. `git push -u origin main`

## Android release builds

For a production-ready backend URL, build Android with the helper script:

- APK: `.\scripts\build-android-release.ps1 -ApiBaseUrl https://<your-render-service>.onrender.com`
- Play Store AAB: `.\scripts\build-android-release.ps1 -ApiBaseUrl https://<your-render-service>.onrender.com -BuildTarget aab`

If you want a signed release artifact, copy [`apps/mobile/android/keystore.properties.example`](apps/mobile/android/keystore.properties.example) to `apps/mobile/android/keystore.properties` and fill in your keystore values. The Gradle config will automatically use it when present.

See the product and system docs for details:

- [`docs/product/prd.md`](docs/product/prd.md)
- [`docs/architecture/system-design.md`](docs/architecture/system-design.md)
