"""
Generic script to update task notebooks with validated data and step images.

This script:
1. Reads a task notebook from Input Data/task_<folder>/
2. Creates <filename>_updated.ipynb in the same folder (non-destructive)
3. Loads validated observations and thoughts from validated_observation_thought.json in task folder
4. Adds step images below step headers in new cells
5. Replaces existing observations and thoughts with validated content
6. Adds action cells with commands from pg_commands.txt in task folder
"""

import json
import os
import sys
import re
import base64
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


def load_actions(actions_path):
    """Load action commands from pyautogui_actions text file."""
    if not actions_path.exists():
        return []
    
    with open(actions_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Remove empty lines and strip whitespace
    actions = [line.strip() for line in lines if line.strip()]
    return actions


def get_step_number(cell_content):
    """Extract step number from markdown cell content."""
    # Match patterns like "## Step 1", "## Step 2", etc.
    match = re.search(r'^##\s+Step\s+(\d+)', cell_content.strip(), re.MULTILINE)
    if match:
        return int(match.group(1))
    return None


def create_image_cell(image_path):
    """Create a markdown cell with an embedded image using base64 encoding."""
    # Read the image file and encode it as base64
    try:
        with open(image_path, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Create markdown with embedded base64 image
        img_markdown = f"![Step Image](data:image/png;base64,{img_data})"
        
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                img_markdown
            ]
        }
    except Exception as e:
        print(f"Warning: Could not encode image {image_path}: {e}")
        # Fallback to file reference if encoding fails
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


def clean_thought_content(thought_text):
    """Remove any embedded ### Action section from thought text."""
    # Split by ### Action and take only the part before it
    if '### Action' in thought_text:
        thought_text = thought_text.split('### Action')[0].strip()
    return thought_text


def update_notebook(notebook_path, validated_json_path, screenshots_dir, actions_path=None, output_path=None):
    """
    Update a task notebook with validated data and step images.
    
    Args:
        notebook_path: Path to the notebook file (.ipynb)
        validated_json_path: Path to the validated JSON file
        screenshots_dir: Path to the directory containing step screenshots
        actions_path: Path to the pyautogui_actions text file (optional)
        output_path: Path to save the updated notebook (optional, defaults to notebook_path)
    """
    # Load data
    notebook = load_notebook(notebook_path)
    validated_data = load_validated_data(validated_json_path)
    
    # Load actions if provided
    actions = []
    if actions_path:
        actions = load_actions(actions_path)
    
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
                # Remove any embedded images from the step header cell
                clean_header = re.sub(r'!\[.*?\]\(.*?\)', '', cell_content).strip()
                cell['source'] = [clean_header]
                
                # Add the step header cell
                new_cells.append(cell)
                i += 1
                
                # Check if next cell is already an image - if so, replace it
                image_filename = f"{step_num}.png"
                image_path = screenshots_folder / image_filename
                
                # Check if the next cell is an existing image cell
                has_existing_image = False
                if i < len(cells) and cells[i]['cell_type'] == 'markdown':
                    next_content = ''.join(cells[i]['source']) if isinstance(cells[i]['source'], list) else cells[i]['source']
                    if next_content.strip().startswith('![Step Image]'):
                        has_existing_image = True
                        i += 1  # Skip the old image cell
                
                # Add image cell (either new or replacement) with absolute path for encoding
                if image_path.exists():
                    new_cells.append(create_image_cell(image_path))
                
                # Get validated data for this step
                step_key = f"step_{step_num}"
                if step_key in validated_data:
                    observation = validated_data[step_key].get('observation', '')
                    thought = validated_data[step_key].get('thought', '')
                    
                    # Clean thought content to remove any embedded action sections
                    thought = clean_thought_content(thought)
                    
                    # Find and preserve original action cell
                    original_action_cell = None
                    temp_i = i
                    
                    while temp_i < len(cells):
                        temp_cell = cells[temp_i]
                        if temp_cell['cell_type'] == 'markdown':
                            temp_content = ''.join(temp_cell['source']) if isinstance(temp_cell['source'], list) else temp_cell['source']
                            
                            # Check if it's the next step header - stop searching
                            if get_step_number(temp_content) is not None:
                                break
                            
                            # Check if this cell contains ### Action header
                            if "### Action" in temp_content:
                                original_action_cell = temp_cell
                                break
                        
                        temp_i += 1
                    
                    # Skip all cells until we find the next step header
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
                        new_cells.append(create_markdown_cell(f"### Observation\n\n{observation}"))
                    
                    if thought:
                        new_cells.append(create_markdown_cell(f"### Thought\n\n{thought}"))
                    
                    # Add original action cell as-is
                    if original_action_cell:
                        new_cells.append(original_action_cell)
                    
                    # Add code cell with command if available
                    if actions and step_num <= len(actions):
                        action_command = actions[step_num - 1]  # step_num is 1-indexed
                        new_cells.append(create_markdown_cell("### Code"))
                        new_cells.append(create_markdown_cell(action_command))
                    
                    continue
        
        # Add cell as-is if not a step header
        new_cells.append(cell)
        i += 1
    # Update notebook with new cells
    notebook['cells'] = new_cells
    
    # Save updated notebook to output path or original path
    save_path = output_path if output_path else notebook_path
    save_notebook(save_path, notebook)
    print(f"✓ Successfully updated {save_path}")


def main():
    """Main function to run the script."""
    if len(sys.argv) < 2:
        print("Usage: python update_notebook.py <folder_name>")
        print("Example: python update_notebook.py task_645")
        sys.exit(1)
    
    folder_name = sys.argv[1]
    
    # Extract task number from folder name (e.g., "task_645" -> "645")
    task_num = folder_name.replace('task_', '') if folder_name.startswith('task_') else folder_name
    
    # Define paths based on modular structure (script is in Local Scripts folder)
    base_dir = Path(__file__).parent.parent  # Go up to project root
    task_folder = base_dir / "Input Data" / folder_name
    
    # Find .ipynb file in the folder
    ipynb_files = list(task_folder.glob("*.ipynb"))
    if not ipynb_files:
        print(f"Error: No .ipynb file found in folder '{task_folder}'")
        sys.exit(1)
    if len(ipynb_files) > 1:
        print(f"Warning: Multiple .ipynb files found in '{task_folder}'. Using first one: {ipynb_files[0].name}")
    
    notebook_path = ipynb_files[0]
    output_notebook_path = task_folder / f"{notebook_path.stem}_updated.ipynb"
    
    # Resource paths - all inside the task folder
    validated_json_path = task_folder / "validated_observation_thought.json"
    screenshots_dir = task_folder / "screenshots"
    actions_path = task_folder / "pg_commands.txt"
    
    # Validate required paths
    if not validated_json_path.exists():
        print(f"✗ Error: Validated JSON not found at {validated_json_path}")
        sys.exit(1)
    
    if not screenshots_dir.exists():
        print(f"✗ Warning: Screenshots directory not found at {screenshots_dir}")
        print("  Continuing without images...")
    
    if not actions_path.exists():
        print(f"✗ Warning: Actions file not found at {actions_path}")
        print("  Continuing without action commands...")
        actions_path = None
    
    # Update the notebook
    print(f"Updating notebook for task {task_num}...")
    print(f"  Input notebook: {notebook_path}")
    print(f"  Output notebook: {output_notebook_path}")
    print(f"  Validated data: {validated_json_path}")
    print(f"  Screenshots: {screenshots_dir}")
    if actions_path:
        print(f"  Actions: {actions_path}")
    print()
    
    # Update notebook (reads from notebook_path, saves to output_notebook_path)
    update_notebook(notebook_path, validated_json_path, screenshots_dir, actions_path, output_notebook_path)
    
    print()
    print(f"✓ Update complete! Created: {output_notebook_path}")


if __name__ == "__main__":
    main()
