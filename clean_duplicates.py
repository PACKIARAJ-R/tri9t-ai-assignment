
import json
from pathlib import Path

file_path = Path("outputs/test_cases.json")
backup_path = Path("outputs/test_cases_backup.json")

# Keep a backup before making changes
backup_path.write_text(
    file_path.read_text(encoding="utf-8"),
    encoding="utf-8"
)

data = json.loads(file_path.read_text(encoding="utf-8"))
original_cases = data.get("test_cases", [])

unique_cases = []
seen = set()

for case in original_cases:
    key = (
        case.get("selection_id"),
        case.get("version"),
        tuple(case.get("source_sections", [])),
        case.get("title"),
    )

    if key not in seen:
        seen.add(key)
        unique_cases.append(case)

data["test_cases"] = unique_cases

file_path.write_text(
    json.dumps(data, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(f"Original test cases: {len(original_cases)}")
print(f"Unique test cases: {len(unique_cases)}")
print(f"Duplicates removed: {len(original_cases) - len(unique_cases)}")
print(f"Backup saved to: {backup_path}")
