#!/usr/bin/env python3
"""
Standalone script to process a task end-to-end.

Usage:
    python process_task.py <task_folder>
    
Example:
    python process_task.py task_645
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description, cwd=None):
    """Run a command and handle errors."""
    print(f"\n{'='*70}")
    print(f"  {description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, cwd=cwd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"\n✗ Error: {description} failed with exit code {result.returncode}")
        sys.exit(1)
    
    print(f"\n✓ {description} completed successfully")
    return result


def check_venv():
    """Check if virtual environment is activated."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)


def activate_venv_and_install():
    """Activate venv and install requirements if needed."""
    project_root = Path(__file__).parent
    venv_path = project_root / "venv"
    
    # Check if venv exists
    if not venv_path.exists():
        print(f"\n{'='*70}")
        print("  CREATING VIRTUAL ENVIRONMENT")
        print(f"{'='*70}\n")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✓ Virtual environment created")
    
    # Determine activation script and python executable
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/Mac
        activate_script = venv_path / "bin" / "activate"
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    # Check if requirements are installed by trying to import a key package
    try:
        result = subprocess.run(
            [str(python_exe), "-c", "import anthropic"],
            capture_output=True,
            text=True
        )
        requirements_installed = (result.returncode == 0)
    except:
        requirements_installed = False
    
    # Install requirements if needed
    if not requirements_installed:
        print(f"\n{'='*70}")
        print("  INSTALLING REQUIREMENTS")
        print(f"{'='*70}\n")
        requirements_file = project_root / "requirements.txt"
        subprocess.run([str(pip_exe), "install", "-r", str(requirements_file)], check=True)
        print("✓ Requirements installed")
    else:
        print("\n✓ Requirements already installed")
    
    return python_exe


def main():
    """Main execution function."""
    print("="*70)
    print("  TASK PROCESSING PIPELINE")
    print("="*70)
    
    # Get task folder from command line
    if len(sys.argv) < 2:
        print("\nUsage: python process_task.py <task_folder>")
        print("Example: python process_task.py task_645")
        sys.exit(1)
    
    task_folder = sys.argv[1]
    
    # Extract task number for verification script
    task_num = task_folder.replace('task_', '') if task_folder.startswith('task_') else task_folder
    
    print(f"\nProcessing: {task_folder}")
    print(f"Task number: {task_num}")
    
    # Get project root
    project_root = Path(__file__).parent
    
    # Verify task folder exists
    task_path = project_root / "Input Data" / task_folder
    if not task_path.exists():
        print(f"\n✗ Error: Task folder not found at {task_path}")
        sys.exit(1)
    
    print(f"Task path: {task_path}")
    
    # Validate required files exist before starting
    print(f"\n{'='*70}")
    print("  VALIDATING INPUT FILES")
    print(f"{'='*70}\n")
    
    required_files = {
        'notebook': task_path / f"{task_folder}.ipynb",
        'events': task_path / "events.json"
    }
    
    missing_files = []
    for file_type, file_path in required_files.items():
        if file_path.exists():
            print(f"✓ Found {file_type}: {file_path.name}")
        else:
            print(f"✗ Missing {file_type}: {file_path.name}")
            print(f"  → Please provide: Input Data/{task_folder}/{file_path.name}")
            missing_files.append((file_type, file_path.name))
    
    if missing_files:
        print(f"\n✗ Error: Cannot proceed. Missing {len(missing_files)} required file(s).")
        sys.exit(1)
    
    print(f"\n✓ All required files present")
    
    # Activate venv and install requirements
    python_exe = activate_venv_and_install()
    
    # Step 1: Convert JSON to PyAutoGUI commands
    run_command(
        [str(python_exe), "Local Scripts/convert_json_to_pg.py", task_folder],
        "Step 1: Converting JSON to PyAutoGUI commands",
        cwd=project_root
    )
    
    # Step 2: Download screenshots
    run_command(
        [str(python_exe), "Local Scripts/download_screenshot.py", task_folder],
        "Step 2: Downloading screenshots",
        cwd=project_root
    )
    
    # Step 3: Generate observations and thoughts
    run_command(
        [str(python_exe), "Local Scripts/generate_observations_thoughts.py", task_folder],
        "Step 3: Generating observations and thoughts",
        cwd=project_root
    )
    
    # Step 4: Run main validation (using python -m syntax)
    run_command(
        [str(python_exe), "-m", "src.main", task_folder],
        "Step 4: Running validation service",
        cwd=project_root
    )
    
    # Step 5: Update notebook with validated data
    run_command(
        [str(python_exe), "Local Scripts/update_notebook.py", task_folder],
        "Step 5: Updating notebook with validated data",
        cwd=project_root
    )
    
    # Step 6: Verify structure
    run_command(
        [str(python_exe), "Local Scripts/verify_structure.py", task_folder],
        "Step 6: Verifying notebook structure",
        cwd=project_root
    )
    
    print(f"\n{'='*70}")
    print("  PIPELINE COMPLETED SUCCESSFULLY")
    print(f"{'='*70}")
    print(f"\nOutput file: {task_path / f'{task_folder}_updated.ipynb'}")
    print()


if __name__ == "__main__":
    main()
