# Retrieval Improvement Ideas

These are planned enhancements to the RAG pipeline that go beyond basic vector search.
Each one is a good workshop exercise and produces visible, comparable traces in Langfuse.

---

## 1. HyDE — Hypothetical Document Embeddings

**Problem:** The user's question and the relevant passage live in different semantic spaces.
*"How did Holmes deduce...?"* doesn't embed close to *"You have been in Afghanistan, I perceive"*.

**Fix:** Before the vector search, ask the LLM to write a short *hypothetical answer*,
then embed that instead of the raw question. A fake answer uses the vocabulary of the
source text and lands much closer to the real passage in embedding space.

```python
# pipeline.py — before similarity_search()
hypothesis = await llm_call(
    f"Write a one-paragraph answer to: {question}\nBase it on Sherlock Holmes stories."
)
[vec] = await embed([hypothesis], settings.embedding_model)
```

**Langfuse angle:** the extra LLM call shows up as a separate generation — participants
can compare retrieval quality with and without it using Langfuse experiments.

---

## 2. Query Rewriting

**Problem:** Users phrase questions conversationally; the corpus uses narrative prose.

**Fix:** Ask the LLM to rephrase the question as a declarative statement or keyword list
that matches the language of the source text.

```python
rewritten = await llm_call(
    f"Rephrase this as keywords or a factual statement for document search: {question}"
)
[vec] = await embed([rewritten], settings.embedding_model)
```

**Langfuse angle:** cheaper than HyDE (shorter prompt, shorter output), good A/B
comparison candidate in a Langfuse experiment.

---

## 3. Multi-Query Retrieval

**Problem:** A single query vector may miss relevant passages that use different phrasing.

**Fix:** Generate 2–3 alternative phrasings of the question, run each through the vector
search, deduplicate and merge the results before passing context to the LLM.

```python
variants = await llm_call(
    f"Write 3 different search queries for: {question}\nReturn as a JSON list."
)
all_chunks = []
for variant in variants:
    [vec] = await embed([variant], settings.embedding_model)
    all_chunks.extend(await repo.similarity_search(vec, top_k=3))
chunks = deduplicate(all_chunks)
```

**Langfuse angle:** multiple retrieval spans visible per turn; participants can inspect
which variant found which passage and measure whether broader recall improves faithfulness scores.
