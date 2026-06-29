# Data

Put your documents here. The ingestion pipeline accepts `.pdf` and `.txt` files.

## Getting the demo dataset

The demo uses two Sherlock Holmes books by Arthur Conan Doyle — both public domain.

```bash
# A Study in Scarlet (1887) — Holmes & Watson's first meeting, the Afghanistan deduction
curl -o data/a-study-in-scarlet.txt \
  https://www.gutenberg.org/files/244/244-0.txt

# The Adventures of Sherlock Holmes (1892) — 12 short stories
curl -o data/adventures-of-sherlock-holmes.txt \
  https://www.gutenberg.org/files/1661/1661-0.txt
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
