"""
Validator service for processing tasks and coordinating validations
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from src.models.schemas import (
    ValidationRequest,
    ValidationResponse,
    TaskValidationResult,
    StepData
)
from src.services.anthropic_service import AnthropicService
from src.utils.logger import logger
from config.settings import settings

class ValidatorService:
    """Service for validating task observations and thoughts"""
    
    def __init__(self):
        """Initialize validator service"""
        self.anthropic_service = AnthropicService()
        logger.info("Validator service initialized")
    
    def load_task_json(self, task_id: str) -> Dict:
        """
        Load task JSON file from the new modular structure
        
        Args:
            task_id: Task identifier (e.g., 'task_645')
            
        Returns:
            Dictionary with task data
        """
        # New structure: Input Data/task_645/observation_thought.json
        task_folder = settings.input_data_dir / task_id
        json_path = task_folder / "observation_thought.json"
        
        # Fallback to old structure for backward compatibility
        if not json_path.exists():
            old_json_path = settings.input_json_dir / f"{task_id}.json"
            if old_json_path.exists():
                logger.warning(f"Using legacy JSON path: {old_json_path}")
                json_path = old_json_path
            else:
                raise FileNotFoundError(
                    f"Task JSON not found. Tried:\n"
                    f"  - {json_path}\n"
                    f"  - {old_json_path}"
                )
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {task_id} with {len(data)} steps from {json_path}")
        return data
    
    def get_screenshot_path(self, task_id: str, step_number: int) -> Path:
        """
        Get the path to a screenshot from the new modular structure
        
        Args:
            task_id: Task identifier
            step_number: Step number (1-based)
            
        Returns:
            Path to the screenshot
        """
        # New structure: Input Data/task_645/screenshots/1.png
        task_folder = settings.input_data_dir / task_id
        screenshot_path = task_folder / "screenshots" / f"{step_number}.png"
        
        # Fallback to old structure for backward compatibility
        if not screenshot_path.exists():
            old_screenshot_path = settings.screenshots_dir / task_id / f"{step_number}.png"
            if old_screenshot_path.exists():
                screenshot_path = old_screenshot_path
            else:
                raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")
        
        return screenshot_path
    
    def prepare_validation_requests(self, task_id: str, task_data: Dict) -> List[Dict]:
        """
        Prepare validation requests from task data with continuity context
        
        Args:
            task_id: Task identifier
            task_data: Task data dictionary
            
        Returns:
            List of validation request dictionaries
        """
        # First pass: collect all steps
        all_steps = {}
        for step_key, step_data in task_data.items():
            if not step_key.startswith("step_"):
                continue
            step_number = int(step_key.split("_")[1])
            all_steps[step_number] = {
                "step_key": step_key,
                "observation": step_data.get("observation", ""),
                "thought": step_data.get("thought", "")
            }
        
        # Second pass: create requests with context (only for empty steps)
        requests = []
        sorted_step_numbers = sorted(all_steps.keys())
        
        for step_number in sorted_step_numbers:
            step_info = all_steps[step_number]
            step_key = step_info["step_key"]
            observation = step_info["observation"]
            thought = step_info["thought"]
            
            # Check if we need to generate from scratch
            is_empty = not observation.strip() and not thought.strip()
            
            # Only get previous and next step context if current step is empty
            # This saves tokens when validating steps with existing content
            previous_step = None
            next_step = None
            
            if is_empty:
                idx = sorted_step_numbers.index(step_number)
                if idx > 0:
                    prev_num = sorted_step_numbers[idx - 1]
                    previous_step = all_steps[prev_num]
                if idx < len(sorted_step_numbers) - 1:
                    next_num = sorted_step_numbers[idx + 1]
                    next_step = all_steps[next_num]
                
                logger.info(f"[{task_id} - {step_key}] Empty observation/thought - will generate from screenshot with context")
            
            try:
                screenshot_path = self.get_screenshot_path(task_id, step_number)
                
                requests.append({
                    "task_id": task_id,
                    "step_key": step_key,
                    "step_number": step_number,
                    "screenshot_path": str(screenshot_path),
                    "observation": observation,
                    "thought": thought,
                    "previous_step": previous_step,
                    "next_step": next_step
                })
            except FileNotFoundError as e:
                # Give clear warning about missing screenshot
                if is_empty:
                    logger.error(
                        f"[{task_id} - {step_key}] ⚠️ CRITICAL: Screenshot missing and observation/thought are empty. "
                        f"Cannot generate content without screenshot. {str(e)}"
                    )
                    raise ValueError(
                        f"Cannot generate content for {step_key}: "
                        f"Screenshot is missing and observation/thought are empty. "
                        f"At least one must be provided."
                    )
                else:
                    logger.warning(
                        f"[{task_id} - {step_key}] ⚠️ WARNING: Screenshot not found at expected location. "
                        f"Validation will be skipped for this step. {str(e)}"
                    )
                    continue
        
        logger.info(f"Prepared {len(requests)} validation requests for {task_id}")
        return requests
    
    async def validate_task(self, task_id: str) -> TaskValidationResult:
        """
        Validate all steps in a task
        
        Args:
            task_id: Task identifier
            
        Returns:
            TaskValidationResult with all validation responses
        """
        logger.info(f"Starting validation for {task_id}")
        
        # Load task data
        task_data = self.load_task_json(task_id)
        
        # Prepare validation requests
        validation_requests = self.prepare_validation_requests(task_id, task_data)
        
        if not validation_requests:
            raise ValueError(f"No valid steps found for {task_id}")
        
        # Validate all steps concurrently
        results = await self.anthropic_service.validate_multiple_steps(validation_requests)
        
        # Process results
        validated_steps = {}
        successful = 0
        failed = 0
        total_tokens = {"input_tokens": 0, "output_tokens": 0}
        
        for req, result in zip(validation_requests, results):
            step_key = req["step_key"]
            
            if isinstance(result, Exception):
                # Handle error
                logger.error(f"Failed to validate {step_key}: {str(result)}")
                validated_steps[step_key] = ValidationResponse(
                    task_id=task_id,
                    step_number=req["step_number"],
                    step_key=step_key,
                    updated_observation=req["observation"],
                    updated_thought=req["thought"],
                    validation_reasoning="",
                    original_observation=req["observation"],
                    original_thought=req["thought"],
                    screenshot_path=req["screenshot_path"],
                    success=False,
                    error=str(result)
                )
                failed += 1
            else:
                # Success
                tokens = result.pop("tokens_used", None)
                if tokens:
                    total_tokens["input_tokens"] += tokens.get("input_tokens", 0)
                    total_tokens["output_tokens"] += tokens.get("output_tokens", 0)
                
                validated_steps[step_key] = ValidationResponse(
                    task_id=task_id,
                    step_number=req["step_number"],
                    step_key=step_key,
                    updated_observation=result.get("updated_observation", req["observation"]),
                    updated_thought=result.get("updated_thought", req["thought"]),
                    validation_reasoning=result.get("validation_reasoning", ""),
                    original_observation=req["observation"],
                    original_thought=req["thought"],
                    screenshot_path=req["screenshot_path"],
                    tokens_used=tokens,
                    success=True
                )
                successful += 1
        
        # Save output
        output_path = self.save_validated_task(task_id, validated_steps)
        
        result = TaskValidationResult(
            task_id=task_id,
            total_steps=len(validation_requests),
            successful_validations=successful,
            failed_validations=failed,
            steps=validated_steps,
            output_path=str(output_path),
            total_tokens_used=total_tokens if total_tokens["input_tokens"] > 0 else None
        )
        
        logger.info(f"Completed {task_id}: {successful}/{len(validation_requests)} successful")
        
        return result
    
    def save_validated_task(self, task_id: str, validated_steps: Dict[str, ValidationResponse]) -> Path:
        """
        Save validated task to output JSON in the task folder
        
        Args:
            task_id: Task identifier
            validated_steps: Dictionary of validated steps
            
        Returns:
            Path to the output file
        """
        # Create output structure matching input format
        output_data = {}
        
        for step_key, response in validated_steps.items():
            output_data[step_key] = {
                "observation": response.updated_observation,
                "thought": response.updated_thought
            }
        
        # Save to task folder: Input Data/task_645/validated_observation_thought.json
        task_folder = settings.input_data_dir / task_id
        task_folder.mkdir(parents=True, exist_ok=True)
        
        output_path = task_folder / "validated_observation_thought.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Saved validated output to {output_path}")
        
        # Also save detailed report in task folder
        report_path = task_folder / "validation_report.json"
        report_data = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "steps": {
                step_key: {
                    "step_number": resp.step_number,
                    "original_observation": resp.original_observation,
                    "updated_observation": resp.updated_observation,
                    "original_thought": resp.original_thought,
                    "updated_thought": resp.updated_thought,
                    "validation_reasoning": resp.validation_reasoning,
                    "tokens_used": resp.tokens_used,
                    "success": resp.success,
                    "error": resp.error
                }
                for step_key, resp in validated_steps.items()
            }
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Saved detailed report to {report_path}")
        
        return output_path
