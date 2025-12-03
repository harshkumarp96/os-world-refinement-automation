"""
Generic script to update task notebooks with validated data and step images.

This script:
1. Reads a task notebook (.ipynb file)
2. Loads validated observations and thoughts from JSON
3. Adds step images below step headers
4. Replaces existing observations and thoughts with validated content
"""

import json
import os
import sys
import re
from pathlib import Path


def load_notebook(notebook_path):
    """Load a Jupyter notebook file."""
    with open(notebook_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_notebook(notebook_path, notebook_data):
    """Save a Jupyter notebook file."""
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook_data, f, indent=1, ensure_ascii=False)


def load_validated_data(json_path):
    """Load validated observation and thought data from JSON."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_step_number(cell_content):
    """Extract step number from markdown cell content."""
    # Match patterns like "## Step 1", "## Step 2", etc.
    match = re.search(r'^##\s+Step\s+(\d+)', cell_content.strip(), re.MULTILINE)
    if match:
        return int(match.group(1))
    return None


def create_image_cell(image_path):
    """Create a markdown cell with an embedded image."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            f"![Step Image]({image_path})"
        ]
    }


def create_markdown_cell(content):
    """Create a markdown cell with the given content."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            content
        ]
    }


def update_notebook(notebook_path, validated_json_path, screenshots_dir):
    """
    Update a task notebook with validated data and step images.
    
    Args:
        notebook_path: Path to the notebook file (.ipynb)
        validated_json_path: Path to the validated JSON file
        screenshots_dir: Path to the directory containing step screenshots
    """
    # Load data
    notebook = load_notebook(notebook_path)
    validated_data = load_validated_data(validated_json_path)
    
    # Get task name from paths for flexibility
    task_name = Path(notebook_path).stem
    screenshots_folder = Path(screenshots_dir)
    
    # Process cells
    new_cells = []
    i = 0
    cells = notebook['cells']
    
    while i < len(cells):
        cell = cells[i]
        
        # Check if this is a step header cell
        if cell['cell_type'] == 'markdown':
            cell_content = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']
            step_num = get_step_number(cell_content)
            
            if step_num is not None:
                # Add the step header cell
                new_cells.append(cell)
                
                # Add image cell right after step header
                image_filename = f"{step_num}.png"
                image_path = screenshots_folder / image_filename
                
                if image_path.exists():
                    # Use relative path for the image
                    relative_image_path = f"../Screenshots/{screenshots_folder.name}/{image_filename}"
                    new_cells.append(create_image_cell(relative_image_path))
                
                # Get validated data for this step
                step_key = f"step_{step_num}"
                if step_key in validated_data:
                    observation = validated_data[step_key].get('observation', '')
                    thought = validated_data[step_key].get('thought', '')
                    
                    # Skip all cells until we find the next step header
                    i += 1
                    while i < len(cells):
                        next_cell = cells[i]
                        if next_cell['cell_type'] == 'markdown':
                            next_content = ''.join(next_cell['source']) if isinstance(next_cell['source'], list) else next_cell['source']
                            
                            # Check if it's the next step header - if so, stop skipping
                            if get_step_number(next_content) is not None:
                                break
                        
                        # Skip this cell (it's part of the old step content)
                        i += 1
                    
                    # Add new observation and thought cells if they have content
                    if observation:
                        new_cells.append(create_markdown_cell("### Observation"))
                        new_cells.append(create_markdown_cell(observation))
                    
                    if thought:
                        new_cells.append(create_markdown_cell("### Thought"))
                        new_cells.append(create_markdown_cell(thought))
                    
                    continue
        
        # Add cell as-is if not a step header
        new_cells.append(cell)
        i += 1
    
    # Update notebook with new cells
    notebook['cells'] = new_cells
    
    # Save updated notebook
    save_notebook(notebook_path, notebook)
    print(f"✓ Successfully updated {notebook_path}")


def main():
    """Main function to run the script."""
    if len(sys.argv) < 2:
        print("Usage: python update_notebook.py <task_number>")
        print("Example: python update_notebook.py 77")
        sys.exit(1)
    
    task_num = sys.argv[1]
    
    # Define paths based on project structure
    base_dir = Path(__file__).parent
    notebook_path = base_dir / "Input Data" / "colab_notebook" / f"task_{task_num}.ipynb"
    validated_json_path = base_dir / "output" / f"task_{task_num}_validated.json"
    screenshots_dir = base_dir / "Input Data" / "Screenshots" / f"task_{task_num}"
    
    # Validate paths
    if not notebook_path.exists():
        print(f"✗ Error: Notebook not found at {notebook_path}")
        sys.exit(1)
    
    if not validated_json_path.exists():
        print(f"✗ Error: Validated JSON not found at {validated_json_path}")
        sys.exit(1)
    
    if not screenshots_dir.exists():
        print(f"✗ Warning: Screenshots directory not found at {screenshots_dir}")
        print("  Continuing without images...")
    
    # Update the notebook
    print(f"Updating notebook for task {task_num}...")
    print(f"  Notebook: {notebook_path}")
    print(f"  Validated data: {validated_json_path}")
    print(f"  Screenshots: {screenshots_dir}")
    print()
    
    update_notebook(notebook_path, validated_json_path, screenshots_dir)
    print()
    print("✓ Update complete!")


if __name__ == "__main__":
    main()
