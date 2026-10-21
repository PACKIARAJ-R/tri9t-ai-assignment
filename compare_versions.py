
import json
from pathlib import Path

from main import parse_pdf

V1_PDF = Path("data/ct200_manual.pdf")
V2_PDF = Path("data/ct200_manual_v2.pdf")

OUTPUT_PATH = Path("outputs/version_diff.json")


def compare_versions(v1, v2):
    """Compare sections from two manual versions."""

    old_sections = {
        section["section_number"]: section
        for section in v1["sections"]
    }

    new_sections = {
        section["section_number"]: section
        for section in v2["sections"]
    }

    results = []

    all_numbers = sorted(
        set(old_sections) | set(new_sections),
        key=lambda number: [
            int(part) for part in number.split(".")
        ]
    )

    for number in all_numbers:
        old = old_sections.get(number)
        new = new_sections.get(number)

        if old is None:
            status = "added"
        elif new is None:
            status = "removed"
        elif old["content_hash"] != new["content_hash"]:
            status = "changed"
        else:
            status = "unchanged"

        results.append({
            "section_number": number,
            "heading_v1": old["heading"] if old else None,
            "heading_v2": new["heading"] if new else None,
            "status": status,
            "hash_v1": old["content_hash"] if old else None,
            "hash_v2": new["content_hash"] if new else None
        })

    return results


if __name__ == "__main__":
    for pdf in (V1_PDF, V2_PDF):
        if not pdf.exists():
            raise FileNotFoundError(f"PDF not found: {pdf}")

    v1_tree = parse_pdf(V1_PDF)
    v2_tree = parse_pdf(V2_PDF)
    with open("outputs/ct200_tree_v2.json", "w", encoding="utf-8") as file:
        json.dump(v2_tree, file, indent=2, ensure_ascii=False)

    diff = compare_versions(v1_tree, v2_tree)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(diff, file, indent=2, ensure_ascii=False)

    print("Version comparison completed!")
    print("Output saved to:", OUTPUT_PATH)

    
    from collections import Counter

    summary = Counter(section["status"] for section in diff)

    print("\nChange Summary")
    print("--------------")
    print("Unchanged:", summary["unchanged"])
    print("Changed:", summary["changed"])
    print("Added:", summary["added"])
    print("Removed:", summary["removed"])

    print("\nSection Details")
    print("---------------")

    for section in diff:
        if section["status"] != "unchanged":
            print(
                section["section_number"],
                section["status"],
                "|",
                section["heading_v2"] or section["heading_v1"]
            )

