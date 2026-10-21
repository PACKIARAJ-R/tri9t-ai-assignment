# AI-Powered Document Versioning and Test Case Generation

## Project Overview

This project parses PDF documents into a hierarchical structure, tracks changes between document versions, and generates QA test ideas linked to their source sections.

It uses content hashes to identify changed sections and marks associated test cases as stale when their source requirements change.

## Features

- **PDF Parsing:** Extracts headings, section numbers, body text, and parent-child relationships.
- **Content Hashing:** Generates hashes to identify changes in section content.
- **Version Comparison:** Compares V1 and V2, identifying unchanged, changed, added, and removed sections.
- **REST API:** Provides endpoints to browse sections, search content, compare versions, and retrieve test cases.
- **Named Selections:** Groups sections into reusable, version-pinned selections.
- **Test Case Generation:** Generates three rule-based QA test ideas per source section.
- **Staleness Detection:** Flags test cases whose source sections have changed.
- **Automated Tests:** Includes unit tests for hashing and heading detection.

## Technology Stack

- Python
- PyMuPDF
- FastAPI
- Uvicorn
- JSON
- Python unittest

## Project Structure

```text
AI Assignment/
├── data/
│   ├── ct200_manual.pdf
│   └── ct200_manual_v2.pdf
├── outputs/
│   ├── ct200_tree.json
│   ├── ct200_tree_v2.json
│   ├── version_diff.json
│   ├── selections.json
│   ├── test_cases.json
│   └── test_cases_backup.json
├── main.py
├── test_main.py
├── compare_versions.py
├── api.py
├── clean_duplicates.py
└── README.md
```

## Setup

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install pymupdf fastapi uvicorn
```

### 3. Run unit tests

```powershell
python -m unittest test_main.py -v
```

### 4. Parse and compare document versions

Run the following commands if you need to regenerate the outputs:

```powershell
python main.py
python compare_versions.py
```

### 5. Start the API

```powershell
python -m uvicorn api:app --reload
```

Open the interactive API documentation at:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API welcome message |
| GET | `/versions` | Lists available document versions |
| GET | `/sections?version=v1` | Lists top-level sections |
| GET | `/sections/{section_number}?version=v1` | Retrieves a section and its details |
| GET | `/search?q=keyword&version=v1` | Searches document content |
| GET | `/diff` | Retrieves version differences |
| GET | `/selections` | Lists named selections |
| GET | `/selections/{selection_id}` | Retrieves a named selection |
| POST | `/generate-tests/{selection_id}` | Generates or retrieves test ideas |
| GET | `/test-cases` | Retrieves test cases with optional filters |
| POST | `/check-staleness/{target_version}` | Checks test case staleness against a version |

## Version Comparison Results

For the supplied CT200 manual versions, the comparison currently reports:

- 23 unchanged sections
- 4 changed sections
- 1 added section
- 0 removed sections

The V2 document introduces section 5.3, Data Export, and changes the content of four existing sections or nodes as identified by the parser.

## Test Case Traceability

Each generated test case stores its source section numbers, source content hashes, selection ID, document version, creation timestamp, and stale status.

When source content changes, the staleness endpoint compares the saved hashes with the target version and identifies affected test cases.

## Current Limitations

- The test idea generator is rule-based and does not currently call an external LLM.
- Section matching primarily relies on section numbers and content hashes; renumbered sections may not be matched as the same logical node.
- PDF parsing relies on heading patterns and may need improvement for unusual layouts or complex documents.
- Staleness detection identifies direct source-section changes and does not automatically determine every indirect downstream impact.

## Running Tests

```powershell
python -m unittest test_main.py -v
```

## Future Improvements

- Integrate an LLM provider for test idea generation.
- Improve logical section matching across renumbered documents.
- Add more parser tests for irregular PDF structures.
- Improve duplicate detection and test case regeneration policies.
- Add API integration tests and validation for malformed generated output.

## License

Add the license required by your submission or repository.
