# Colab Notebook Generator

Generates updated Colab notebooks as per refinement task requirements using Claude's vision API to analyze screenshots and create observations/thoughts.

## 🚀 How to Get Started

### 1. Configure API Key

Copy the example environment file and add your Anthropic API key:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and add your API key:

```env
ANTHROPIC_API_KEY=your_actual_api_key_here
```

**Note:** Dependencies are automatically installed when you run the script.

### 2. Prepare Your Task Data

Check the sample task structure: `Input Data/task_84/`

For each task, you need:
- **events.json** - SFT events from activity monitor
- **task_XX.ipynb** - Base Colab notebook (unmodified)

### 3. Run the Script

From the project root directory:

```powershell
python .\process_task.py task_84
```

The script will generate:
- `task_84_updated.ipynb` - Updated notebook with observations/thoughts
- `validated_observation_thought.json` - Generated content
- `validation_report.json` - Detailed processing report

## ✅ For Best Results

1. **Perform the task using Activity Monitor**
   - Record all actions properly

2. **Create clean SFT events**
   - Remove unnecessary events
   - Keep only relevant actions

3. **Preview and save events**
   - Preview JSON in activity monitor
   - Copy into `events.json` file

4. **Download base Colab notebook**
   - Use strictly the **base version** (not modified)
   - Copy into your task folder

5. **Verify correlation**
   - Ensure events and Colab notebook are correlated
   - Modify if required to match

6. **Run and validate**
   - Execute the script
   - Review generated notebook

## 📁 Project Structure

```
Input Data/
  └── task_XX/
      ├── events.json              # SFT events (required)
      ├── task_XX.ipynb            # Base Colab notebook (required)
      ├── task_XX_updated.ipynb    # Generated output
      ├── validated_observation_thought.json
      └── validation_report.json
```


## ⚙️ Configuration

Default settings work out of the box. To customize, edit `config/settings.py` or `.env`:

```env
# Model settings
ANTHROPIC_MODEL=claude-sonnet-4-20250514
MAX_TOKENS=4096
TEMPERATURE=0

# Paths
INPUT_DIR=Input Data
OUTPUT_DIR=output

# Logging
LOG_LEVEL=INFO
```

## 📝 Notes

- Screenshots are auto-downloaded from events.json
- Claude analyzes each screenshot to generate observations/thoughts
- Continuity is maintained across steps
- All API calls are async for fast processing
- Token usage is tracked and reported

---

**Happy Validating! 🚀**

