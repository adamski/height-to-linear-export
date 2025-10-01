# Height to Linear CSV Import Tool

Transform Height JSON exports to Linear CSV import format with automated parent-child relationship handling.

## Features

- ✅ Converts Height JSON export to Linear CSV format
- ✅ Preserves Height IDs in issue descriptions for traceability
- ✅ Maps teams, users, statuses, and priorities
- ✅ Converts dates to Linear's GMT format
- ✅ Generates parent-child relationship mapping
- ✅ Two import strategies: auto-generated IDs or custom Height IDs

## Installation

Requires Python 3.7+. No additional dependencies needed (uses standard library only).

```bash
# Make executable (optional)
chmod +x height_to_linear.py
```

## Usage

### Basic Usage (Recommended)

Generate CSV with empty IDs (safest for two-pass import):

```bash
python3 height_to_linear.py
```

This creates:
- `linear_import.csv` - Ready to import into Linear
- `parent_mapping.json` - Parent-child relationships for reference

### Generate Both Formats

Create both standard and experimental versions:

```bash
python3 height_to_linear.py --generate-both
```

This creates:
- `linear_import.csv` - Empty IDs (recommended)
- `linear_import_with_ids.csv` - With Height IDs (experimental)
- `parent_mapping.json` - Parent-child relationships

### Custom Paths

```bash
python3 height_to_linear.py \
  --input-dir /path/to/height/export \
  --output my_linear_import.csv
```

### Use Height IDs (Experimental)

Test if Linear accepts custom IDs:

```bash
python3 height_to_linear.py --use-height-ids
```

## Import Strategies

### Strategy 1: Two-Pass Import (Recommended)

This is the safest approach when Linear auto-generates IDs.

**Step 1: Initial Import**
1. Use `linear_import.csv` (empty IDs)
2. Import into Linear via CLI importer
3. Linear assigns new IDs (e.g., `NEW-1`, `NEW-2`, etc.)

**Step 2: Update Parent Relationships**
1. Export from Linear to get new ID mappings
2. Use `parent_mapping.json` to match Height parent relationships
3. Update parent-child relationships via:
   - Linear UI (manual)
   - Linear API (automated - see below)

### Strategy 2: Height IDs (Experimental)

Test if Linear preserves custom IDs from CSV.

**Step 1: Test with Small Subset**
1. Create a small CSV with ~10-20 tasks using `--use-height-ids`
2. Import into Linear
3. Check if Linear preserves the `T-XXX` IDs

**Step 2a: If Linear Accepts Custom IDs**
- ✅ Parent relationships will work automatically!
- Use `linear_import_with_ids.csv` for full import

**Step 2b: If Linear Rejects/Ignores Custom IDs**
- ❌ Fall back to Strategy 1 (two-pass import)

## Parent Mapping JSON Format

The `parent_mapping.json` file contains Height parent-child relationships:

```json
{
  "T-423": "T-224",
  "T-176": "T-1",
  "T-450": "T-224"
}
```

Key: Child Height ID → Value: Parent Height ID

## Post-Import API Script (Optional)

If you need to automate parent-child relationship updates after import, you can use Linear's API:

```python
#!/usr/bin/env python3
"""Update Linear parent-child relationships after import."""

import json
from linear import LinearClient  # pip install linear-client

# Load mappings
with open('parent_mapping.json') as f:
    height_parents = json.load(f)

# Initialize Linear client
client = LinearClient("YOUR_LINEAR_API_TOKEN")

# Get all imported issues
issues = client.issues()  # Filter by team/project as needed

# Build Height ID -> Linear ID mapping
height_to_linear = {}
for issue in issues:
    # Extract Height ID from description
    if "[Imported from Height: T-" in issue.description:
        height_id = issue.description.split("[Imported from Height: ")[1].split("]")[0]
        height_to_linear[height_id] = issue.id

# Update parent relationships
for child_height_id, parent_height_id in height_parents.items():
    if child_height_id in height_to_linear and parent_height_id in height_to_linear:
        child_linear_id = height_to_linear[child_height_id]
        parent_linear_id = height_to_linear[parent_height_id]

        client.update_issue(child_linear_id, parent_id=parent_linear_id)
        print(f"✓ Updated {child_height_id} -> parent: {parent_height_id}")
```

## Data Mapping

| Height Field | Linear Field | Notes |
|--------------|--------------|-------|
| `index` | ID (optional) | `T-{index}` format, or empty for auto-generation |
| `name` | Title | Direct mapping |
| `description` | Description | Cleaned, with Height ID reference added |
| `teamIds` | Team | First team name |
| `createdUserId` | Creator | Email from users.json |
| `assigneesIds` | Assignee | First assignee email |
| `status` | Status | Mapped (backLog→Backlog, done→Closed) |
| `fields[Priority]` | Priority | Extracted from fields array |
| `createdAt` | Created | Converted to GMT format |
| `lastActivityAt` | Updated | Converted to GMT format |
| `startedAt` | Started | Converted to GMT format |
| `completedAt` | Completed | Converted to GMT format |
| `parentTaskId` | Parent issue | Height ID reference |

## Troubleshooting

### Issue: CSV has 782 tasks but only 648 parent relationships

**Expected.** Only tasks with parents are included in `parent_mapping.json`. Top-level tasks (134 in your case) have no parents.

### Issue: Linear rejects custom IDs

**Solution:** Use Strategy 1 (two-pass import) with empty IDs.

### Issue: Date format errors

The script converts ISO 8601 dates to Linear's expected format:
- Input: `2025-01-08T10:17:10.439Z`
- Output: `Wed Jan 08 2025 10:17:10 GMT+0000 (GMT)`

If dates don't import correctly, verify Linear's expected format hasn't changed.

### Issue: Team/User not found

**Check:** Ensure the Height export includes complete `teams.json` and `users.json` files.

## Command Reference

```bash
# Show help
python3 height_to_linear.py --help

# Default (empty IDs)
python3 height_to_linear.py

# Generate both formats
python3 height_to_linear.py --generate-both

# Use Height IDs
python3 height_to_linear.py --use-height-ids

# Custom paths
python3 height_to_linear.py --input-dir PATH --output FILE
```

## License

MIT

## Support

For issues or questions, please refer to:
- Linear Import Docs: https://linear.app/docs/import-issues
- Linear CLI Importer: https://github.com/linear/linear/tree/master/packages/import# height-to-linear-export
