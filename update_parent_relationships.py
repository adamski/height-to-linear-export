#!/usr/bin/env python3
"""
Update Linear parent-child relationships after importing from Height.

This script:
1. Fetches all issues from Linear (filtered by team/project if needed)
2. Extracts Height IDs from issue descriptions
3. Matches parent relationships from parent_mapping.json
4. Updates parent-child relationships via Linear API

Requirements:
    pip install requests

Usage:
    python3 update_parent_relationships.py
"""

import getpass
import json
import os
import re
import sys
from typing import Dict, List, Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("Error: 'requests' module not found.")
    print("Install it with: pip install requests")
    sys.exit(1)


LINEAR_API_URL = "https://api.linear.app/graphql"


class LinearClient:
    """Simple Linear API client using requests."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

    def query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            LINEAR_API_URL,
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")

        return data.get("data", {})

    def get_all_issues(self, team_key: Optional[str] = None) -> List[Dict]:
        """Fetch all issues, optionally filtered by team."""
        issues = []
        has_next_page = True
        cursor = None

        # Build filter
        filter_clause = ""
        if team_key:
            filter_clause = f'filter: {{ team: {{ key: {{ eq: "{team_key}" }} }} }}'

        while has_next_page:
            after_clause = f', after: "{cursor}"' if cursor else ""

            query = f"""
            query {{
                issues({filter_clause}, first: 100{after_clause}) {{
                    nodes {{
                        id
                        identifier
                        title
                        description
                        parent {{
                            id
                            identifier
                        }}
                    }}
                    pageInfo {{
                        hasNextPage
                        endCursor
                    }}
                }}
            }}
            """

            result = self.query(query)
            issues_data = result.get("issues", {})
            issues.extend(issues_data.get("nodes", []))

            page_info = issues_data.get("pageInfo", {})
            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")

        return issues

    def update_issue_parent(self, issue_id: str, parent_id: str) -> Dict:
        """Update an issue's parent."""
        mutation = """
        mutation UpdateIssue($issueId: String!, $parentId: String!) {
            issueUpdate(
                id: $issueId,
                input: { parentId: $parentId }
            ) {
                success
                issue {
                    id
                    identifier
                    parent {
                        identifier
                    }
                }
            }
        }
        """

        variables = {
            "issueId": issue_id,
            "parentId": parent_id
        }

        return self.query(mutation, variables)


def extract_height_id(description: str) -> Optional[str]:
    """Extract Height ID from issue description."""
    if not description:
        return None

    match = re.search(r'\\?\[Imported from Height: (T-\d+)\\?\]', description)
    if match:
        return match.group(1)

    return None


def build_height_to_linear_mapping(issues: List[Dict]) -> Dict[str, Dict]:
    """Build mapping of Height IDs to Linear issue data."""
    mapping = {}

    for issue in issues:
        height_id = extract_height_id(issue.get("description", ""))
        if height_id:
            mapping[height_id] = {
                "linear_id": issue["id"],
                "linear_identifier": issue["identifier"],
                "title": issue["title"],
                "current_parent": issue.get("parent")
            }

    return mapping


def load_parent_mapping(file_path: str = "parent_mapping.json") -> Dict[str, str]:
    """Load parent mapping from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        print("Make sure you've run height_to_linear.py first to generate this file.")
        sys.exit(1)


def main():
    print("="*70)
    print("Linear Parent-Child Relationship Updater")
    print("="*70)

    # Get API key interactively
    print("\nLinear API Key required.")
    print("Get your API key from: Linear Settings > API > Personal API keys")
    api_key = getpass.getpass("Enter your Linear API key: ").strip()
    if not api_key:
        print("Error: API key is required.")
        sys.exit(1)

    # Optional: filter by team
    team_key = input("\nFilter by team key? (e.g., 'NODE', or press Enter to skip): ").strip()
    if not team_key:
        team_key = None

    # Initialize client
    print("\nInitializing Linear API client...")
    client = LinearClient(api_key)

    # Fetch all issues
    print(f"Fetching issues from Linear{f' (team: {team_key})' if team_key else ''}...")
    issues = client.get_all_issues(team_key)
    print(f"✓ Found {len(issues)} issues")

    # Build Height -> Linear mapping
    print("\nBuilding Height ID to Linear ID mapping...")
    height_to_linear = build_height_to_linear_mapping(issues)
    print(f"✓ Found {len(height_to_linear)} issues with Height IDs")

    if not height_to_linear:
        print("\nWarning: No issues found with Height ID tags in their descriptions.")
        print("Make sure you've imported the CSV generated by height_to_linear.py")
        sys.exit(1)

    # Load parent mapping
    print("\nLoading parent mapping from parent_mapping.json...")
    height_parents = load_parent_mapping()
    print(f"✓ Loaded {len(height_parents)} parent-child relationships")

    # Calculate updates needed
    updates_needed = []
    for child_height_id, parent_height_id in height_parents.items():
        if child_height_id not in height_to_linear:
            continue

        if parent_height_id not in height_to_linear:
            print(f"⚠ Warning: Parent {parent_height_id} not found for {child_height_id}")
            continue

        child_data = height_to_linear[child_height_id]
        parent_data = height_to_linear[parent_height_id]

        # Check if already set correctly
        current_parent = child_data.get("current_parent")
        if current_parent and current_parent.get("id") == parent_data["linear_id"]:
            continue  # Already set correctly

        updates_needed.append({
            "child_height_id": child_height_id,
            "parent_height_id": parent_height_id,
            "child_linear_id": child_data["linear_id"],
            "parent_linear_id": parent_data["linear_id"],
            "child_identifier": child_data["linear_identifier"],
            "parent_identifier": parent_data["linear_identifier"],
            "child_title": child_data["title"]
        })

    print(f"\n{'='*70}")
    print(f"Updates needed: {len(updates_needed)}")
    print(f"{'='*70}")

    if not updates_needed:
        print("\n✓ All parent-child relationships are already set correctly!")
        return

    # Show sample updates
    print("\nSample updates (first 5):")
    for update in updates_needed[:5]:
        print(f"  {update['child_identifier']} ({update['child_height_id']}) → parent: {update['parent_identifier']} ({update['parent_height_id']})")

    # Confirm before proceeding
    print(f"\nThis will update {len(updates_needed)} issues.")
    confirm = input("Proceed with updates? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("Aborted.")
        return

    # Perform updates
    print("\nUpdating parent relationships...")
    success_count = 0
    error_count = 0

    for i, update in enumerate(updates_needed, 1):
        try:
            result = client.update_issue_parent(
                update["child_linear_id"],
                update["parent_linear_id"]
            )

            if result.get("issueUpdate", {}).get("success"):
                success_count += 1
                print(f"  [{i}/{len(updates_needed)}] ✓ {update['child_identifier']} → {update['parent_identifier']}")
            else:
                error_count += 1
                print(f"  [{i}/{len(updates_needed)}] ✗ Failed: {update['child_identifier']}")

        except Exception as e:
            error_count += 1
            print(f"  [{i}/{len(updates_needed)}] ✗ Error: {update['child_identifier']}: {e}")

    # Summary
    print(f"\n{'='*70}")
    print("Summary:")
    print(f"  ✓ Successful updates: {success_count}")
    print(f"  ✗ Failed updates: {error_count}")
    print(f"  Total: {len(updates_needed)}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()