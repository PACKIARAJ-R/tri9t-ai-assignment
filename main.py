
import pymupdf
import re
import json
import hashlib
from pathlib import Path

PDF_PATH = Path("data/ct200_manual.pdf")
OUTPUT_PATH = Path("outputs/ct200_tree.json")

HEADING_PATTERN = re.compile(
    r"^(\d+(?:\.\d+)*)(?:\.)?\s+(.+?)\s*$"
)

# These are real top-level sections in the manual.
VALID_TOP_LEVEL = {str(i) for i in range(1, 9)}


def make_hash(text):
    """Create a fingerprint of section content."""
    normalized = " ".join(text.split())
    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()



def is_heading(line, current_node):
    """Check whether a line is a real section heading."""
    match = HEADING_PATTERN.match(line)

    if not match:
        return False

    number = match.group(1)
    heading = match.group(2).strip()

    if not heading:
        return False

    # Top-level sections must be numbered 1 through 8
    # and must not look like classification list entries.
    if "." not in number:
        if number not in VALID_TOP_LEVEL:
            return False

        # These two lines are classification items, not headings.
        if heading.startswith(
            ("Hypertension Stage", "Hypertensive Crisis")
        ):
            return False

        return heading[0].isupper()

    return heading[0].isupper()



def parse_pdf(pdf_path):
    document = pymupdf.open(pdf_path)

    nodes = []
    node_by_number = {}
    current_node = None
    document_title = ""

    for page in document:
        text = page.get_text()

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            # Capture the document title separately.
            if (
                not document_title
                and "CardioTrack CT-200 Home Blood" in line
            ):
                document_title = line
                continue

            match = HEADING_PATTERN.match(line)

            if match and is_heading(line, current_node):
                number = match.group(1)
                heading = match.group(2).strip()

                # Ignore duplicate section numbers.
                if number in node_by_number:
                    current_node = node_by_number[number]
                    continue

                parts = number.split(".")
                parent = None
                missing_levels = []

                # Find the nearest existing ancestor.
                for i in range(len(parts) - 1, 0, -1):
                    prefix = ".".join(parts[:i])

                    if prefix in node_by_number:
                        parent = node_by_number[prefix]
                        break

                # Record missing intermediate section numbers.
                if len(parts) > 1:
                    for i in range(1, len(parts)):
                        prefix = ".".join(parts[:i])

                        if prefix not in node_by_number:
                            missing_levels.append(prefix)

                node = {
                    "node_id": f"node_{len(nodes) + 1:03d}",
                    "section_number": number,
                    "heading": heading,
                    "level": len(parts),
                    "parent_id": (
                        parent["node_id"] if parent else None
                    ),
                    "children": [],
                    "body_lines": [],
                    "missing_intermediate_sections": missing_levels
                }

                nodes.append(node)
                node_by_number[number] = node
                current_node = node

                if parent:
                    parent["children"].append(node["node_id"])

            elif current_node is not None:
                # Keep paragraphs and table text with the section.
                current_node["body_lines"].append(line)

    document.close()

    # Finalize text and calculate content hashes.
    for node in nodes:
        node["body_text"] = "\n".join(node.pop("body_lines"))
        node["content_hash"] = make_hash(node["body_text"])

    return {
        "document_title": document_title,
        "source_file": pdf_path.name,
        "sections": nodes
    }


if __name__ == "__main__":
    if not PDF_PATH.exists():
        print(f"PDF not found: {PDF_PATH}")
    else:
        OUTPUT_PATH.parent.mkdir(
            parents=True, exist_ok=True
        )

        result = parse_pdf(PDF_PATH)

        with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
            json.dump(
                result,
                file,
                indent=2,
                ensure_ascii=False
            )

        print("PDF parsing completed!")
        print("Sections extracted:", len(result["sections"]))
        print("Output saved to:", OUTPUT_PATH)

        for node in result["sections"]:
            print(
                node["section_number"],
                node["heading"],
                "| Parent:", node["parent_id"],
                "| Missing levels:",
                node["missing_intermediate_sections"]
            )
