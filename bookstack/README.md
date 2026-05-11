# BookStack Knowledge Library Demo

This folder defines a real BookStack demo for the financial-operations knowledge model.

It is separate from the Streamlit app on purpose:

- Streamlit shows the operational review surface.
- BookStack stores business concepts, procedures, payment exception playbooks, rule definitions, and governance history.

## Run Locally

BookStack requires Docker. From this folder:

```bash
cp .env.example .env
```

Generate a real BookStack application key and replace `APP_KEY` in `.env`:

```bash
docker run -it --rm --entrypoint /bin/bash lscr.io/linuxserver/bookstack:latest appkey
```

Start BookStack:

```bash
docker compose up -d
```

Then open:

```text
http://localhost:6875
```

The containers persist local demo data under `bookstack/config/`.

## Demo Content

The `content/` folder contains sanitized markdown pages that can be loaded into BookStack as a departmental library:

- business concepts for invoices, reservations, receipts, payment batches, and channels
- daily reconciliation procedures
- open-balance aging review
- allocation-ready, evidence-review, and missing-evidence definitions
- e-commerce payment-channel mapping
- chargeback handling
- rejected card transaction handling
- over/under payment review
- refund with cancellation fee handling
- rule-change governance checklist

The content is intentionally business-facing. It explains how the finance team should operate the platform, not only how the SQL works.

## Optional API Import

After creating an API token in BookStack, import the sample library:

```bash
BOOKSTACK_URL=http://localhost:6875 \
BOOKSTACK_TOKEN_ID=token_id_here \
BOOKSTACK_TOKEN_SECRET=token_secret_here \
python3 import_content.py
```

Use a fresh demo instance or delete the existing demo book first. The script creates a book called `Financial Operations Knowledge Library`.

Import the optional second book to demonstrate multiple knowledge categories:

```bash
BOOKSTACK_URL=http://localhost:6875 \
BOOKSTACK_TOKEN_ID=token_id_here \
BOOKSTACK_TOKEN_SECRET=token_secret_here \
python3 import_additional_books.py
```

This creates `Finance Operations Controls and Training`.

Apply small updates to two pages in the first book to demonstrate BookStack activity history:

```bash
BOOKSTACK_URL=http://localhost:6875 \
BOOKSTACK_TOKEN_ID=token_id_here \
BOOKSTACK_TOKEN_SECRET=token_secret_here \
python3 update_first_book_demo_pages.py
```

Update existing demo pages after changing public status labels:

```bash
BOOKSTACK_URL=http://localhost:6875 \
BOOKSTACK_TOKEN_ID=token_id_here \
BOOKSTACK_TOKEN_SECRET=token_secret_here \
python3 update_status_label_pages.py
```

## Notes

The Docker images are provided by LinuxServer.io:

- `lscr.io/linuxserver/bookstack:latest`
- `lscr.io/linuxserver/mariadb:latest`

The BookStack image requires `APP_URL`, `APP_KEY`, and database settings to be provided.

Useful references:

- LinuxServer BookStack image: https://docs.linuxserver.io/images/docker-bookstack/
- BookStack API docs: https://demo.bookstackapp.com/api/docs
