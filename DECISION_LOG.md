# Decision Log

## Decision 1: How are document sections matched across versions?

**Decision:** Match sections primarily by their section numbers, then compare normalized content hashes to detect changes.

**Reasoning:** Section numbers provide a simple and understandable identifier for comparing document versions. Content hashes efficiently identify changes without comparing the entire text manually.

**Trade-off:** If a section is renamed or renumbered, the system may incorrectly classify it as removed and added, or fail to recognize it as the same logical section.

**Future improvement:** Combine section numbers with normalized titles, parent paths, and similarity-based matching to improve logical section identification.

## Decision 2: How is test case staleness determined?

**Decision:** Store each test case's source section numbers and content hashes. When checking against a target version, compare the saved hashes with the target section hashes and mark affected cases as stale.

**Reasoning:** This provides direct traceability between requirements and test ideas and makes it possible to identify which cases require review after a document change.

**Trade-off:** The current approach detects direct changes to tracked source sections but does not automatically identify indirect dependencies or every downstream impact.

**Future improvement:** Maintain an explicit dependency graph between requirements and test cases, and extend impact analysis to related sections.

## Decision 3: How should QA test ideas be generated and validated?

**Decision:** The current implementation uses a rule-based generator to create three test ideas per selected section: normal behavior, boundary conditions, and error handling.

**Reasoning:** This baseline is deterministic, easy to test, and does not require an external LLM service or API key.

**Trade-off:** The generated ideas use generic templates and may not cover all requirement-specific scenarios. The current implementation does not yet provide actual LLM-based generation or LLM output validation.

**Future improvement:** Integrate an LLM provider, request structured JSON output, validate the output against a schema, reject incomplete responses, and retain source references for every generated test idea.

## Summary

The implementation prioritizes a working document parser, version comparison, REST API, traceable test idea storage, and hash-based staleness detection. The main limitations are rule-based PDF parsing, section-number-based matching, and the absence of actual LLM integration.
