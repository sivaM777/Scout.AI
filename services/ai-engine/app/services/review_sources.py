from urllib.parse import quote_plus

from app.models.schemas import ProductIdentity, SourceEvidence


def gather_review_signals(product: ProductIdentity) -> list[SourceEvidence]:
    query = quote_plus(f"{product.name} review")

    return [
        SourceEvidence(
            id="reddit-1",
            sourceType="reddit",
            title=f"{product.name} owner discussion",
            url=f"https://www.reddit.com/search/?q={query}",
            sentiment="mixed",
            summary=f"Community comments highlight practical ownership experience, especially around durability and daily use for {product.name}.",
            trustLabel="Community signal",
        ),
        SourceEvidence(
            id="youtube-1",
            sourceType="youtube",
            title=f"{product.name} video review roundup",
            url=f"https://www.youtube.com/results?search_query={query}",
            sentiment="positive",
            summary=f"Video reviewers generally like the overall value of {product.name}, while still flagging a few compromises at this price point.",
            trustLabel="Video signal",
        ),
        SourceEvidence(
            id="blog-1",
            sourceType="blog",
            title=f"{product.name} long-form review coverage",
            url=f"https://www.google.com/search?q={query}+blog+review",
            sentiment="mixed",
            summary=f"Editorial and blog reviews add more detail on sizing, finish quality, setup, and who should skip {product.name}.",
            trustLabel="Editorial signal",
        ),
    ]
