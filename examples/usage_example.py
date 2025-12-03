"""
Example usage of the Screenshot Validator
"""
import asyncio
from pathlib import Path
from src.services.validator_service import ValidatorService
from src.utils.logger import logger

async def example_single_task():
    """Example: Validate a single task"""
    print("=== Example 1: Validate a single task ===\n")
    
    validator = ValidatorService()
    
    # Validate task_84
    result = await validator.validate_task("task_84")
    
    print(f"\nTask ID: {result.task_id}")
    print(f"Total Steps: {result.total_steps}")
    print(f"Successful: {result.successful_validations}")
    print(f"Failed: {result.failed_validations}")
    print(f"Output saved to: {result.output_path}")
    
    # Show first step details
    if result.steps:
        first_step = list(result.steps.values())[0]
        print(f"\nFirst Step Details:")
        print(f"  Original Observation: {first_step.original_observation[:100]}...")
        print(f"  Updated Observation: {first_step.updated_observation[:100]}...")
        print(f"  Reasoning: {first_step.validation_reasoning[:100]}...")

async def example_programmatic_usage():
    """Example: Programmatic usage with custom data"""
    print("\n=== Example 2: Programmatic usage ===\n")
    
    from src.services.anthropic_service import AnthropicService
    
    anthropic_service = AnthropicService()
    
    # Single validation
    result = await anthropic_service.validate_step_async(
        screenshot_path="Input Data/Screenshots/task_84/1.png",
        observation="This is a test observation that may or may not match the screenshot.",
        thought="This is a test thought process.",
        task_id="custom_task",
        step_number=1
    )
    
    print(f"Updated Observation: {result['updated_observation'][:100]}...")
    print(f"Updated Thought: {result['updated_thought'][:100]}...")
    print(f"Reasoning: {result['validation_reasoning']}")

async def example_batch_validation():
    """Example: Batch validation of multiple steps"""
    print("\n=== Example 3: Batch validation ===\n")
    
    from src.services.anthropic_service import AnthropicService
    
    anthropic_service = AnthropicService()
    
    # Prepare multiple requests
    requests = [
        {
            "screenshot_path": "Input Data/Screenshots/task_84/1.png",
            "observation": "Test observation 1",
            "thought": "Test thought 1",
            "task_id": "batch_test",
            "step_number": 1
        },
        {
            "screenshot_path": "Input Data/Screenshots/task_84/2.png",
            "observation": "Test observation 2",
            "thought": "Test thought 2",
            "task_id": "batch_test",
            "step_number": 2
        }
    ]
    
    # Validate all concurrently
    results = await anthropic_service.validate_multiple_steps(requests)
    
    print(f"Validated {len(results)} steps concurrently")
    for i, result in enumerate(results, 1):
        if not isinstance(result, Exception):
            print(f"\nStep {i}:")
            print(f"  Reasoning: {result.get('validation_reasoning', 'N/A')[:80]}...")

async def example_custom_validation_flow():
    """Example: Custom validation flow with error handling"""
    print("\n=== Example 4: Custom validation with error handling ===\n")
    
    validator = ValidatorService()
    
    try:
        # Load task data
        task_data = validator.load_task_json("task_84")
        print(f"Loaded task with {len(task_data)} steps")
        
        # Prepare requests
        requests = validator.prepare_validation_requests("task_84", task_data)
        print(f"Prepared {len(requests)} validation requests")
        
        # You can filter or modify requests here
        # For example, validate only first 3 steps
        limited_requests = requests[:3]
        print(f"Processing only first {len(limited_requests)} steps")
        
        # Validate
        from src.services.anthropic_service import AnthropicService
        anthropic_service = AnthropicService()
        results = await anthropic_service.validate_multiple_steps(limited_requests)
        
        # Process results
        for req, result in zip(limited_requests, results):
            if isinstance(result, Exception):
                print(f"❌ Step {req['step_number']} failed: {str(result)}")
            else:
                print(f"✓ Step {req['step_number']} validated successfully")
        
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Run all examples"""
    print("Screenshot Validator - Usage Examples\n")
    print("=" * 60)
    
    # Run examples
    await example_single_task()
    
    # Uncomment to run other examples
    # await example_programmatic_usage()
    # await example_batch_validation()
    # await example_custom_validation_flow()
    
    print("\n" + "=" * 60)
    print("Examples completed!")

if __name__ == "__main__":
    asyncio.run(main())
