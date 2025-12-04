"""Quick verification script to check for duplicate observations/thoughts in notebook."""

import json
import sys
from pathlib import Path

def verify_notebook(notebook_path):
    """Verify that each step has exactly one observation, one thought, and one action."""
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    cells = notebook['cells']
    step_num = 0
    i = 0
    
    issues = []
    
    while i < len(cells):
        cell = cells[i]
        
        if cell['cell_type'] == 'markdown':
            content = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']
            
            # Check for step header
            if content.strip().startswith('## Step '):
                step_num += 1
                obs_count = 0
                thought_count = 0
                action_count = 0
                
                # Look ahead to count obs/thought/action headers for this step
                j = i + 1
                while j < len(cells):
                    next_cell = cells[j]
                    if next_cell['cell_type'] == 'markdown':
                        next_content = ''.join(next_cell['source']) if isinstance(next_cell['source'], list) else next_cell['source']
                        
                        # Stop at next step
                        if next_content.strip().startswith('## Step '):
                            break
                        
                        # Count obs/thought/action headers
                        if next_content.strip() == '### Observation':
                            obs_count += 1
                        elif next_content.strip() == '### Thought':
                            thought_count += 1
                        elif next_content.strip() == '### Action':
                            action_count += 1
                    
                    j += 1
                
                # Check for duplicates or missing
                if obs_count > 1:
                    issues.append(f"Step {step_num}: {obs_count} observations (expected 1)")
                elif obs_count == 0:
                    issues.append(f"Step {step_num}: 0 observations (expected 1)")
                
                if thought_count > 1:
                    issues.append(f"Step {step_num}: {thought_count} thoughts (expected 1)")
                elif thought_count == 0:
                    issues.append(f"Step {step_num}: 0 thoughts (expected 1)")
                
                if action_count > 1:
                    issues.append(f"Step {step_num}: {action_count} actions (expected 1)")
                elif action_count == 0:
                    issues.append(f"Step {step_num}: 0 actions (expected 1)")
        
        i += 1
    
    print(f"✓ Checked {step_num} steps\n")
    
    if issues:
        print("✗ ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ NO DUPLICATES FOUND")
        print("✓ Each step has exactly 1 observation, 1 thought, and 1 action")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_structure.py <task_number>")
        print("Example: python verify_structure.py 77")
        sys.exit(1)
    
    task_num = sys.argv[1]
    base_dir = Path(__file__).parent.parent
    notebook_path = base_dir / "Input Data" / "colab_notebook" / f"task_{task_num}.ipynb"
    
    if not notebook_path.exists():
        print(f"✗ Error: Notebook not found at {notebook_path}")
        sys.exit(1)
    
    verify_notebook(notebook_path)
