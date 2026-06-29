# Comment Style Examples

## Principles

1. **Question format** - Frame as questions, not declarations
2. **Humility** - Acknowledge you might be wrong
3. **Brevity** - Get to the point, no filler
4. **Actionable** - Include fix suggestion when appropriate

## Good Examples

### Security Issues

```
Is the file read into memory before size validation here? If so, might be worth
checking Content-Length first to prevent large uploads from exhausting memory.
```

```
Could detail=str(e) leak internal error details to the client? Might be safer to
log the exception server-side and return a generic message.
```

```
Is source_id validated as a UUID before hitting the database? Invalid input might
cause a 500. Could use FastAPI's Path with UUID type:

async def delete_pdf_source(source_id: UUID = Path(...)):
```

### Logic Issues

```
When force_reingest=True, are existing chunks deleted before re-running the pipeline?
If not, this could accumulate duplicate embeddings.
```

```
When LLM returns no choices, this returns an empty response. Should the user get
an error message or retry instead?
```

```
Does getCanonicalUrl intentionally strip query params? URLs like example.com?id=123
would lose the query. Might want to keep parsed.search in the return value.
```

### Configuration

```
Should this use validation_alias instead of alias? As-is, I don't think the
env var will bind correctly. Could be wrong though.
```

```
Should score_threshold have range validation (ge=0.0, le=1.0)? Might prevent
misconfiguration.
```

### Type Safety

```
Would it be worth using proper types instead of Any for parent_span?
Might improve type safety.
```

### Testing

```
Looks like this module doesn't have unit tests yet. Would be good to cover:
- retrieve() with various score thresholds
- empty query handling
- format_context() output
```

### Privacy/Compliance

```
Is logging document content here intentional? Wondering if this could be a
GDPR/PII concern. Maybe just log source and score?
```

### Code Style

```
Is the slice(0, 5) limit intentional? Might be worth a comment explaining
the choice or making it configurable.
```

## Bad Examples (Avoid)

### Too Assertive

```
This is wrong. You need to fix this.
```

```
This will definitely cause a bug in production.
```

### Too Wordy

```
I noticed that this particular piece of code might potentially have an issue
where under certain circumstances it could possibly lead to some problems.
I think it would be really great if you could maybe consider looking into
this and perhaps making some changes.
```

### Praise/Filler

```
Great work on this PR! Just one tiny thing...
```

```
Love what you've done here! Minor suggestion:
```

### Emojis

```
Bug alert! This could cause issues in prod.
```

## Template Patterns

### With Code Suggestion
```
{Question about the issue}? {Brief explanation of concern}:

```{language}
{suggested fix}
```
```

### Simple Question
```
{Question about behavior/intent}? {Why it matters}.
```

### Verification Request
```
{Observation about code}. {Question about whether this is intentional}?
```