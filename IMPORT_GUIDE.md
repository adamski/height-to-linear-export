# Linear Import Guide - Complete Workflow

Step-by-step guide for importing Height tasks into Linear with parent-child relationships.

## Prerequisites

1. **Linear Account** with appropriate permissions
2. **Python 3.7+** installed
3. **Linear API Key** (we'll get this in Step 3)

---

## Step 1: Generate Import Files

Run the transformation script to create your import files:

```bash
python3 height_to_linear.py
```

This creates:
- ✅ `linear_import.csv` (782 tasks)
- ✅ `parent_mapping.json` (648 relationships)

---

## Step 2: Import CSV into Linear

### Option A: Using Linear CLI Importer (Recommended)

1. **Install Node.js** (if not already installed):
   ```bash
   # macOS
   brew install node

   # Or download from https://nodejs.org/
   ```

2. **Install Linear CLI importer**:
   ```bash
   npm install -g @linear/import
   ```

3. **Run the importer**:
   ```bash
   linear-import csv
   ```

4. **Follow the prompts**:
   - Select your Linear workspace
   - Choose "Linear CSV" format when prompted
   - Select `linear_import.csv` as your file
   - Map the fields (should auto-detect)
   - Confirm the import

5. **Wait for completion**:
   - The CLI will show progress
   - Note any errors or warnings
   - Linear will assign new IDs (e.g., `NODE-1`, `NODE-2`, etc.)

### Option B: Using Linear Web UI

1. Go to **Linear Settings** → **Import & Export**
2. Click **Import Issues**
3. Select **CSV** as the source
4. Upload `linear_import.csv`
5. Map the fields (should auto-detect)
6. Review and confirm import
7. Wait for completion

---

## Step 3: Get Your Linear API Key

1. Go to **Linear Settings** → **API**
2. Under **Personal API keys**, click **Create key**
3. Give it a name (e.g., "Height Import Parent Updater")
4. Copy the generated key (starts with `lin_api_...`)
5. **Important**: Save it securely - you won't see it again!

---

## Step 4: Install Python Dependencies

Install the required Python package:

```bash
pip install requests
```

Or if using Python 3 specifically:

```bash
pip3 install requests
```

---

## Step 5: Update Parent-Child Relationships

Now we'll use the API script to set up the parent-child relationships.

### Set up your API key

```bash
# macOS/Linux
export LINEAR_API_KEY="lin_api_YOUR_KEY_HERE"

# Windows (Command Prompt)
set LINEAR_API_KEY=lin_api_YOUR_KEY_HERE

# Windows (PowerShell)
$env:LINEAR_API_KEY="lin_api_YOUR_KEY_HERE"
```

### Run the parent relationship updater

```bash
python3 update_parent_relationships.py
```

### Follow the prompts

```
Filter by team key? (e.g., 'NODE', or press Enter to skip):
```

- If all your tasks are in one team (e.g., "Node Audio"), enter the team key (e.g., `NODE`)
- If tasks span multiple teams, press Enter to process all

The script will:
1. ✅ Fetch all issues from Linear
2. ✅ Extract Height IDs from descriptions
3. ✅ Match parent relationships
4. ✅ Show you what will be updated
5. ⚠️ Ask for confirmation before making changes

**Example output:**
```
======================================================================
Updates needed: 648
======================================================================

Sample updates (first 5):
  NODE-423 (T-423) → parent: NODE-224 (T-224)
  NODE-176 (T-176) → parent: NODE-1 (T-1)
  NODE-450 (T-450) → parent: NODE-224 (T-224)
  NODE-328 (T-328) → parent: NODE-224 (T-224)
  NODE-532 (T-532) → parent: NODE-531 (T-531)

This will update 648 issues.
Proceed with updates? (yes/no):
```

### Confirm and wait

Type `yes` and press Enter. The script will:
- Update all parent-child relationships
- Show progress for each update
- Display a summary when complete

---

## Step 6: Verify the Import

### In Linear UI

1. Go to your Linear workspace
2. Check a few issues that should have parents
3. Verify the parent-child relationships are correct
4. Check that Height IDs are preserved in descriptions (e.g., `[Imported from Height: T-423]`)

### Using the API script (optional)

Run the script again to verify:

```bash
python3 update_parent_relationships.py
```

If everything is correct, you should see:
```
✓ All parent-child relationships are already set correctly!
```

---

## Troubleshooting

### Issue: "LINEAR_API_KEY environment variable not set"

**Solution:** Make sure you've exported your API key (see Step 5)

### Issue: "No issues found with Height ID tags"

**Possible causes:**
1. Import hasn't completed yet - wait a few minutes
2. Wrong team filter - try without team filter
3. CSV import failed - check Linear UI for import status

**Solution:** Verify issues exist in Linear and have descriptions with `[Imported from Height: T-XXX]`

### Issue: "Parent T-XXX not found for T-YYY"

**This is expected** if:
- Parent task wasn't imported (filtered out)
- Parent task failed to import (check import logs)

**Solution:** Either import the missing parent or manually remove the relationship

### Issue: API rate limiting

**Solution:** The script processes updates one at a time. If you hit rate limits:
1. Wait a few minutes
2. Run the script again - it will skip already-updated relationships

### Issue: Some updates failing

Check Linear UI for those specific issues:
- Issue might be locked
- Circular dependency detected
- Permissions issue

---

## Advanced: Filtering Tasks Before Import

If you want to import only specific tasks, filter the CSV before importing:

```bash
# Example: Import only Node Audio team tasks
python3 -c "
import csv
with open('linear_import.csv') as fin:
    reader = csv.DictReader(fin)
    rows = [r for r in reader if r['Team'] == 'Node Audio']

with open('linear_import_filtered.csv', 'w', newline='') as fout:
    writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f'Filtered to {len(rows)} tasks')
"
```

Then import `linear_import_filtered.csv` instead.

---

## Complete Command Reference

```bash
# Step 1: Generate files
python3 height_to_linear.py

# Step 2: Install Linear CLI
npm install -g @linear/import

# Step 2: Import CSV
linear-import csv

# Step 4: Install Python dependencies
pip install requests

# Step 5: Set API key
export LINEAR_API_KEY="lin_api_YOUR_KEY_HERE"

# Step 5: Update parent relationships
python3 update_parent_relationships.py

# Verify
python3 update_parent_relationships.py  # Should show "already set correctly"
```

---

## What Gets Imported

✅ **Imported and Preserved:**
- Title
- Description (with Height ID reference)
- Team
- Status (mapped: Backlog, Closed, etc.)
- Priority
- Creator email
- Assignee email
- Created date
- Updated date
- Started date
- Completed date
- Parent-child relationships (after Step 5)

❌ **Not Imported:**
- Comments
- Attachments
- Activity history
- Custom fields (except Priority)
- Watchers/subscribers

---

## Support

- **Linear Import Docs**: https://linear.app/docs/import-issues
- **Linear API Docs**: https://developers.linear.app/docs
- **Linear CLI**: https://github.com/linear/linear/tree/master/packages/import

For issues with this script, check:
1. All files are in the same directory
2. API key is correctly set
3. You have permissions in Linear workspace