"""
Anthropic API service using LangChain
"""
import asyncio
from typing import Dict, Optional
from pathlib import Path
from anthropic import AsyncAnthropic
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from config.settings import settings
from src.utils.logger import logger
from src.utils.image_handler import encode_image_to_base64, get_image_mime_type

class AnthropicService:
    """Service for interacting with Anthropic API"""
    
    def __init__(self):
        """Initialize Anthropic service"""
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        # LangChain Anthropic client
        self.llm = ChatAnthropic(
            model=settings.anthropic_model,
            anthropic_api_key=settings.anthropic_api_key,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature
        )
        
        # Direct Anthropic client for async operations
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    def _create_validation_prompt(
        self, 
        observation: str, 
        thought: str,
        previous_step: dict = None,
        next_step: dict = None
    ) -> str:
        """
        Create the validation prompt for Claude
        
        Args:
            observation: Original observation text (can be empty)
            thought: Original thought text (can be empty)
            previous_step: Previous step data for continuity context
            next_step: Next step data for continuity context
            
        Returns:
            Formatted prompt string
        """
        # Check if we need to generate from scratch
        is_empty = not observation.strip() and not thought.strip()
        
        if is_empty:
            # Generation mode
            context_info = ""
            if previous_step:
                context_info += f"\n**Previous Step Context:**\nObservation: {previous_step.get('observation', '')[:200]}...\nThought: {previous_step.get('thought', '')[:200]}...\n"
            if next_step:
                context_info += f"\n**Next Step Context:**\nObservation: {next_step.get('observation', '')[:200]}...\nThought: {next_step.get('thought', '')[:200]}...\n"
            
            prompt = f"""You are an expert screenshot analyst. Your task is to generate detailed observation and thought for this screenshot from scratch.
{context_info}
**Your Task:**
1. Carefully analyze the screenshot provided
2. Generate a comprehensive observation describing what you see in the screenshot
3. Generate a thought process explaining the reasoning, next actions, or analysis based on what's visible
4. Ensure continuity with the previous and next steps if provided
5. The screenshot is the SINGLE SOURCE OF TRUTH - only describe what's actually visible

**Response Format (JSON):**
{{
    "updated_observation": "Your generated observation describing the screenshot in detail",
    "updated_thought": "Your generated thought process and reasoning",
    "validation_reasoning": "Explanation that this was generated from scratch based on the screenshot"
}}

**Important Guidelines:**
- Be factual and precise
- Only describe what's actually visible in the screenshot
- Provide sufficient detail for understanding the screen state
- Explain the reasoning or next logical actions in the thought
- Maintain continuity with adjacent steps if context is provided
"""
        else:
            # Validation mode
            prompt = f"""You are an expert screenshot analyst. Your task is to validate and correct AI-generated observations and thoughts based on what you actually see in the screenshot.

**Original Observation:**
{observation}

**Original Thought:**
{thought}

**Your Task:**
1. Carefully analyze the screenshot provided
2. Compare the original observation and thought with what you actually see
3. **PRESERVE the existing structure and phrasing** - only modify incorrect descriptions or values
4. Make **minimal changes** - update only what is factually wrong based on the screenshot
5. Keep accurate parts unchanged to enable easy comparison between old and new versions
6. The screenshot is the SINGLE SOURCE OF TRUTH - all text must align with what's visible

**Response Format (JSON):**
{{
    "updated_observation": "Observation with ONLY incorrect parts corrected, keeping structure intact",
    "updated_thought": "Thought with ONLY incorrect parts corrected, keeping structure intact",
    "validation_reasoning": "List specific corrections made (e.g., 'Changed X from Y to Z')"
}}

**Important Guidelines:**
- **Preserve original structure and wording** wherever possible
- Only change specific incorrect values, names, numbers, or descriptions
- If the original is accurate, return it exactly as-is
- Make corrections surgical and precise for easy comparison
- In reasoning, clearly state what was changed from what to what
"""
        return prompt
    
    async def validate_step_async(
        self,
        screenshot_path: str | Path,
        observation: str,
        thought: str,
        task_id: str = "",
        step_number: int = 0,
        previous_step: dict = None,
        next_step: dict = None
    ) -> Dict[str, str]:
        """
        Validate observation and thought against screenshot using async API.
        Generates new content from scratch if observation and thought are empty.
        
        Args:
            screenshot_path: Path to the screenshot image
            observation: Original observation text (can be empty)
            thought: Original thought text (can be empty)
            task_id: Task identifier for logging
            step_number: Step number for logging
            previous_step: Previous step data for continuity
            next_step: Next step data for continuity
            
        Returns:
            Dictionary with updated_observation, updated_thought, and validation_reasoning
            
        Raises:
            ValueError: If both observation/thought are empty AND screenshot is None/missing
        """
        try:
            screenshot_path = Path(screenshot_path)
            
            # Check if screenshot exists
            if not screenshot_path.exists():
                if not observation.strip() and not thought.strip():
                    raise ValueError(
                        f"[{task_id} - Step {step_number}] Cannot generate content: "
                        f"Screenshot is missing and observation/thought are empty. "
                        f"Screenshot path: {screenshot_path}"
                    )
                raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")
            
            # Encode image
            is_generating = not observation.strip() and not thought.strip()
            mode = "Generating" if is_generating else "Validating"
            logger.info(f"[{task_id} - Step {step_number}] {mode} - Encoding screenshot...")
            image_base64 = encode_image_to_base64(screenshot_path)
            media_type = get_image_mime_type(screenshot_path)
            
            # Create prompt with context
            prompt = self._create_validation_prompt(
                observation, 
                thought,
                previous_step=previous_step,
                next_step=next_step
            )
            
            response = await self.client.messages.create(
                model=settings.anthropic_model,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )
            
            # Extract response
            response_text = response.content[0].text
            
            # Track token usage
            tokens_used = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
            
            # Parse JSON response
            import json
            import re
            
            try:
                result = json.loads(response_text)
                result["tokens_used"] = tokens_used
                return result
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks (common Claude behavior)
                # Pattern to match JSON in markdown code blocks
                json_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
                match = re.search(json_pattern, response_text, re.DOTALL)
                
                if match:
                    json_text = match.group(1)
                    try:
                        result = json.loads(json_text)
                        result["tokens_used"] = tokens_used
                        return result
                    except json.JSONDecodeError:
                        pass  # Will try recovery next
                
                # If still can't parse, try to recover partial JSON for generation mode
                if is_generating:
                    # Try to extract fields with regex
                    obs_match = re.search(r'"updated_observation":\s*"([^"]*(?:\\"[^"]*)*)"', response_text, re.DOTALL)
                    thought_match = re.search(r'"updated_thought":\s*"([^"]*(?:\\"[^"]*)*)"', response_text, re.DOTALL)
                    
                    if obs_match or thought_match:
                        recovered = {
                            "updated_observation": obs_match.group(1).replace('\\"', '"') if obs_match else "",
                            "updated_thought": thought_match.group(1).replace('\\"', '"') if thought_match else "",
                            "validation_reasoning": f"Recovered from incomplete API response",
                            "tokens_used": tokens_used
                        }
                        return recovered
                
                # Last resort: return original content with error message
                logger.warning(f"[{task_id} - Step {step_number}] Could not parse response")
                return {
                    "updated_observation": observation,
                    "updated_thought": thought,
                    "validation_reasoning": f"API returned non-JSON response: {response_text[:200]}",
                    "tokens_used": tokens_used
                }
        
        except Exception as e:
            logger.error(f"[{task_id} - Step {step_number}] Error validating step: {str(e)}")
            raise
    
    async def validate_multiple_steps(
        self,
        validation_requests: list[Dict]
    ) -> list[Dict]:
        """
        Validate multiple steps concurrently
        
        Args:
            validation_requests: List of dicts with screenshot_path, observation, thought, task_id, step_number, previous_step, next_step
            
        Returns:
            List of validation results
        """
        tasks = [
            self.validate_step_async(
                screenshot_path=req["screenshot_path"],
                observation=req["observation"],
                thought=req["thought"],
                task_id=req.get("task_id", ""),
                step_number=req.get("step_number", 0),
                previous_step=req.get("previous_step"),
                next_step=req.get("next_step")
            )
            for req in validation_requests
        ]
        
        logger.info(f"Processing {len(tasks)} validation requests concurrently...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
