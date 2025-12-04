import json
import sys
import os
from pathlib import Path
import asyncio
import aiohttp

async def download_image(session, url, output_path, event_num, event_type, url_type):
    """Download an image from URL and save to output_path"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            response.raise_for_status()
            
            content = await response.read()
            with open(output_path, 'wb') as f:
                f.write(content)
            
            print(f"  ✓ Event {event_num} ({event_type}, {url_type}) saved")
            return True
    except Exception as e:
        print(f"  ✗ Event {event_num} failed: {e}")
        return False

async def download_all_screenshots(events, screenshots_dir, project_root, task_folder):
    """Download all screenshots asynchronously"""
    download_tasks = []
    
    async with aiohttp.ClientSession() as session:
        for index, event in enumerate(events, start=1):
            event_type = event.get("type")
            screenshots = event.get("screenshots", {})
            
            # Determine which URL to download
            if event_type == "click":
                url = screenshots.get("end")
                url_type = "end"
            else:
                url = screenshots.get("start")
                url_type = "start"
            
            if not url:
                print(f"Warning: No {url_type} screenshot URL found for event {index} (type: {event_type})")
                continue
            
            # Create download task
            output_path = screenshots_dir / f"{index}.png"
            task = download_image(session, url, output_path, index, event_type, url_type)
            download_tasks.append(task)
        
        # Download all screenshots concurrently
        print(f"Downloading {len(download_tasks)} screenshots concurrently...\n")
        results = await asyncio.gather(*download_tasks, return_exceptions=True)
        
        # Count successes
        successful_downloads = sum(1 for r in results if r is True)
        failed_downloads = len(results) - successful_downloads
        
        return successful_downloads, failed_downloads

def main():
    if len(sys.argv) < 2:
        print("Usage: python download_screenshot.py <task_folder>")
        print("Example: python download_screenshot.py task_964")
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
    
    # Create screenshots directory
    screenshots_dir = input_task_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    
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
    
    # Process events and download screenshots asynchronously
    successful_downloads, failed_downloads = asyncio.run(
        download_all_screenshots(events, screenshots_dir, project_root, task_folder)
    )
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Download Summary:")
    print(f"  Total events: {len(events)}")
    print(f"  Successful downloads: {successful_downloads}")
    print(f"  Failed downloads: {failed_downloads}")
    print(f"  Screenshots saved to: Input Data/{task_folder}/screenshots/")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
