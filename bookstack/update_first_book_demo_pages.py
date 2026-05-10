#!/usr/bin/env python3
"""Apply small demo updates to pages in the first BookStack demo book."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONTENT_ROOT = ROOT / "content"

BOOK_NAME = "Financial Operations Knowledge Library"
UPDATES = {
    "Invoice and Reservation References": (
        CONTENT_ROOT / "business-concepts/invoice-and-reservation-references.md",
        "\n## Demo Maintenance Note\n\n"
        "Updated during the portfolio demo to show how business definitions can be maintained "
        "inside BookStack without changing reconciliation code.\n",
    ),
    "Chargeback Review": (
        CONTENT_ROOT / "exception-handling/chargeback-review.md",
        "\n## Demo Maintenance Note\n\n"
        "Updated during the portfolio demo to show that exception playbooks can be revised "
        "as operational knowledge evolves.\n",
    ),
}


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


class BookStackClient:
    def __init__(self, base_url: str, token_id: str, token_secret: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = f"Token {token_id}:{token_secret}"

    def request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/{path.lstrip('/')}",
            data=data,
            method=method,
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
                f"BookStack API request failed: {method} {path} -> {exc.code}\n{message}"
            ) from exc

    def get(self, path: str) -> dict:
        return self.request("GET", path)

    def put(self, path: str, payload: dict) -> dict:
        return self.request("PUT", path, payload)


def list_all(client: BookStackClient, path: str) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    count = 100
    while True:
        separator = "&" if "?" in path else "?"
        response = client.get(f"{path}{separator}count={count}&offset={offset}")
        batch = response.get("data", [])
        rows.extend(batch)
        if len(batch) < count:
            return rows
        offset += count


def main() -> int:
    client = BookStackClient(
        base_url=env("BOOKSTACK_URL"),
        token_id=env("BOOKSTACK_TOKEN_ID"),
        token_secret=env("BOOKSTACK_TOKEN_SECRET"),
    )

    books = list_all(client, "books")
    book = next((row for row in books if row.get("name") == BOOK_NAME), None)
    if not book:
        raise SystemExit(f"Book not found: {BOOK_NAME}")

    pages = list_all(client, "pages")
    updated_pages = []

    for page_name, (markdown_path, note) in UPDATES.items():
        page = next(
            (
                row
                for row in pages
                if row.get("name") == page_name and row.get("book_id") == book.get("id")
            ),
            None,
        )
        if not page:
            raise SystemExit(f"Page not found in {BOOK_NAME}: {page_name}")

        markdown = markdown_path.read_text(encoding="utf-8").rstrip() + note
        client.put(
            f"pages/{page['id']}",
            {
                "name": page_name,
                "markdown": markdown,
            },
        )
        updated_pages.append(page_name)

    print("Updated BookStack pages: " + ", ".join(updated_pages))
    return 0


if __name__ == "__main__":
    sys.exit(main())
