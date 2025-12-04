#!/usr/bin/env python3
"""
Comprehensive script to parse task notebooks and generate JSON files.

Usage:
    python "Local Scripts\generate_observations_thoughts.py" task_<number>
    
Example:
    python "Local Scripts\generate_observations_thoughts.py" task_645
    
Input: Input Data/task_<number>/task_<number>.ipynb
Output: Input Data/task_<number>/observation_thought.json
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def parse_notebook_to_json(notebook_path: str) -> Dict[str, Any]:
    """
    Parse a Jupyter notebook file and convert it to the task JSON format.
    
    Args:
        notebook_path: Path to the input notebook file
        
    Returns:
        Dictionary containing the parsed task data
    """
    # Load the notebook JSON
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    task_data = {}
    current_step = None
    current_section = None
    
    # Process each cell in the notebook
    for cell in notebook.get('cells', []):
        if cell.get('cell_type') != 'markdown':
            continue
        
        # Get cell content as string
        cell_text = ''.join(cell.get('source', [])).strip()
        
        if not cell_text:
            continue
        
        # Check if this is a step header (e.g., "## Step 1")
        # Allow additional content after the step header (like images)
        step_match = re.match(r'^##\s+Step\s+(\d+)', cell_text, re.IGNORECASE)
        if step_match:
            step_num = int(step_match.group(1))
            current_step = f"step_{step_num}"
            # Initialize step with empty strings if it doesn't exist
            if current_step not in task_data:
                task_data[current_step] = {
                    "observation": "",
                    "thought": ""
                }
            current_section = None
            continue
        
        # Check if this is a section header (### Observation, ### Thought, ### Action)
        # Allow content after the header in the same cell
        section_match = re.match(r'^###\s+(Observation|Thought|Action)', cell_text, re.IGNORECASE)
        if section_match:
            current_section = section_match.group(1).lower()
            
            # Extract content after the header if present in the same cell
            lines = cell_text.split('\n', 1)  # Split on first newline only
            if len(lines) > 1:
                content = lines[1].strip()
                if current_step and current_section in ['observation', 'thought'] and content:
                    task_data[current_step][current_section] = content
            continue
        
        # Check if section header and content are in the same cell
        combined_match = re.match(r'^###\s+(Observation|Thought)\s*\n\n(.+)', cell_text, re.IGNORECASE | re.DOTALL)
        if combined_match:
            current_section = combined_match.group(1).lower()
            content = combined_match.group(2).strip()
            if current_step and current_section in ['observation', 'thought'] and content:
                task_data[current_step][current_section] = content
            continue
        
        # If we're in a section and this is content (continuation cell or standalone content)
        if current_step and current_section in ['observation', 'thought']:
            # This is content for the current section
            if task_data[current_step][current_section]:
                # Append to existing content
                task_data[current_step][current_section] += "\n\n" + cell_text
            else:
                # Set as new content
                task_data[current_step][current_section] = cell_text
    
    return task_data


def save_json(data: Dict[str, Any], output_path: str) -> None:
    """Save the parsed data to a JSON file."""
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON file with proper formatting
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def validate_output(data: Dict[str, Any], notebook_path: str) -> Dict[str, Any]:
    """
    Validate the generated JSON data.
    
    Returns:
        Dictionary with validation results
    """
    validation = {
        'total_steps': len(data),
        'empty_observations': 0,
        'empty_thoughts': 0,
        'steps_with_content': 0,
        'empty_steps': [],
        'valid': True
    }
    
    for step_key, step_data in data.items():
        has_obs = bool(step_data.get('observation', '').strip())
        has_thought = bool(step_data.get('thought', '').strip())
        
        if not has_obs:
            validation['empty_observations'] += 1
        if not has_thought:
            validation['empty_thoughts'] += 1
        
        if has_obs or has_thought:
            validation['steps_with_content'] += 1
        else:
            validation['empty_steps'].append(step_key)
    
    return validation


def print_validation_report(validation: Dict[str, Any], output_path: str) -> None:
    """Print a formatted validation report."""
    print("\n" + "="*70)
    print("  VALIDATION REPORT")
    print("="*70)
    
    print(f"\n✓ Output file: {output_path}")
    print(f"✓ Total steps: {validation['total_steps']}")
    print(f"✓ Steps with content: {validation['steps_with_content']}")
    
    if validation['empty_observations'] > 0:
        print(f"\n⚠ Steps with empty observations: {validation['empty_observations']}")
        if validation['empty_steps']:
            print(f"  Empty steps: {', '.join(validation['empty_steps'])}")
    else:
        print("\n✓ All steps have observations")
    
    if validation['empty_thoughts'] > 0:
        print(f"\n⚠ Steps with empty thoughts: {validation['empty_thoughts']}")
    else:
        print("\n✓ All steps have thoughts")
    
    print("\n" + "="*70)


def get_output_path(task_name: str) -> str:
    """
    Determine the output JSON path based on the task name.
    Output will be saved in the same folder as the input notebook.
    """
    # Get the base directory (Local Scripts folder parent is project root)
    base_dir = Path(__file__).parent.parent
    output_path = base_dir / "Input Data" / task_name / "observation_thought.json"
    
    return str(output_path)


def print_sample(data: Dict[str, Any], num_steps: int = 2) -> None:
    """Print sample output from the generated data."""
    print("\n" + "="*70)
    print(f"  SAMPLE OUTPUT (First {num_steps} steps)")
    print("="*70)
    
    sample_steps = sorted(data.keys(), key=lambda x: int(x.split('_')[1]))[:num_steps]
    
    for step in sample_steps:
        print(f"\n{step}:")
        obs = data[step]['observation']
        thought = data[step]['thought']
        
        if obs:
            print(f"  observation: {obs[:80]}{'...' if len(obs) > 80 else ''}")
        else:
            print(f"  observation: [EMPTY]")
        
        if thought:
            print(f"  thought: {thought[:80]}{'...' if len(thought) > 80 else ''}")
        else:
            print(f"  thought: [EMPTY]")


def main():
    """Main execution function."""
    print("="*70)
    print("  TASK NOTEBOOK TO JSON CONVERTER")
    print("="*70)
    
    # Get task name from command line (e.g., "task_645")
    if len(sys.argv) < 2:
        print("\nUsage: python \"Local Scripts\\generate_observations_thoughts.py\" task_<number>")
        print("Example: python \"Local Scripts\\generate_observations_thoughts.py\" task_645")
        sys.exit(1)
    
    task_name = sys.argv[1]
    
    # Build notebook path using new structure: Input Data/task_<number>/task_<number>.ipynb
    base_dir = Path(__file__).parent.parent
    notebook_path = str(base_dir / "Input Data" / task_name / f"{task_name}.ipynb")
    
    # Check if input file exists
    if not Path(notebook_path).exists():
        print(f"\nERROR: Notebook file not found: {notebook_path}")
        sys.exit(1)
    
    # Determine output path (same folder as input)
    output_path = get_output_path(task_name)
    
    print(f"\nInput:  {notebook_path}")
    print(f"Output: {output_path}")
    
    # Parse notebook
    print("\n" + "-"*70)
    print("  PARSING NOTEBOOK...")
    print("-"*70)
    
    try:
        task_data = parse_notebook_to_json(notebook_path)
        
        if not task_data:
            print("\nERROR: No data extracted from notebook")
            sys.exit(1)
        
        # Save to JSON
        save_json(task_data, output_path)
        print(f"\n✓ Successfully created: {output_path}")
        print(f"✓ Extracted {len(task_data)} steps")
        
        # Validate output
        validation = validate_output(task_data, notebook_path)
        print_validation_report(validation, output_path)
        
        # Print sample
        print_sample(task_data, num_steps=2)
        
        print("\n" + "="*70)
        print("  CONVERSION COMPLETE")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
