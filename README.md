# Screenshot Validator with LangChain & Anthropic

A LangChain-based project that validates and corrects LLM-generated observations and thoughts against screenshots using Anthropic's Claude API with vision capabilities.

## 🎯 Purpose

This tool takes:
- **Screenshots** (single source of truth - manually created)
- **LLM-generated observations** (text descriptions of screenshots)
- **LLM-generated thoughts** (reasoning/analysis text)

And returns:
- **Updated observations** aligned with actual screenshot content
- **Updated thoughts** corrected to match screenshot reality
- **Validation reasoning** explaining what changed and why

Perfect for validating AI-generated UI/UX analysis, testing documentation, or any workflow where screenshots are the ground truth.

## 📋 Features

✅ **Async Processing** - Validate multiple steps simultaneously for fast processing  
✅ **Vision-Powered** - Uses Claude's vision API to analyze screenshots  
✅ **LangChain Integration** - Leverages LangChain for orchestration  
✅ **Structured Output** - Returns validated JSON matching input format  
✅ **Auto-Generation** - Generate observations/thoughts from scratch when empty  
✅ **Continuity Aware** - Maintains context with previous/next steps  
✅ **Token Tracking** - Records API usage for cost monitoring  
✅ **Detailed Logging** - Rich console output and file logging  
✅ **Error Handling** - Graceful handling of missing files or API errors  
✅ **Batch Processing** - Process entire task folders or individual tasks  

## 🏗️ Project Structure

```
Langchain/
├── .env                          # Your API keys (create from .env.example)
├── requirements.txt              # Python dependencies
├── README.md                     # Full documentation
├── config/
│   └── settings.py              # Configuration
├── src/
│   ├── models/
│   │   └── schemas.py       # Data models
│   ├── services/
│   │   ├── anthropic_service.py  # Async API calls
│   │   └── validator_service.py  # Orchestration
│   ├── utils/
│   │   ├── image_handler.py # Image encoding
│   │   └── logger.py        # Logging
│   └── main.py              # Main entry point
├── examples/
│   └── usage_example.py     # Usage examples
├── Input Data/
│   ├── Json/
│   │   └── task_84.json     # Input JSON files
│   └── Screenshots/
│       └── task_84/         # Screenshots folder
│           ├── 1.png
│           ├── 2.png
│           └── ...
└── output/                  # Generated outputs
    ├── task_84_validated.json   # Validated observations/thoughts
    ├── task_84_report.json      # Detailed validation report
    └── validation.log           # Log file
```

## 🚀 Setup

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file from the template:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and add your Anthropic API key:

**Note:** You can also activate the virtual environment:
```powershell
.\venv\Scripts\Activate.ps1
```

```env
ANTHROPIC_API_KEY=your_actual_api_key_here
```

### 3. Prepare Your Data

**Input JSON Format** (`Input Data/Json/task_84.json`):
```json
{
    "step_1": {
        "observation": "The screen shows...",
        "thought": "I need to determine..."
    },
    "step_2": {
        "observation": "",
        "thought": ""
    }
}
```

**Note:** Empty observations/thoughts will be **generated from scratch** based on the screenshot while maintaining continuity with adjacent steps!

**Screenshots Structure**:
```
Input Data/Screenshots/task_84/
├── 1.png   # Corresponds to step_1
├── 2.png   # Corresponds to step_2
└── ...
```

## 💻 Usage

### Validate All Tasks

Process all tasks in the `json/` directory:

```powershell
python -m src.main
```

### Validate Specific Task

Process a single task by ID:

```powershell
python -m src.main task_84
```

### Programmatic Usage

```python
import asyncio
from src.services.validator_service import ValidatorService

async def validate():
    validator = ValidatorService()
    result = await validator.validate_task("task_84")
    print(f"Validated {result.successful_validations}/{result.total_steps} steps")

asyncio.run(validate())
```

### Advanced Usage

See `examples/usage_example.py` for more examples:

```powershell
python examples/usage_example.py
```

## 📤 Output

### Validated JSON (`output/task_84_validated.json`)

Matches input format with corrected content:

```json
{
    "step_1": {
        "observation": "Corrected observation aligned with screenshot...",
        "thought": "Corrected thought process..."
    },
    "step_2": {
        "observation": "...",
        "thought": "..."
    }
}
```

### Detailed Report (`output/task_84_report.json`)

Includes validation metadata:

```json
{
    "task_id": "task_84",
    "timestamp": "2025-12-03T10:30:00",
    "steps": {
        "step_1": {
            "step_number": 1,
            "original_observation": "...",
            "updated_observation": "...",
            "validation_reasoning": "Changed because...",
            "tokens_used": {
                "input_tokens": 1250,
                "output_tokens": 450
            },
            "success": true
        }
    }
}
```

## ⚙️ Configuration

Edit `config/settings.py` or `.env` to customize:

```env
# Model settings
ANTHROPIC_MODEL=claude-sonnet-4-20250514
MAX_TOKENS=4096
TEMPERATURE=0

# Paths
INPUT_JSON_DIR=Input Data/Json
SCREENSHOTS_DIR=Input Data/Screenshots
OUTPUT_DIR=output

# Logging
LOG_LEVEL=INFO
```

## 🔧 API Details

### ValidatorService

Main service for orchestrating validations:

```python
from src.services.validator_service import ValidatorService

validator = ValidatorService()

# Validate entire task
result = await validator.validate_task("task_84")

# Load task manually
task_data = validator.load_task_json("task_84")

# Prepare validation requests
requests = validator.prepare_validation_requests("task_84", task_data)
```

### AnthropicService

Direct API interaction:

```python
from src.services.anthropic_service import AnthropicService

service = AnthropicService()

# Single validation
result = await service.validate_step_async(
    screenshot_path="path/to/screenshot.png",
    observation="Original observation text",
    thought="Original thought text",
    task_id="my_task",
    step_number=1
)

# Batch validation
requests = [
    {
        "screenshot_path": "path/1.png",
        "observation": "...",
        "thought": "...",
        "task_id": "task1",
        "step_number": 1
    },
    # ... more requests
]
results = await service.validate_multiple_steps(requests)
```

## 📊 Example Output

When you run the validator, you'll see:

```
Screenshot Validator
Model: claude-sonnet-4-20250514
Output Directory: c:\Users\...\output

Validating task_84...

┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric              ┃ Value                         ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Total Steps         │ 15                            │
│ Successful          │ 15                            │
│ Failed              │ 0                             │
│ Total Tokens        │ 18750 in / 6825 out           │
│ Output File         │ output/task_84_validated.json │
└─────────────────────┴───────────────────────────────┘

Step Details:
  ✓ step_1 (Step 1)
    Original observation accurate, no changes needed
  ✓ step_2 (Step 2)
    Corrected button color description from blue to green...
  ...
```

## 🐛 Troubleshooting

**API Key Error**
```
Error: ANTHROPIC_API_KEY not set in environment
```
→ Make sure you created `.env` with your API key

**Screenshot Not Found**
```
FileNotFoundError: Screenshot not found: Input Data/Screenshots/task_84/1.png
```
→ Check that screenshots are in correct folder structure

**Import Errors**
```
ModuleNotFoundError: No module named 'anthropic'
```
## 📝 Notes

- Screenshots are treated as **single source of truth**
- Claude analyzes each screenshot and compares with text
- **Empty observations/thoughts** are generated from scratch using the screenshot
- Continuity is maintained with previous/next steps when generating
- Only factual discrepancies are corrected in validation mode
- Original intent/meaning is preserved when possible
- All API calls are async for maximum performance
- Token usage is tracked per step and in total
- **Error raised** if both observation/thought are empty AND screenshot is missingssible
- All API calls are async for maximum performance
- Token usage is tracked per step and in total

## 🎓 Examples

Check `examples/usage_example.py` for:
- Single task validation
- Batch processing
- Custom validation flows
- Error handling patterns
- Programmatic API usage

## 📜 License

MIT License - feel free to use and modify as needed.

## 🤝 Contributing

This is a custom project, but feel free to adapt it for your needs!

---

**Happy Validating! 🚀**
