# Height to Linear Import Tool

Transform Height JSON exports to Linear CSV import format with automated parent-child relationship handling.

## Features

- Converts Height JSON export to Linear CSV format
- Preserves Height IDs in issue descriptions for traceability
- Maps teams, users, statuses, and priorities
- Converts dates to Linear's GMT format
- Automated parent-child relationship setup via Linear API

## Quick Start

```bash
# 1. Generate CSV files
python3 height_to_linear.py

# 2. Import into Linear (via CLI or web UI)
linear-import csv

# 3. Set up parent-child relationships
export LINEAR_API_KEY="your_key_here"
python3 update_parent_relationships.py
```

**For complete step-by-step instructions, see [IMPORT_GUIDE.md](IMPORT_GUIDE.md)**

## Requirements

- Python 3.7+
- `requests` library (for parent relationship updates only)

## Scripts

### `height_to_linear.py`

Transforms Height JSON export to Linear CSV format.

**Basic usage:**
```bash
python3 height_to_linear.py
```

**Options:**
- `--input-dir PATH` - Height export directory (default: `export-2025-09-29-FevGPS`)
- `--output FILE` - Output CSV path (default: `linear_import.csv`)
- `--generate-both` - Generate both standard and experimental formats
- `--use-height-ids` - Use Height IDs in CSV (experimental)

### `update_parent_relationships.py`

Updates parent-child relationships in Linear after import via GraphQL API.

**Usage:**
```bash
export LINEAR_API_KEY="lin_api_..."
python3 update_parent_relationships.py
```

## Data Mapping

| Height Field | Linear Field | Notes |
|--------------|--------------|-------|
| `index` | Description tag | Preserved as `[Imported from Height: T-{index}]` |
| `name` | Title | Direct mapping |
| `description` | Description | Cleaned, with Height ID reference added |
| `teamIds` | Team | First team name |
| `createdUserId` | Creator | Email from users.json |
| `assigneesIds` | Assignee | First assignee email |
| `status` | Status | Mapped to Linear states (Backlog, Todo, In Progress, Done) |
| `fields[Priority]` | Priority | Extracted from fields array |
| `createdAt` | Created | Converted to Linear GMT format |
| `lastActivityAt` | Updated | Converted to Linear GMT format |
| `startedAt` | Started | Converted to Linear GMT format |
| `completedAt` | Completed | Converted to Linear GMT format |
| `parentTaskId` | Parent issue | Set via API after import using `parent_mapping.json` |

## Output Files

- `linear_import.csv` - CSV file for initial Linear import
- `parent_mapping.json` - Parent-child relationships

## Resources

- [IMPORT_GUIDE.md](IMPORT_GUIDE.md) - Complete step-by-step import workflow
- [Linear Import Docs](https://linear.app/docs/import-issues)
- [Linear API Docs](https://developers.linear.app/docs)

## License

MIT
