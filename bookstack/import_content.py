#!/usr/bin/env python3
"""Import the demo finance-operations library into a BookStack instance."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONTENT_ROOT = ROOT / "content"

BOOK_NAME = "Financial Operations Knowledge Library"
BOOK_DESCRIPTION = (
    "Sanitized operating library for payment operations, reconciliation, "
    "exception handling, business concepts, and governance."
)

LIBRARY = [
    (
        "Business Concepts",
        [
            "business-concepts/invoice-and-reservation-references.md",
            "business-concepts/payment-channels-and-ecommerce.md",
            "business-concepts/receipts-and-payment-batches.md",
        ],
    ),
    (
        "Daily Procedures",
        [
            "daily-procedures/daily-reconciliation-run.md",
            "daily-procedures/open-payment-batch-aging-review.md",
        ],
    ),
    (
        "Matching Rules",
        [
            "matching-rules/match-check-unmatched.md",
            "matching-rules/gateway-token-mapping.md",
        ],
    ),
    (
        "Exception Handling",
        [
            "exception-handling/chargeback-review.md",
            "exception-handling/rejected-card-transactions.md",
            "exception-handling/over-under-payment-review.md",
            "exception-handling/refund-with-cancellation-fee.md",
        ],
    ),
    (
        "Governance",
        [
            "governance/rule-change-checklist.md",
        ],
    ),
]


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


class BookStackClient:
    def __init__(self, base_url: str, token_id: str, token_secret: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = f"Token {token_id}:{token_secret}"

    def post(self, path: str, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/{path.lstrip('/')}",
            data=data,
            method="POST",
            headers={
                "Authorization": self.auth,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(
                f"BookStack API request failed: POST {path} -> {exc.code}\n{message}"
            ) from exc


def page_name(markdown_path: Path) -> str:
    first_line = markdown_path.read_text(encoding="utf-8").splitlines()[0]
    return first_line.lstrip("#").strip()


def main() -> int:
    client = BookStackClient(
        base_url=env("BOOKSTACK_URL"),
        token_id=env("BOOKSTACK_TOKEN_ID"),
        token_secret=env("BOOKSTACK_TOKEN_SECRET"),
    )

    book = client.post(
        "books",
        {
            "name": BOOK_NAME,
            "description": BOOK_DESCRIPTION,
        },
    )
    book_id = book["id"]

    for chapter_name, page_paths in LIBRARY:
        chapter = client.post(
            "chapters",
            {
                "book_id": book_id,
                "name": chapter_name,
                "description": f"{chapter_name} for the reconciliation operating model.",
            },
        )
        chapter_id = chapter["id"]

        for relative_path in page_paths:
            markdown_path = CONTENT_ROOT / relative_path
            client.post(
                "pages",
                {
                    "chapter_id": chapter_id,
                    "name": page_name(markdown_path),
                    "markdown": markdown_path.read_text(encoding="utf-8"),
                },
            )

    print(f"Imported BookStack demo library: {BOOK_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
