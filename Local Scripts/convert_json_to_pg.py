import json
import sys
import os
from pathlib import Path

def convert_to_pyautogui(event):
    """Convert a single event to PyAutoGUI command"""
    event_type = event.get("type")
    data = event.get("data", {})
    
    if event_type == "click":
        x = data.get("x")
        y = data.get("y")
        text = data.get("text", "").lower()
        num_clicks = data.get("numClicks", 1)
        
        # Handle right-click
        if "right" in text:
            if num_clicks == 2:
                return f"pyautogui.rightClick({x}, {y}); pyautogui.rightClick({x}, {y})"
            elif num_clicks == 3:
                return f"pyautogui.rightClick({x}, {y}); pyautogui.rightClick({x}, {y}); pyautogui.rightClick({x}, {y})"
            else:
                return f"pyautogui.rightClick({x}, {y})"
        
        # Handle middle-click
        elif "middle" in text:
            if num_clicks == 2:
                return f"pyautogui.middleClick({x}, {y}); pyautogui.middleClick({x}, {y})"
            elif num_clicks == 3:
                return f"pyautogui.middleClick({x}, {y}); pyautogui.middleClick({x}, {y}); pyautogui.middleClick({x}, {y})"
            else:
                return f"pyautogui.middleClick({x}, {y})"
        
        # Handle left-click (default)
        else:
            if num_clicks == 2:
                return f"pyautogui.doubleClick({x}, {y})"
            elif num_clicks == 3:
                return f"pyautogui.tripleClick({x}, {y})"
            else:
                return f"pyautogui.click({x}, {y})"
    
    elif event_type == "typing":
        text = data.get("text", "")
        return f'pyautogui.write("{text}", interval=0.1)'
    
    elif event_type == "hotkey":
        keys = data.get("keys", [])
        keys_str = ", ".join([f'"{k.lower()}"' for k in keys])
        return f"pyautogui.hotkey({keys_str})"
    
    elif event_type == "press":
        key = data.get("key", "").lower()
        return f'pyautogui.press("{key}")'
    
    elif event_type == "dragFromTo":
        x_end = data.get("xEnd")
        y_end = data.get("yEnd")
        return f"pyautogui.dragTo({x_end}, {y_end}, duration=1, button='left')"
    
    elif event_type == "scroll":
        scroll_direction = data.get("scrollDirection", "").lower()
        total_distance = data.get("totalScrollDistance", 0)
        
        if scroll_direction == "down":
            return f"pyautogui.scroll(-{total_distance})"
        else:  # up
            return f"pyautogui.scroll({total_distance})"
    
    elif event_type == "wait":
        return None  # Exclude wait events
    
    else:
        return f"# Unknown event type: {event_type}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_json_to_pg.py <task_folder>")
        print("Example: python convert_json_to_pg.py task_78")
        sys.exit(1)
    
    task_folder = sys.argv[1]
    
    # Get the script's parent directory (project root)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    # Construct input paths
    input_task_dir = project_root / "Input Data" / task_folder
    input_file = input_task_dir / "events.json"
    
    # Check if task folder exists
    if not input_task_dir.exists():
        print(f"Error: Task folder not found at 'Input Data/{task_folder}'")
        sys.exit(1)
    
    # Check if events.json exists
    if not input_file.exists():
        print(f"Error: events.json not found in 'Input Data/{task_folder}/'")
        sys.exit(1)
    
    # Construct output file path in same directory as input
    output_file = input_task_dir / "pg_commands.txt"
    
    # Read JSON file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Could not read file: {e}")
        sys.exit(1)
    
    # Get events from JSON
    events = data.get("events", [])
    
    if not events:
        print("Error: No events array found in events.json")
        sys.exit(1)
    
    # Convert events to PyAutoGUI commands
    commands = []
    event_stats = {}
    
    for event in events:
        event_type = event.get("type")
        event_stats[event_type] = event_stats.get(event_type, 0) + 1
        
        pg_command = convert_to_pyautogui(event)
        if pg_command:
            commands.append(pg_command)
    
    # Write to output file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for cmd in commands[:-1]:
                f.write(cmd + "\n")
            if commands:
                f.write("import sys sys.exit(0)\n")
    except Exception as e:
        print(f"Error: Could not write output file: {e}")
        sys.exit(1)
    
    # Print results
    print(f"Processed {len(events)} events")
    print(f"Generated {len(commands)} PyAutoGUI commands")
    print(f"Output saved to 'Input Data/{task_folder}/pg_commands.txt'")

if __name__ == "__main__":
    main()
