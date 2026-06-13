"""Ingest all 12 daily batches into Snowflake STG tables."""

from datetime import date

from dotenv import load_dotenv

load_dotenv()

from pipeline.ingest.ingest_stg import ingest_batch  # noqa: E402
from pipeline.utils.logging_config import configure_logging  # noqa: E402

configure_logging()

batch_dates = [
    date(2026, 4, 29),
    date(2026, 4, 30),
    date(2026, 5, 1),
    date(2026, 5, 2),
    date(2026, 5, 3),
    date(2026, 5, 4),
    date(2026, 5, 5),
    date(2026, 5, 6),
    date(2026, 5, 7),
    date(2026, 5, 8),
    date(2026, 5, 9),
    date(2026, 5, 10),
]

for d in batch_dates:
    print(f"Ingesting {d}...")
    ingest_batch(d)
    print("  Done.")

print("All batches ingested.")
