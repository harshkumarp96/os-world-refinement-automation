"""Verification script to check notebook structure follows the expected format.

Expected structure for each step:
1. ## Step N
2. ![Step Image](screenshots/N.png)
3. ### Observation
4. <observation content>
5. ### Thought
6. <thought content>
7. ### Action
8. <action content>
9. ### Code
10. <code content>
"""

import json
import sys
from pathlib import Path

def verify_notebook(notebook_path):
    """Verify that notebook follows the expected structure."""
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    cells = notebook['cells']
    issues = []
    warnings = []
    step_count = 0
    
    # Check first cell is task title
    if len(cells) > 0:
        first_cell = ''.join(cells[0]['source']) if isinstance(cells[0]['source'], list) else cells[0]['source']
        if not first_cell.strip().startswith('# Task '):
            issues.append("First cell should be '# Task <number>'")
    
    # Check second cell is instruction
    if len(cells) > 1:
        second_cell = ''.join(cells[1]['source']) if isinstance(cells[1]['source'], list) else cells[1]['source']
        if not second_cell.strip().startswith('## Instruction'):
            issues.append("Second cell should be '## Instruction'")
    
    # Process each step
    i = 0
    while i < len(cells):
        cell = cells[i]
        if cell['cell_type'] == 'markdown':
            content = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']
            
            # Check for step header
            if content.strip().startswith('## Step '):
                step_count += 1
                step_num = content.strip().split('## Step ')[1].strip()
                
                # Expected structure after step header
                expected_sequence = [
                    ('image', f'![Step Image](screenshots/{step_num}.png)'),
                    ('observation_header', '### Observation'),
                    ('observation_content', None),
                    ('thought_header', '### Thought'),
                    ('thought_content', None),
                    ('action_header', '### Action'),
                    ('action_content', None),
                    ('code_header', '### Code'),
                    ('code_content', None)
                ]
                
                j = i + 1
                seq_idx = 0
                
                while j < len(cells) and seq_idx < len(expected_sequence):
                    if j >= len(cells):
                        break
                    
                    next_cell = cells[j]
                    next_content = ''.join(next_cell['source']) if isinstance(next_cell['source'], list) else next_cell['source']
                    next_content_strip = next_content.strip()
                    
                    # Stop at next step
                    if next_content_strip.startswith('## Step '):
                        break
                    
                    exp_type, exp_value = expected_sequence[seq_idx]
                    
                    # Check image
                    if exp_type == 'image':
                        if not next_content_strip.startswith('![Step Image](screenshots/'):
                            issues.append(f"Step {step_num}: Missing or incorrect screenshot image reference")
                        else:
                            # Verify image path matches step number
                            if f'screenshots/{step_num}.png' not in next_content_strip:
                                warnings.append(f"Step {step_num}: Screenshot path doesn't match step number")
                        seq_idx += 1
                    
                    # Check headers
                    elif exp_type in ['observation_header', 'thought_header', 'action_header', 'code_header']:
                        if next_content_strip.startswith(exp_value):
                            # For action_header, content is in the same cell
                            if exp_type == 'action_header':
                                # Check if there's content after the header in the same cell
                                if len(next_content_strip) > len(exp_value):
                                    seq_idx += 2  # Skip both header and content check
                                else:
                                    warnings.append(f"Step {step_num}: Action header found but content is empty")
                                    seq_idx += 2
                            else:
                                seq_idx += 1
                        else:
                            section = exp_type.replace('_header', '').capitalize()
                            issues.append(f"Step {step_num}: Missing '### {section}' header in correct order")
                            break
                    
                    # Check content cells
                    elif exp_type in ['observation_content', 'thought_content', 'action_content', 'code_content']:
                        # Content should not be another header
                        if next_content_strip.startswith('###'):
                            section = exp_type.replace('_content', '').capitalize()
                            issues.append(f"Step {step_num}: Missing {section} content")
                            seq_idx += 1
                            continue
                        
                        # Check content is not empty
                        if not next_content_strip:
                            section = exp_type.replace('_content', '').capitalize()
                            warnings.append(f"Step {step_num}: {section} content is empty")
                        
                        seq_idx += 1
                    
                    j += 1
                
                # Check if all expected elements were found
                if seq_idx < len(expected_sequence):
                    missing = expected_sequence[seq_idx][0].replace('_', ' ').title()
                    issues.append(f"Step {step_num}: Incomplete structure, stopped at {missing}")
        
        i += 1
    
    # Print results
    print(f"{'='*60}")
    print(f"Verification Results for: {notebook_path.name}")
    print(f"{'='*60}")
    print(f"✓ Total steps found: {step_count}\n")
    
    if issues:
        print(f"✗ ISSUES FOUND ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
        print()
    
    if warnings:
        print(f"⚠ WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    if not issues and not warnings:
        print("✓ ALL CHECKS PASSED")
        print("✓ Notebook structure is correct")
        print(f"✓ All {step_count} steps follow the expected format:")
        print("  - Step header")
        print("  - Screenshot image")
        print("  - Observation")
        print("  - Thought")
        print("  - Action")
        print("  - Code")
        return True
    elif not issues:
        print("✓ STRUCTURE IS VALID (with warnings)")
        return True
    else:
        print("✗ STRUCTURE VALIDATION FAILED")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_structure.py <task_folder>")
        print("Example: python verify_structure.py task_645")
        sys.exit(1)
    
    task_folder = sys.argv[1]
    base_dir = Path(__file__).parent.parent
    
    # Look for task_folder with task_folder_updated.ipynb
    notebook_path = base_dir / "Input Data" / task_folder / f"{task_folder}_updated.ipynb"
    
    if not notebook_path.exists():
        print(f"✗ Error: Notebook not found at {notebook_path}")
        print(f"\nExpected path: Input Data/{task_folder}/{task_folder}_updated.ipynb")
        sys.exit(1)
    
    print(f"\nVerifying notebook structure...\n")
    success = verify_notebook(notebook_path)
    print(f"\n{'='*60}\n")
    
    sys.exit(0 if success else 1)
