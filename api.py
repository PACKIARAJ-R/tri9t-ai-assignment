
import json
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(
    title="Tri9T Manual Versioning API",
    description="Browse and search versioned manual sections",
    version="1.0.0"
)

V1_PATH = Path("outputs/ct200_tree.json")
V2_PATH = Path("outputs/ct200_tree_v2.json")
DIFF_PATH = Path("outputs/version_diff.json")
SELECTIONS_PATH = Path("outputs/selections.json")
TEST_CASES_PATH = Path("outputs/test_cases.json")


def load_json(path):
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return None


def get_tree_path(version):
    if version == "v1":
        return V1_PATH
    if version == "v2":
        return V2_PATH
    return None


def find_selection(selection_id):
    data = load_json(SELECTIONS_PATH)

    if data is None or "selections" not in data:
        raise HTTPException(
            status_code=404,
            detail="Selections file not found or invalid"
        )

    selection = next(
        (
            item for item in data["selections"]
            if item["selection_id"] == selection_id
        ),
        None
    )

    if selection is None:
        raise HTTPException(
            status_code=404,
            detail=f"Selection '{selection_id}' not found"
        )

    return selection


@app.get("/")
def home():
    return {
        "message": "Manual Versioning API is running",
        "docs": "/docs"
    }


@app.get("/versions")
def list_versions():
    versions = []

    if V1_PATH.exists():
        versions.append("v1")
    if V2_PATH.exists():
        versions.append("v2")

    return {"versions": versions}


@app.get("/sections")
def list_sections(version: str = Query("v1")):
    path = get_tree_path(version)

    if path is None:
        raise HTTPException(400, "Version must be v1 or v2")

    tree = load_json(path)

    if tree is None:
        raise HTTPException(404, f"Data for {version} not found or invalid")

    return [
        {
            "node_id": node["node_id"],
            "section_number": node["section_number"],
            "heading": node["heading"],
            "parent_id": node["parent_id"],
            "children": node["children"]
        }
        for node in tree["sections"]
        if node["level"] == 1
    ]


@app.get("/sections/{section_number:path}")
def get_section(
    section_number: str,
    version: str = Query("v1")
):
    path = get_tree_path(version)

    if path is None:
        raise HTTPException(400, "Version must be v1 or v2")

    tree = load_json(path)

    if tree is None:
        raise HTTPException(404, f"Data for {version} not found or invalid")

    for node in tree["sections"]:
        if node["section_number"] == section_number:
            return node

    raise HTTPException(
        404,
        f"Section {section_number} not found in {version}"
    )


@app.get("/search")
def search_sections(
    q: str = Query(..., min_length=1),
    version: str = Query("v1")
):
    path = get_tree_path(version)

    if path is None:
        raise HTTPException(400, "Version must be v1 or v2")

    tree = load_json(path)

    if tree is None:
        raise HTTPException(404, f"Data for {version} not found or invalid")

    query = q.casefold()
    results = []

    for node in tree["sections"]:
        if (
            query in node["heading"].casefold()
            or query in node["body_text"].casefold()
        ):
            results.append({
                "section_number": node["section_number"],
                "heading": node["heading"],
                "body_text": node["body_text"],
                "content_hash": node["content_hash"]
            })

    return {"query": q, "version": version, "results": results}


@app.get("/diff")
def get_diff():
    diff = load_json(DIFF_PATH)

    if diff is None:
        raise HTTPException(404, "Version comparison file not found or invalid")

    return {"changes": diff}


@app.get("/selections")
def list_selections():
    data = load_json(SELECTIONS_PATH)

    if data is None or "selections" not in data:
        raise HTTPException(404, "Selections file not found or invalid")

    return data["selections"]


@app.get("/selections/{selection_id}")
def get_selection(selection_id: str):
    selection = find_selection(selection_id)
    tree_path = get_tree_path(selection["version"])

    if tree_path is None:
        raise HTTPException(400, "Unsupported selection version")

    tree = load_json(tree_path)

    if tree is None:
        raise HTTPException(404, "Manual tree not found or invalid")

    selected_sections = [
        node for node in tree["sections"]
        if node["section_number"] in selection["section_numbers"]
    ]

    return {
        "selection_id": selection["selection_id"],
        "name": selection["name"],
        "version": selection["version"],
        "sections": selected_sections
    }


def generate_test_ideas(section):
    """Create three basic QA ideas linked to their source section."""
    number = section["section_number"]
    heading = section["heading"]
    body = section["body_text"]

    templates = [
        (
            "normal behavior",
            f"Verify the device follows the documented requirements for {heading}."
        ),
        (
            "boundary conditions",
            f"Test the limits and thresholds documented for {heading}."
        ),
        (
            "error handling",
            f"Test the device response to relevant error or abnormal conditions for {heading}."
        )
    ]

    ideas = []

    for test_type, description in templates:
        ideas.append({
            "title": f"Verify {test_type} for {heading}",
            "description": description,
            "source_sections": [number],
            "source_hashes": {
                number: section["content_hash"]
            }
        })

    return ideas


@app.post("/generate-tests/{selection_id}")
def generate_tests(selection_id: str):
    selection = find_selection(selection_id)
    version = selection["version"]
    tree_path = get_tree_path(version)

    if tree_path is None:
        raise HTTPException(400, "Unsupported selection version")

    tree = load_json(tree_path)

    if tree is None:
        raise HTTPException(404, "Manual tree not found or invalid")

    selected_numbers = set(selection["section_numbers"])
    selected_sections = [
        section for section in tree["sections"]
        if section["section_number"] in selected_numbers
    ]

    if not selected_sections:
        raise HTTPException(400, "Selection contains no valid sections")

    # Load existing cases and prevent duplicate generation for the
    # same named selection and pinned version.
    if TEST_CASES_PATH.exists():
        stored_data = load_json(TEST_CASES_PATH)
        if stored_data is None or not isinstance(
            stored_data.get("test_cases"), list
        ):
            raise HTTPException(500, "Test-case storage is invalid")
    else:
        stored_data = {"test_cases": []}

    existing_cases = [
        case for case in stored_data["test_cases"]
        if case.get("selection_id") == selection_id
        and case.get("version") == version
    ]

    if existing_cases:
        return {
            "selection_id": selection_id,
            "version": version,
            "generated_count": 0,
            "message": "Test cases already exist; returning existing cases.",
            "test_cases": existing_cases
        }

    new_cases = []

    for section in selected_sections:
        new_cases.extend(generate_test_ideas(section))

    if not 3 <= len(new_cases) <= 100:
        raise HTTPException(
            500,
            "Generated test count is outside allowed limits"
        )

    timestamp = datetime.now(timezone.utc).isoformat()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

    for index, case in enumerate(new_cases, start=1):
        case["test_id"] = f"{selection_id}_{run_id}_{index}"
        case["selection_id"] = selection_id
        case["version"] = version
        case["created_at"] = timestamp
        case["stale"] = False

    stored_data["test_cases"].extend(new_cases)
    TEST_CASES_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(TEST_CASES_PATH, "w", encoding="utf-8") as file:
        json.dump(stored_data, file, indent=2, ensure_ascii=False)

    return {
        "selection_id": selection_id,
        "version": version,
        "generated_count": len(new_cases),
        "test_cases": new_cases
    }



@app.get("/test-cases")
def list_test_cases(
    selection_id: str = Query(None),
    version: str = Query(None),
    section_number: str = Query(None),
    stale: bool = Query(None)
):
    """Retrieve test cases with selection, source, version and stale filters."""

    stored_data = load_json(TEST_CASES_PATH)

    if stored_data is None or not isinstance(
        stored_data.get("test_cases"), list
    ):
        raise HTTPException(
            status_code=404,
            detail="Test-case storage not found or invalid"
        )

    cases = stored_data["test_cases"]

    if selection_id:
        cases = [
            case for case in cases
            if case.get("selection_id") == selection_id
        ]

    if version:
        cases = [
            case for case in cases
            if case.get("version") == version
        ]

    if section_number:
        cases = [
            case for case in cases
            if section_number in case.get("source_sections", [])
        ]

    if stale is not None:
        cases = [
            case for case in cases
            if case.get("stale", False) == stale
        ]

    return {
        "count": len(cases),
        "test_cases": cases
    }


@app.post("/check-staleness/{target_version}")
def check_staleness(target_version: str):
    """Compare stored test source hashes with a target manual version."""

    tree_path = get_tree_path(target_version)

    if tree_path is None:
        raise HTTPException(
            status_code=400,
            detail="Version must be v1 or v2"
        )

    tree = load_json(tree_path)

    if tree is None:
        raise HTTPException(
            status_code=404,
            detail=f"Tree for {target_version} not found"
        )

    stored_data = load_json(TEST_CASES_PATH)

    if stored_data is None or not isinstance(
        stored_data.get("test_cases"), list
    ):
        raise HTTPException(
            status_code=404,
            detail="Test-case storage not found or invalid"
        )

    current_hashes = {
        section["section_number"]: section["content_hash"]
        for section in tree["sections"]
    }

    updated = []
    stale_count = 0

    for case in stored_data["test_cases"]:
        changed_sources = []

        for section_number, old_hash in case.get(
            "source_hashes", {}
        ).items():
            current_hash = current_hashes.get(section_number)

            if current_hash is None or current_hash != old_hash:
                changed_sources.append(section_number)

        case["stale"] = bool(changed_sources)
        case["stale_against_version"] = target_version
        case["changed_source_sections"] = changed_sources

        if case["stale"]:
            stale_count += 1

        updated.append(case)

    with open(TEST_CASES_PATH, "w", encoding="utf-8") as file:
        json.dump(
            stored_data,
            file,
            indent=2,
            ensure_ascii=False
        )

    return {
        "target_version": target_version,
        "checked_count": len(updated),
        "stale_count": stale_count,
        "fresh_count": len(updated) - stale_count,
        "test_cases": updated
    }
