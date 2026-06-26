# Data

Put your documents here. The ingestion pipeline accepts `.pdf` and `.txt` files.

## Getting the demo dataset

The demo uses **The Adventures of Sherlock Holmes** by Arthur Conan Doyle (1892) — public domain.

Download as plain text from Project Gutenberg (CC0 / public domain):

```bash
curl -o "data/adventures-of-sherlock-holmes.txt" \
  "https://www.gutenberg.org/files/1661/1661-0.txt"
```

Then ingest:

```bash
task migrate   # create DB schema (first time only)
task ingest    # embed and store
```

## Other free sources

- [Standard Ebooks](https://standardebooks.org) — beautifully formatted public domain books (EPUB; convert to PDF with Calibre)
- [Project Gutenberg](https://www.gutenberg.org) — plain text downloads
- Any PDF you own the rights to

> **Note:** Gutenberg TXT files include a licence header (~3 KB). The chunker will ingest it too, which is harmless for a demo.
