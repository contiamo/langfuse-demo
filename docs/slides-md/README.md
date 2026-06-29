# Markdown Slides

Markdown versions of the HTML slide decks in `../slides-html/`. Content-faithful; designed to be readable as plain markdown and renderable as slides with [Marp](https://marp.app/) or similar tools.

## Files

| File | Session | Slides |
|---|---|---|
| `00-workshop-overview.md` | MC deck — full day | 17 |
| `01-langfuse-tour.md` | Langfuse Feature Tour | 20 |
| `02-tracing-v1.md` | What Basic Tracing Looks Like | 5 |
| `03-tracing-v2.md` | Taking Tracing to Another Level | 9 |
| `04-evaluation-datasets.md` | Evaluation Datasets, Scoring & Experiments | 16 |
| `05-ai-assisted-coding.md` | AI-Assisted Coding for GenAI Engineering | 9 |

## Rendering with Marp

```bash
# Install Marp CLI
npm install -g @marp-team/marp-cli

# Preview
marp --preview 01-langfuse-tour.md

# Export to HTML
marp 01-langfuse-tour.md -o 01-langfuse-tour-marp.html
```
