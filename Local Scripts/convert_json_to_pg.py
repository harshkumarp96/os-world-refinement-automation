import json
import sys
import os

def convert_to_pyautogui(event):
    """Convert a single event to PyAutoGUI command"""
    event_type = event.get("type")
    data = event.get("data", {})
    
    if event_type == "click":
        x = data.get("x")
        y = data.get("y")
        text = data.get("text", "").lower()
        num_clicks = data.get("numClicks", 1)
        
        if "right" in text:
            if num_clicks == 2:
                return f"pg.click({x}, {y}, clicks=2, button='right')"
            else:
                return f"pg.click({x}, {y}, button='right')"
        elif "middle" in text:
            if num_clicks == 2:
                return f"pg.click({x}, {y}, clicks=2, button='middle')"
            else:
                return f"pg.click({x}, {y}, button='middle')"
        else:  # left-click
            if num_clicks == 2:
                return f"pg.click({x}, {y}, clicks=2)"
            else:
                return f"pg.click({x}, {y})"
    
    elif event_type == "typing":
        text = data.get("text", "")
        return f'pg.write("{text}", interval=0.1)'
    
    elif event_type == "hotkey":
        keys = data.get("keys", [])
        keys_str = ", ".join([f'"{k.lower()}"' for k in keys])
        return f"pg.hotkey({keys_str})"
    
    elif event_type == "press":
        key = data.get("key", "").lower()
        return f'pg.press("{key}")'
    
    elif event_type == "dragFromTo":
        x_end = data.get("xEnd")
        y_end = data.get("yEnd")
        return f"pg.dragTo({x_end}, {y_end}, duration=1, button='left')"
    
    elif event_type == "scroll":
        scroll_direction = data.get("scrollDirection", "").lower()
        total_distance = data.get("totalScrollDistance", 0)
        
        if scroll_direction == "down":
            return f"pg.scroll(-{total_distance})"
        else:  # up
            return f"pg.scroll({total_distance})"
    
    elif event_type == "wait":
        return None  # Exclude wait events
    
    else:
        return f"# Unknown event type: {event_type}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_json_to_pg.py <input_json_file> [output_txt_file]")
        print("\nExample:")
        print("  python convert_json_to_pg.py task_78.json")
        print("  python convert_json_to_pg.py task_78.json output.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Determine output file name
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # Replace .json extension with .txt
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.txt"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    # Read JSON file
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{input_file}': {e}")
        sys.exit(1)
    
    events = data.get("events", [])
    
    if not events:
        print(f"⚠️  Warning: No events found in '{input_file}'")
        sys.exit(0)
    
    # Convert events to PyAutoGUI commands
    commands = []
    event_stats = {}
    
    for event in events:
        event_type = event.get("type")
        event_stats[event_type] = event_stats.get(event_type, 0) + 1
        
        pg_command = convert_to_pyautogui(event)
        if pg_command:  # Only add if not None (excludes wait events)
            commands.append(pg_command)
    
    # Write to output file
    with open(output_file, "w") as f:
        for cmd in commands:
            f.write(cmd + "\n")
        # Add exit command as last line
        f.write("import sys; sys.exit(0)\n")
    
    # Print statistics
    print(f"✓ Processed {len(events)} events from '{input_file}'")
    print(f"✓ Generated {len(commands)} PyAutoGUI commands (wait events excluded)")
    print(f"✓ Output saved to '{output_file}'")
    print(f"\nCommand breakdown:")
    for event_type, count in sorted(event_stats.items()):
        status = "(excluded)" if event_type == "wait" else ""
        print(f"  • {event_type:12s}: {count:2d} {status}")
    
    # Show first 20 commands
    if commands:
        print(f"\nFirst {min(20, len(commands))} commands:")
        for i, cmd in enumerate(commands[:20], 1):
            print(f"{i:2d}. {cmd}")

if __name__ == "__main__":
    main()
