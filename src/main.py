"""
Main application entry point for Screenshot Validator
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from src.services.validator_service import ValidatorService
from src.utils.logger import logger
from config.settings import settings

console = Console()

async def validate_task(task_id: str, validator: ValidatorService):
    """
    Validate a single task
    
    Args:
        task_id: Task identifier (e.g., 'task_84')
        validator: ValidatorService instance
    """
    try:
        console.print(f"\n[bold cyan]Validating {task_id}...[/bold cyan]")
        
        result = await validator.validate_task(task_id)
        
        # Display results
        table = Table(title=f"Validation Results for {task_id}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Steps", str(result.total_steps))
        table.add_row("Successful", str(result.successful_validations))
        table.add_row("Failed", str(result.failed_validations))
        
        if result.total_tokens_used:
            table.add_row(
                "Total Tokens", 
                f"{result.total_tokens_used['input_tokens']} in / {result.total_tokens_used['output_tokens']} out"
            )
        
        table.add_row("Output File", str(result.output_path))
        
        console.print(table)
        
        # Show step-by-step summary
        console.print(f"\n[bold]Step Details:[/bold]")
        for step_key, step_result in result.steps.items():
            status = "✓" if step_result.success else "✗"
            status_color = "green" if step_result.success else "red"
            console.print(f"  [{status_color}]{status}[/{status_color}] {step_key} (Step {step_result.step_number})")
            
            if step_result.validation_reasoning:
                console.print(f"    [dim]{step_result.validation_reasoning[:100]}...[/dim]")
        
        return result
        
    except Exception as e:
        console.print(f"[bold red]Error validating {task_id}:[/bold red] {str(e)}")
        logger.error(f"Error validating {task_id}: {str(e)}", exc_info=True)
        raise

async def validate_all_tasks(validator: ValidatorService):
    """
    Validate all tasks in the Input Data directory
    
    Args:
        validator: ValidatorService instance
    """
    # Find all task folders in new structure
    task_folders = []
    if settings.input_data_dir.exists():
        task_folders = [d for d in settings.input_data_dir.iterdir() 
                       if d.is_dir() and d.name.startswith("task_") 
                       and (d / "observation_thought.json").exists()]
    
    # Also check legacy structure for backward compatibility
    if settings.input_json_dir.exists():
        legacy_files = list(settings.input_json_dir.glob("task_*.json"))
        for json_file in legacy_files:
            task_id = json_file.stem
            if not any(f.name == task_id for f in task_folders):
                task_folders.append(json_file.parent.parent / task_id)
    
    if not task_folders:
        console.print("[yellow]No task folders found in the Input Data directory[/yellow]")
        return
    
    console.print(f"\n[bold cyan]Found {len(task_folders)} tasks to validate[/bold cyan]")
    
    results = []
    for task_folder in task_folders:
        task_id = task_folder.name
        result = await validate_task(task_id, validator)
        results.append(result)
    
    # Summary table
    summary_table = Table(title="Overall Summary")
    summary_table.add_column("Task ID", style="cyan")
    summary_table.add_column("Steps", justify="right")
    summary_table.add_column("Success", justify="right", style="green")
    summary_table.add_column("Failed", justify="right", style="red")
    summary_table.add_column("Tokens", justify="right")
    
    total_tokens = {"input": 0, "output": 0}
    
    for result in results:
        tokens_str = "-"
        if result.total_tokens_used:
            tokens_str = f"{result.total_tokens_used['input_tokens']} / {result.total_tokens_used['output_tokens']}"
            total_tokens["input"] += result.total_tokens_used['input_tokens']
            total_tokens["output"] += result.total_tokens_used['output_tokens']
        
        summary_table.add_row(
            result.task_id,
            str(result.total_steps),
            str(result.successful_validations),
            str(result.failed_validations),
            tokens_str
        )
    
    console.print(f"\n{summary_table}")
    console.print(f"\n[bold]Total Tokens Used:[/bold] {total_tokens['input']} input / {total_tokens['output']} output")

async def main():
    """Main entry point"""
    console.print("[bold green]Screenshot Validator[/bold green]")
    console.print(f"Model: {settings.anthropic_model}")
    console.print(f"Output Directory: {settings.output_dir}\n")
    
    # Check API key
    if not settings.anthropic_api_key:
        console.print("[bold red]Error:[/bold red] ANTHROPIC_API_KEY not set in environment")
        console.print("Please create a .env file with your API key (see .env.example)")
        sys.exit(1)
    
    # Initialize validator
    validator = ValidatorService()
    
    # Parse command-line arguments
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
        await validate_task(task_id, validator)
    else:
        await validate_all_tasks(validator)
    
    console.print("\n[bold green]✓ Validation complete![/bold green]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Validation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error:[/bold red] {str(e)}")
        logger.error("Fatal error", exc_info=True)
        sys.exit(1)
