from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import quote_plus

import httpx

from app.config import settings
from app.models.schemas import ProductIdentity, SourceEvidence

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:  # pragma: no cover - exercised only when dependency is unavailable
    YouTubeTranscriptApi = None


REVIEW_HEADERS = {
    "Accept": "application/json,text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
}
CATEGORY_LENSES = {
    "beauty": {
        "pain_points": "ingredients irritation oxidation lasting review",
        "editorial_sites": "site:nykaa.com OR site:beautypedia.com OR site:byrdie.com",
        "editorial_title": "ingredient and wear-test coverage",
        "community_title": "skin-type and sensitivity checks",
    },
    "electronics": {
        "pain_points": "battery camera heating display durability review",
        "editorial_sites": "site:91mobiles.com OR site:gadgets360.com OR site:techradar.com OR site:tomsguide.com",
        "editorial_title": "spec and performance coverage",
        "community_title": "long-term ownership issues",
    },
    "fashion": {
        "pain_points": "fit fabric quality sizing comfort wash review",
        "editorial_sites": "site:ajio.com OR site:myntra.com OR site:vogue.in OR site:elle.com",
        "editorial_title": "fit and styling coverage",
        "community_title": "fit, quality, and wash feedback",
    },
    "general": {
        "pain_points": "problems durability quality review",
        "editorial_sites": "site:reddit.com OR site:youtube.com",
        "editorial_title": "general review coverage",
        "community_title": "owner feedback checks",
    },
    "grocery": {
        "pain_points": "taste freshness packaging value review",
        "editorial_sites": "site:jiomart.com OR site:amazon.in OR site:youtube.com",
        "editorial_title": "taste and value coverage",
        "community_title": "freshness and packaging feedback",
    },
    "kids": {
        "pain_points": "safety comfort durability cleaning review",
        "editorial_sites": "site:firstcry.com OR site:thebump.com OR site:whattoexpect.com",
        "editorial_title": "parent-focused review coverage",
        "community_title": "safety and comfort checks",
    },
}
POSITIVE_HINTS = {
    "amazing",
    "best",
    "comfortable",
    "excellent",
    "good",
    "great",
    "love",
    "premium",
    "recommend",
    "reliable",
    "solid",
    "value",
    "worth",
}
NEGATIVE_HINTS = {
    "avoid",
    "bad",
    "bug",
    "cheap",
    "complaint",
    "disappoint",
    "heating",
    "issue",
    "poor",
    "problem",
    "refund",
    "return",
    "skip",
    "worst",
}


@dataclass(frozen=True)
class RedditPost:
    title: str
    url: str
    body: str
    score: int
    comment_count: int


@dataclass(frozen=True)
class YouTubeReview:
    video_id: str
    title: str
    url: str
    transcript: str


def _clean_phrase(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _base_search_phrase(product: ProductIdentity) -> str:
    name = _clean_phrase(product.name)
    brand = _clean_phrase(product.brand)
    if not name.lower().startswith(brand.lower()):
        name = f"{brand} {name}"
    return name


def _query_url(prefix: str, phrase: str) -> str:
    return prefix.format(query=quote_plus(_clean_phrase(phrase)))


def _infer_sentiment(text: str, fallback: str = "mixed") -> str:
    normalized = text.lower()
    positive = sum(1 for hint in POSITIVE_HINTS if hint in normalized)
    negative = sum(1 for hint in NEGATIVE_HINTS if hint in normalized)

    if positive >= negative + 2:
        return "positive"
    if negative >= positive + 2:
        return "negative"
    return fallback


def _clip_text(value: str, max_words: int = 36) -> str:
    tokens = value.split()
    if len(tokens) <= max_words:
        return " ".join(tokens)
    return f"{' '.join(tokens[:max_words])}..."


def _flatten_runs(value: Any) -> str:
    if isinstance(value, dict):
        if isinstance(value.get("simpleText"), str):
            return value["simpleText"]
        if isinstance(value.get("runs"), list):
            return " ".join(
                run["text"].strip()
                for run in value["runs"]
                if isinstance(run, dict) and isinstance(run.get("text"), str)
            ).strip()
    return ""


def _walk_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _extract_yt_initial_data(html: str) -> dict[str, Any] | None:
    patterns = (
        r"var ytInitialData = (\{.*?\});",
        r"window\[[\"']ytInitialData[\"']\]\s*=\s*(\{.*?\});",
        r"ytInitialData\s*=\s*(\{.*?\});",
    )
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.DOTALL)
        if not match:
            continue

        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

    return None


async def _fetch_reddit_posts(client: httpx.AsyncClient, query: str, limit: int) -> list[RedditPost]:
    response = await client.get(
        "https://www.reddit.com/search.json",
        params={"q": query, "sort": "relevance", "limit": limit, "type": "link"},
    )
    if not response.is_success:
        return []

    payload = response.json()
    children = payload.get("data", {}).get("children", [])
    posts: list[RedditPost] = []

    for child in children:
        data = child.get("data", {})
        title = _clean_phrase(str(data.get("title", "")))
        permalink = data.get("permalink")
        if not title or not permalink:
            continue

        posts.append(
            RedditPost(
                title=title,
                url=f"https://www.reddit.com{permalink}",
                body=_clean_phrase(str(data.get("selftext", ""))),
                score=int(data.get("score", 0) or 0),
                comment_count=int(data.get("num_comments", 0) or 0),
            )
        )

    return posts


def _parse_youtube_search_results(html: str, limit: int) -> list[dict[str, str]]:
    payload = _extract_yt_initial_data(html)
    if not payload:
        return []

    videos: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for node in _walk_dicts(payload):
        renderer = node.get("videoRenderer")
        if not isinstance(renderer, dict):
            continue

        video_id = renderer.get("videoId")
        title = _flatten_runs(renderer.get("title"))
        if not video_id or not title or video_id in seen_ids:
            continue

        seen_ids.add(video_id)
        videos.append(
            {
                "video_id": video_id,
                "title": _clean_phrase(title),
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
        )
        if len(videos) >= limit:
            break

    return videos


async def _fetch_youtube_transcript(video_id: str) -> str | None:
    if YouTubeTranscriptApi is None:
        return None

    try:
        transcript = await asyncio.to_thread(YouTubeTranscriptApi.get_transcript, video_id, languages=["en"])
    except Exception:
        return None

    text = " ".join(
        item["text"].strip()
        for item in transcript
        if isinstance(item, dict) and isinstance(item.get("text"), str) and item["text"].strip()
    )
    cleaned = _clean_phrase(text)
    return cleaned or None


async def _search_youtube_reviews(client: httpx.AsyncClient, query: str, limit: int) -> list[YouTubeReview]:
    response = await client.get(
        "https://www.youtube.com/results",
        params={"search_query": query, "hl": "en", "gl": "IN"},
    )
    if not response.is_success:
        return []

    videos = _parse_youtube_search_results(response.text, limit=limit)
    reviews: list[YouTubeReview] = []

    for video in videos:
        transcript = await _fetch_youtube_transcript(video["video_id"])
        if not transcript:
            continue

        reviews.append(
            YouTubeReview(
                video_id=video["video_id"],
                title=video["title"],
                url=video["url"],
                transcript=transcript,
            )
        )

    return reviews


def _reddit_source(posts: list[RedditPost], product: ProductIdentity, fallback_query: str) -> SourceEvidence:
    if not posts:
        return SourceEvidence(
            id="reddit-owner-signal",
            sourceType="reddit",
            title=f"{product.name} Reddit owner discussions",
            url=_query_url("https://www.reddit.com/search/?q={query}", fallback_query),
            sentiment="mixed",
            summary=(
                f"Live Reddit posts were unavailable, so this falls back to a direct owner-discussion search for {product.name}."
            ),
            trustLabel="Owner signal",
        )

    top_titles = "; ".join(post.title for post in posts[:2])
    body_snippets = " ".join(post.body for post in posts if post.body)
    summary_text = _clip_text(_clean_phrase(f"{top_titles} {body_snippets}"), max_words=34)
    sentiment = _infer_sentiment(f"{top_titles} {body_snippets}")

    return SourceEvidence(
        id="reddit-owner-signal",
        sourceType="reddit",
        title=posts[0].title,
        url=posts[0].url,
        sentiment=sentiment,
        summary=(
            f"Top Reddit threads for {product.name} mention {summary_text}"
        ),
        trustLabel="Owner signal",
    )


def _youtube_source(reviews: list[YouTubeReview], product: ProductIdentity, fallback_query: str) -> SourceEvidence:
    if not reviews:
        return SourceEvidence(
            id="youtube-review-signal",
            sourceType="youtube",
            title=f"{product.name} YouTube review roundup",
            url=_query_url("https://www.youtube.com/results?search_query={query}", fallback_query),
            sentiment="mixed",
            summary=(
                f"Live transcript extraction was unavailable, so this falls back to a direct YouTube review search for {product.name}."
            ),
            trustLabel="Video signal",
        )

    transcript_summary = _clip_text(reviews[0].transcript, max_words=38)
    sentiment = _infer_sentiment(" ".join(review.transcript for review in reviews), fallback="positive")

    return SourceEvidence(
        id="youtube-review-signal",
        sourceType="youtube",
        title=reviews[0].title,
        url=reviews[0].url,
        sentiment=sentiment,
        summary=(
            f"Transcript-backed YouTube coverage for {product.name} highlights {transcript_summary}"
        ),
        trustLabel="Video signal",
    )


async def gather_review_signals(product: ProductIdentity, product_url: str | None = None) -> list[SourceEvidence]:
    lens = CATEGORY_LENSES.get(product.category, CATEGORY_LENSES["general"])
    phrase = _base_search_phrase(product)
    owner_query = f"{phrase} review owner experience"
    issue_query = f"{phrase} {lens['pain_points']}"
    comparison_query = f"{phrase} vs alternatives"
    editorial_query = f"{phrase} review {lens['editorial_sites']}"
    youtube_query = f"{phrase} long term review"

    timeout = httpx.Timeout(settings.review_fetch_timeout_seconds)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=REVIEW_HEADERS) as client:
        reddit_task = _fetch_reddit_posts(client, owner_query, settings.reddit_search_limit)
        youtube_task = _search_youtube_reviews(client, youtube_query, settings.youtube_search_limit)
        reddit_result, youtube_result = await asyncio.gather(reddit_task, youtube_task, return_exceptions=True)

    reddit_posts = reddit_result if isinstance(reddit_result, list) else []
    youtube_reviews = youtube_result if isinstance(youtube_result, list) else []

    sources = [
        _reddit_source(reddit_posts, product, owner_query),
        _youtube_source(youtube_reviews, product, youtube_query),
        SourceEvidence(
            id="editorial-review-signal",
            sourceType="editorial",
            title=f"{product.name} {lens['editorial_title']}",
            url=_query_url("https://www.google.com/search?q={query}", editorial_query),
            sentiment="mixed",
            summary=(
                f"Editorial coverage helps validate structured pros and cons for {product.name}, with more disciplined testing than raw marketplace comments."
            ),
            trustLabel="Editorial signal",
        ),
        SourceEvidence(
            id="community-issues-signal",
            sourceType="community",
            title=f"{product.name} {lens['community_title']}",
            url=_query_url("https://www.google.com/search?q={query}", issue_query),
            sentiment="mixed",
            summary=(
                f"This query stays focused on the risk checks for {product.name}, especially around {lens['pain_points']}."
            ),
            trustLabel="Risk check",
        ),
        SourceEvidence(
            id="comparison-signal",
            sourceType="blog",
            title=f"{product.name} alternative comparisons",
            url=_query_url("https://www.google.com/search?q={query}", comparison_query),
            sentiment="mixed",
            summary=(
                f"Comparison coverage helps position {product.name} against close substitutes, which is especially useful when the live price feels borderline."
            ),
            trustLabel="Comparison signal",
        ),
    ]

    if product_url:
        sources.append(
            SourceEvidence(
                id="listing-signal",
                sourceType="community",
                title=f"{product.marketplace} listing for {product.name}",
                url=product_url,
                sentiment="mixed",
                summary=(
                    f"Keep the original {product.marketplace} listing in the loop to cross-check seller, size or variant details, and any buyer Q&A that could change the final decision."
                ),
                trustLabel="Listing signal",
            )
        )

    return sources
