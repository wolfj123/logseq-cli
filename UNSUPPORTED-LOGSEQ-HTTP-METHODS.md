# Unsupported Logseq HTTP Methods

This file tracks Logseq HTTP API methods that were attempted against a live
running Logseq server and found to be unsupported.

Update this file whenever a method is tested live and the server rejects it as
missing or unsupported.

## Confirmed Unsupported

### `logseq.Editor.appendBlock`

- Status: unsupported by the tested live Logseq HTTP server
- Discovered: 2026-04-05
- How it was tested:
  - Created a temporary page with `python -m src.cli.main page create <page>`
  - Ran `python -m src.cli.main block append <page> "append-block smoke test"`
- Server response:

```json
{"error": "MethodNotExist: append_block"}
```

- Repo action taken:
  - Stopped calling `logseq.Editor.appendBlock` directly
  - Reimplemented `block append` as a fallback that inserts after the last top-level block in the page tree
  - Updated tests and docs to describe the fallback correctly

### `logseq.Editor.getPageProperties`

- Status: unsupported by the tested live Logseq HTTP server
- Discovered: 2026-04-05
- How it was tested:
  - Created a temporary page with `python -m src.cli.main page create <page>`
  - Called the service mapping for `logseq.Editor.getPageProperties` against that page during the live support audit
- Server response:

```json
{"error": "MethodNotExist: get_page_properties"}
```

- Repo action taken:
  - Stopped calling `logseq.Editor.getPageProperties` directly
  - Reimplemented `page properties` as a fallback that reads the first block from `logseq.Editor.getPageBlocksTree`
  - Updated tests and docs to describe the fallback correctly

### `logseq.Editor.createJournalPage`

- Status: unsupported by the tested live Logseq HTTP server
- Discovered: 2026-04-05
- How it was tested:
  - Called the service mapping for `logseq.Editor.createJournalPage` with `2026-04-05` during the live support audit
- Server response:

```json
{"error": "MethodNotExist: create_journal_page"}
```

- Repo action taken:
  - Stopped calling `logseq.Editor.createJournalPage` directly
  - Reimplemented `page journal` as a fallback that calls `createPage` with `YYYY_MM_DD`, then resolves the journal by `journalDay`
  - Updated tests and docs to describe the fallback correctly

## Template For Future Entries

### `logseq.Some.method`

- Status: unsupported by the tested live Logseq HTTP server
- Discovered: YYYY-MM-DD
- How it was tested:
  - Describe the exact command or API call used
- Server response:

```json
{"error": "example"}
```

- Repo action taken:
  - Describe what changed in the CLI, tests, or docs
