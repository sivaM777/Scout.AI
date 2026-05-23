from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha1
from pathlib import Path
from threading import Lock

from app.config import settings
from app.models.schemas import PricePoint, ProductIdentity


@dataclass(frozen=True)
class StoredPriceSnapshot:
    observed_day: str
    observed_at: str
    price: float
    currency: str


def product_snapshot_key(product: ProductIdentity) -> str:
    identity = "|".join(
        (
            product.marketplace.strip().lower(),
            product.brand.strip().lower(),
            product.name.strip().lower(),
        )
    )
    return sha1(identity.encode("utf-8")).hexdigest()


class PriceSnapshotStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or settings.price_store_path)
        self._lock = Lock()

    def _connect(self) -> sqlite3.Connection:
        if self.db_path != Path(":memory:"):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS price_snapshots (
                product_key TEXT NOT NULL,
                observed_day TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                marketplace TEXT NOT NULL,
                brand TEXT NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                product_url TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT NOT NULL,
                PRIMARY KEY (product_key, observed_day)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_price_snapshots_product_time
            ON price_snapshots (product_key, observed_at DESC)
            """
        )
        connection.commit()

    def record_snapshot(
        self,
        product: ProductIdentity,
        product_url: str,
        price: float,
        currency: str,
        observed_at: datetime | None = None,
    ) -> None:
        timestamp = observed_at or datetime.now(UTC)
        observed_day = timestamp.date().isoformat()
        snapshot_key = product_snapshot_key(product)

        with self._lock:
            connection = self._connect()
            try:
                self._ensure_schema(connection)
                connection.execute(
                    """
                    INSERT INTO price_snapshots (
                        product_key,
                        observed_day,
                        observed_at,
                        marketplace,
                        brand,
                        product_name,
                        category,
                        product_url,
                        price,
                        currency
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(product_key, observed_day) DO UPDATE SET
                        observed_at = excluded.observed_at,
                        marketplace = excluded.marketplace,
                        brand = excluded.brand,
                        product_name = excluded.product_name,
                        category = excluded.category,
                        product_url = excluded.product_url,
                        price = excluded.price,
                        currency = excluded.currency
                    """,
                    (
                        snapshot_key,
                        observed_day,
                        timestamp.isoformat(),
                        product.marketplace,
                        product.brand,
                        product.name,
                        product.category,
                        product_url,
                        price,
                        currency,
                    ),
                )
                connection.commit()
            finally:
                connection.close()

    def list_recent_snapshots(self, product: ProductIdentity, limit: int = 5) -> list[StoredPriceSnapshot]:
        snapshot_key = product_snapshot_key(product)

        with self._lock:
            connection = self._connect()
            try:
                self._ensure_schema(connection)
                rows = connection.execute(
                    """
                    SELECT observed_day, observed_at, price, currency
                    FROM price_snapshots
                    WHERE product_key = ?
                    ORDER BY observed_day DESC
                    LIMIT ?
                    """,
                    (snapshot_key, limit),
                ).fetchall()
            finally:
                connection.close()

        snapshots = [
            StoredPriceSnapshot(
                observed_day=row["observed_day"],
                observed_at=row["observed_at"],
                price=float(row["price"]),
                currency=row["currency"],
            )
            for row in rows
        ]
        return list(reversed(snapshots))

    def load_history_points(self, product: ProductIdentity, limit: int = 5) -> list[PricePoint]:
        snapshots = self.list_recent_snapshots(product, limit=limit)
        if not snapshots:
            return []

        latest_day = snapshots[-1].observed_day
        points: list[PricePoint] = []

        for snapshot in snapshots:
            if snapshot.observed_day == latest_day:
                label = "Now"
            else:
                day = datetime.fromisoformat(f"{snapshot.observed_day}T00:00:00+00:00")
                label = day.strftime("%d %b")

            points.append(PricePoint(label=label, value=round(snapshot.price, 2)))

        return points


_default_snapshot_store = PriceSnapshotStore()


def get_price_snapshot_store() -> PriceSnapshotStore:
    return _default_snapshot_store
