---
title: Vulcan Prime — Operational Schema
version: 0.1
date: 2026-05-25
---

# Vulcan Prime Operational Schema

This file is the single source of truth for how agents operate on this vault.
It is injected as the system prompt prefix for every agent call.

---

## Directory Contract

| Directory | Owner | Rule |
|-----------|-------|------|
| `raw/` | Human | Agents READ ONLY. Never vault_write to raw/. |
| `wiki/` | Agent | Agents create and maintain all pages here. |
| `wiki/index.md` | Agent | Updated on every INGEST. One line per page. |
| `wiki/log.md` | Agent | Append-only. INGEST/QUERY/LINT entries. |
| `wiki/answers/` | Agent | Query file-back results. |
| `feed/` | Human | Staging area for articles before ingest. |
| `experiments/` | Agent | Playground / A-B results. |

---

## Page Naming Rules

- Paths: lowercase, hyphens only, no spaces. e.g. `wiki/concepts/retrieval-augmented-generation.md`
- Entities (people, companies, products): `wiki/entities/<name>.md`
- Concepts (ideas, techniques): `wiki/concepts/<name>.md`
- Source summaries: `wiki/sources/<source-slug>.md`
- Query answers: `wiki/answers/<question-slug>.md`

---

## Frontmatter Standard

Every wiki page MUST begin with:

```yaml
---
title: <human-readable title>
date: YYYY-MM-DD
sources: [list of raw/ paths that informed this page]
tags: [optional]
---
```

---

## INGEST Workflow

1. `vault_read` the source file from `raw/` or `feed/`.
2. Analyse: list new concepts, existing page extensions, contradictions.
3. Call `request_triage_approval` with the full list of planned writes.
4. After approval, `vault_write` new/updated wiki pages.
5. `vault_write` wiki/index.md — add new entries under the right category.
6. `vault_append` wiki/log.md with:
   `## [YYYY-MM-DD HH:MM] INGEST · <source title>\n- Pages created: ...\n- Pages updated: ...\n`

---

## QUERY Workflow

1. `vault_read` wiki/index.md.
2. Identify relevant pages; `vault_read` each one.
3. Follow `[[links]]` if needed for deeper context.
4. Compose answer with citations: "According to [[wiki/concepts/rag]]..."
5. If file_back requested, `vault_write` wiki/answers/<slug>.md.

---

## LINT Workflow

1. `vault_list("wiki")` to get all pages.
2. `vault_read` each page; extract `[[links]]` and frontmatter `date`.
3. For every `[[link]]`, try `vault_read` to check it exists.
4. Identify orphan pages (never linked from any other page).
5. Flag pages whose `date` is more than 6 months in the past.
6. `vault_write` wiki/lint-report.md with structured findings.

---

## Log Entry Format (shell-parseable)

```
## [YYYY-MM-DD HH:MM] INGEST|QUERY|LINT · <title>
```

grep pattern: `grep "^## \[" wiki/log.md`

---

## Cross-Reference Rules

- Always link entity/concept names on first mention in a page.
- Use relative vault paths: `[[wiki/concepts/rag]]` not `[[rag]]`.
- index.md entry format: `- [[wiki/concepts/rag]] — Retrieval-Augmented Generation`
