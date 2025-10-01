#!/usr/bin/env python3
"""
Transform Height JSON export to Linear CSV import format.

Usage:
    python height_to_linear.py [--input-dir DIR] [--output FILE]
"""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Linear CSV column headers
LINEAR_HEADERS = [
    "ID", "Team", "Title", "Description", "Status", "Estimate", "Priority",
    "Project ID", "Project", "Creator", "Assignee", "Labels", "Cycle Number",
    "Cycle Name", "Cycle Start", "Cycle End", "Created", "Updated", "Started",
    "Triaged", "Completed", "Canceled", "Archived", "Due Date", "Parent issue",
    "Initiatives", "Project Milestone ID", "Project Milestone", "SLA Status", "Roadmaps"
]

# Status mapping from Height status IDs to Linear status names
STATUS_MAP = {
    # Standard statuses
    "backLog": "Backlog",
    "done": "Done",
    "inProgress": "In Progress",
    "Open": "Open",
    "Closed": "Done",

    # UUID statuses (map to standard Linear statuses)
    "c79706e5-618d-4c3f-a31c-38e2b45c3afb": "Backlog",
    "1719cfde-fdf7-4d15-83bd-6bc1e6f46b3b": "Todo",
    "28e2b389-fb49-4595-a5f6-c338553dbbc2": "Todo",
    "1eb8b8d9-9f0a-4f31-9d19-b01f841a9ffb": "Todo",
    "7aa06750-ed00-4d8d-80a1-9946317cd01a": "Todo",
    "877844db-f8be-45b2-ba3b-606c93871542": "Todo",
    "62e6162e-c5af-4f73-863d-e7c1f9fb03cc": "Todo",
    "d6a747d1-a448-440f-973a-129731f79dd3": "Todo",
    "ce2bb19b-bdfb-41e2-8562-14a65e26e0db": "Todo",
    "4e1f732d-5694-4af4-befb-487d982c66da": "Todo",
}


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load and parse a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def convert_iso_to_linear_date(iso_date: Optional[str]) -> str:
    """
    Convert ISO 8601 date to Linear's expected format.

    Example: "2025-01-08T10:17:10.439Z" -> "Wed Jan 08 2025 10:17:10 GMT+0000 (GMT)"
    """
    if not iso_date:
        return ""

    try:
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        # Format: "Fri Mar 17 2023 21:33:58 GMT+0000 (GMT)"
        return dt.strftime("%a %b %d %Y %H:%M:%S GMT+0000 (GMT)")
    except (ValueError, AttributeError):
        return ""


def build_mappings(tasks: List[Dict], teams: List[Dict], users: List[Dict]) -> Dict[str, Dict]:
    """Build lookup dictionaries for IDs."""

    # Map team ID -> team name
    team_map = {team['id']: team['name'] for team in teams}

    # Map user ID -> email
    user_map = {}
    for user in users:
        if 'email' in user:
            user_map[user['id']] = user['email']

    # Map task UUID -> T-{index}
    task_id_to_index = {task['id']: f"T-{task['index']}" for task in tasks}

    return {
        'teams': team_map,
        'users': user_map,
        'task_ids': task_id_to_index
    }


def clean_description(description: str) -> str:
    """Clean up description text."""
    if not description:
        return ""

    # Remove specific markers that were added during import
    description = description.replace("┆Task is synchronized with this Gitlab issue by Unito", "")

    # Clean up excessive newlines
    lines = [line.rstrip() for line in description.split('\n')]
    return '\n'.join(lines).strip()


def extract_priority(fields: List[Dict]) -> str:
    """Extract priority value from task fields."""
    for field in fields:
        if field.get('name') == 'Priority' or field.get('fieldTemplateId') in [
            'e5b1cb21-c337-4511-903b-861ed1cc9ae5',
            'b88e01b3-3028-47f1-8076-e6967fc31710'
        ]:
            label = field.get('label') or field.get('selectValue')
            if label:
                return label.get('value', '')
    return ""


def transform_task(task: Dict, mappings: Dict, use_height_ids: bool = False) -> Dict[str, str]:
    """Transform a Height task to Linear CSV row format."""

    # Get team names
    team_names = [mappings['teams'].get(team_id, '') for team_id in task.get('teamIds', [])]
    team = team_names[0] if team_names else ""

    # Get creator email
    creator_id = task.get('createdUserId', '')
    creator = mappings['users'].get(creator_id, '')

    # Get assignee emails
    assignee_ids = task.get('assigneesIds', [])
    assignee = mappings['users'].get(assignee_ids[0], '') if assignee_ids else ""

    # Get parent task reference
    parent_task_id = task.get('parentTaskId')
    parent_issue = mappings['task_ids'].get(parent_task_id, '') if parent_task_id else ""

    # Extract priority
    priority = extract_priority(task.get('fields', []))

    # Map status
    status = STATUS_MAP.get(task.get('status', ''), task.get('status', ''))

    # Fix status if task has completedAt date (Linear requirement)
    # If a task has a completion date, it must be in "Done" status
    if task.get('completedAt'):
        status = "Done"

    # Get title (no truncation)
    title = task.get('name', '')

    # Clean and enhance description
    description = clean_description(task.get('description', ''))
    height_id = f"T-{task['index']}"

    # Add Height ID reference to description
    if description:
        description = f"[Imported from Height: {height_id}]\n\n{description}"
    else:
        description = f"[Imported from Height: {height_id}]"

    # Decide whether to use Height IDs or let Linear auto-generate
    issue_id = height_id if use_height_ids else ""

    # Fix completion date if it's before creation date
    completed_at = task.get('completedAt')
    created_at = task.get('createdAt')

    if completed_at and created_at:
        try:
            from datetime import datetime
            completed_dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

            # If completion is before creation, use the updated date instead
            if completed_dt < created_dt:
                completed_at = task.get('lastActivityAt', completed_at)
        except (ValueError, AttributeError):
            pass

    # Build the row
    return {
        "ID": issue_id,
        "Team": team,
        "Title": title,
        "Description": description,
        "Status": status,
        "Estimate": "",
        "Priority": priority,
        "Project ID": "",
        "Project": "",
        "Creator": creator,
        "Assignee": assignee,
        "Labels": "",
        "Cycle Number": "",
        "Cycle Name": "",
        "Cycle Start": "",
        "Cycle End": "",
        "Created": convert_iso_to_linear_date(task.get('createdAt')),
        "Updated": convert_iso_to_linear_date(task.get('lastActivityAt')),
        "Started": convert_iso_to_linear_date(task.get('startedAt')),
        "Triaged": "",
        "Completed": convert_iso_to_linear_date(completed_at),
        "Canceled": "",
        "Archived": "",
        "Due Date": "",
        "Parent issue": parent_issue,
        "Initiatives": "",
        "Project Milestone ID": "",
        "Project Milestone": "",
        "SLA Status": "",
        "Roadmaps": ""
    }


def generate_parent_mapping(tasks: List[Dict], mappings: Dict) -> Dict[str, str]:
    """Generate a mapping of Height task IDs to their parent IDs."""
    parent_map = {}
    for task in tasks:
        height_id = f"T-{task['index']}"
        parent_task_id = task.get('parentTaskId')
        if parent_task_id:
            parent_height_id = mappings['task_ids'].get(parent_task_id, '')
            if parent_height_id:
                parent_map[height_id] = parent_height_id
    return parent_map


def main():
    parser = argparse.ArgumentParser(
        description="Transform Height JSON export to Linear CSV import format"
    )
    parser.add_argument(
        '--input-dir',
        type=Path,
        default=Path('export-2025-09-29-FevGPS'),
        help='Path to Height export directory (default: export-2025-09-29-FevGPS)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('linear_import.csv'),
        help='Output CSV file path (default: linear_import.csv)'
    )
    parser.add_argument(
        '--use-height-ids',
        action='store_true',
        help='Use Height IDs (T-XXX) in the ID column (experimental - test with small subset first)'
    )
    parser.add_argument(
        '--generate-both',
        action='store_true',
        help='Generate both CSV formats: one with empty IDs and one with Height IDs'
    )

    args = parser.parse_args()

    # Load JSON files
    print(f"Loading data from {args.input_dir}...")
    tasks = load_json_file(args.input_dir / 'tasks.json')
    teams = load_json_file(args.input_dir / 'teams.json')
    users = load_json_file(args.input_dir / 'users.json')

    print(f"Loaded {len(tasks)} tasks, {len(teams)} teams, {len(users)} users")

    # Build mappings
    print("Building ID mappings...")
    mappings = build_mappings(tasks, teams, users)

    # Generate parent mapping JSON
    parent_mapping = generate_parent_mapping(tasks, mappings)
    mapping_file = args.output.parent / 'parent_mapping.json'
    print(f"Writing parent mapping to {mapping_file}...")
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(parent_mapping, f, indent=2)
    print(f"✓ Created parent mapping with {len(parent_mapping)} relationships")

    # Decide which CSV formats to generate
    formats_to_generate = []
    if args.generate_both:
        formats_to_generate = [
            (args.output, False),
            (args.output.parent / f"{args.output.stem}_with_ids{args.output.suffix}", True)
        ]
    else:
        formats_to_generate = [(args.output, args.use_height_ids)]

    # Generate CSV files
    for output_path, use_ids in formats_to_generate:
        print(f"\nTransforming tasks {'with' if use_ids else 'without'} Height IDs...")
        rows = [transform_task(task, mappings, use_ids) for task in tasks]

        print(f"Writing to {output_path}...")
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=LINEAR_HEADERS, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(rows)

        print(f"✓ Successfully created {output_path} with {len(rows)} tasks")

    # Print usage notes
    print("\n" + "="*70)
    if args.generate_both or not args.use_height_ids:
        print("📄 Standard CSV (empty IDs):")
        print(f"   {args.output}")
        print("   → Use for two-pass import (safest option)")
        print("   → Linear will auto-generate IDs")
        print("   → Use parent_mapping.json to update relationships after import")

    if args.generate_both or args.use_height_ids:
        output_with_ids = args.output.parent / f"{args.output.stem}_with_ids{args.output.suffix}" if args.generate_both else args.output
        print(f"\n📄 CSV with Height IDs:")
        print(f"   {output_with_ids}")
        print("   → EXPERIMENTAL: Test with small subset first")
        print("   → If Linear accepts custom IDs, parent relationships will work automatically")
        print("   → If Linear rejects/ignores IDs, use standard CSV instead")

    print(f"\n📋 Parent mapping JSON:")
    print(f"   {mapping_file}")
    print(f"   → {len(parent_mapping)} parent-child relationships")
    print("   → Use for post-import API updates or manual reference")
    print("="*70)


if __name__ == '__main__':
    main()