"""
Pydantic models for data validation
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime

class StepData(BaseModel):
    """Model for each step in the task"""
    observation: str = Field(..., description="LLM-generated observation about the screenshot")
    thought: str = Field(..., description="LLM-generated thought process")

class ValidatedStepData(BaseModel):
    """Model for validated step data"""
    original_observation: str = Field(..., description="Original observation from JSON")
    original_thought: str = Field(..., description="Original thought from JSON")
    updated_observation: str = Field(..., description="Updated observation aligned with screenshot")
    updated_thought: str = Field(..., description="Updated thought aligned with screenshot")
    validation_reasoning: str = Field(..., description="Reasoning for updates made")
    screenshot_path: str = Field(..., description="Path to the screenshot used for validation")
    timestamp: datetime = Field(default_factory=datetime.now)
    tokens_used: Optional[Dict[str, int]] = None

class TaskData(BaseModel):
    """Model for the entire task JSON"""
    steps: Dict[str, StepData] = Field(..., description="Dictionary of steps")
    
    class Config:
        # Allow arbitrary field names like step_1, step_2, etc.
        extra = "allow"

class ValidationRequest(BaseModel):
    """Request for validation of a single step"""
    task_id: str = Field(..., description="Task identifier (e.g., task_84)")
    step_number: int = Field(..., description="Step number (1-based)")
    screenshot_path: str = Field(..., description="Path to the screenshot")
    observation: str = Field(..., description="Original observation text")
    thought: str = Field(..., description="Original thought text")

class ValidationResponse(BaseModel):
    """Response from validation"""
    task_id: str
    step_number: int
    step_key: str
    updated_observation: str
    updated_thought: str
    validation_reasoning: str
    original_observation: str
    original_thought: str
    screenshot_path: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tokens_used: Optional[Dict[str, int]] = None
    success: bool = True
    error: Optional[str] = None

class TaskValidationResult(BaseModel):
    """Result of validating an entire task"""
    task_id: str
    total_steps: int
    successful_validations: int
    failed_validations: int
    steps: Dict[str, ValidationResponse]
    output_path: Optional[str] = None
    total_tokens_used: Optional[Dict[str, int]] = None
