# Task Processing Pipeline - Usage Guide

## Quick Start

Process any task with a single command:

```bash
python process_task.py <task_folder>
```

**Example:**
```bash
python process_task.py task_645
```

## What It Does

The script automatically runs the complete processing pipeline:

1. **Convert JSON to PyAutoGUI** - Converts `events.json` to PyAutoGUI commands
2. **Generate Observations/Thoughts** - Extracts from notebook to JSON
3. **Validate with AI** - Uses Claude to validate and improve observations/thoughts
4. **Update Notebook** - Creates `task_XXX_updated.ipynb` with validated data
5. **Verify Structure** - Checks for consistency and completeness

## Prerequisites

The script handles these automatically:
- Creates virtual environment if needed
- Installs requirements if needed
- Just run the script and it takes care of everything

## Input Structure

Your task folder should contain:
```
Input Data/
  task_645/
    ├── task_645.ipynb          # Original notebook
    ├── events.json             # Event data
    ├── screenshots/            # Step screenshots
    │   ├── 1.png
    │   ├── 2.png
    │   └── ...
```

## Output

After completion, you'll find:
```
Input Data/
  task_645/
    ├── pg_commands.txt                      # PyAutoGUI commands
    ├── observation_thought.json             # Extracted data
    ├── validated_observation_thought.json   # AI-validated data
    ├── validation_report.json               # Detailed report
    └── task_645_updated.ipynb              # Final notebook ✓
```

## Environment Variables

Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Troubleshooting

- **Script fails immediately**: Check that task folder exists in `Input Data/`
- **Validation errors**: Ensure `.env` has valid ANTHROPIC_API_KEY
- **Missing screenshots**: Script continues without images (warning shown)
- **Verification warnings**: Normal if original notebook structure varies

## Notes

- Non-destructive: Creates new `_updated.ipynb` file
- Each step logs progress with clear ✓ or ✗ indicators
- Failed steps exit immediately with error message
