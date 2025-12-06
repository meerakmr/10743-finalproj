# Running PrivaCI-Bench with Claude Sonnet

To run Claude models on PrivaCI-Bench, follow these steps:

## 1. Install Anthropic SDK

```bash
pip install anthropic
```

## 2. Run the Direct Answer evaluation with Claude

```bash
python direct_answer.py \
  --log_path logs/claude_results.txt \
  --api_name claude \
  --api_model claude-sonnet-4-20250514 \
  --api_token $ANTHROPIC_API_KEY \
  --domains 'GDPR+HIPAA+AI_ACT+CCPA'
```

## 3. Run the MCQ evaluation with Claude

```bash
python MCQ_qwq.py \
  --log_path logs/claude_mcq_results.txt \
  --api_name claude \
  --api_model claude-sonnet-4-20250514 \
  --api_token $ANTHROPIC_API_KEY \
  --strategy medium \
  --sample 1000
```

## Required Changes to agents.py

The agents.py file needs to be updated to support Claude. Replace the imports and AgentAction class initialization:

### Step 1: Add Anthropic import
Add `from anthropic import Anthropic` to the imports at the top of agents/agents.py

### Step 2: Add Claude_model class
Add this class after the OpenAI_model class definition:

```python
class Claude_model:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key)

    def compeletion(self, model: str, messages: list, max_retries: int, **kwargs):
        retries = 0
        while retries < max_retries:
            try:
                response = self.client.messages.create(
                    model=model,
                    messages=messages,
                    **kwargs
                )
                msg = response.content[0].text
                assert isinstance(msg, str), "The returned response is not a string."
                return msg  # Return the response if successful

            except Exception as e:
                # Catch all other exceptions
                print(f"Unexpected error: {e}. Retrying in 5 seconds...")
                retries += 1
                time.sleep(1)
        
        return ''  # Return an empty string if max_retries is exceeded
```

### Step 3: Update AgentAction.__init__
In the AgentAction.__init__ method, update the chatbot initialization around line 76:

Replace:
```python
if(not api_name):
    print('using HF chatbot to respond...')
    self.chatbot = chatbot
else:
    print('using OpenAI API to respond...')
    self.chatbot = OpenAI_model(api_key=self.api_token, api_name = self.api_name)
```

With:
```python
if(not api_name):
    print('using HF chatbot to respond...')
    self.chatbot = chatbot
elif(api_name == 'claude'):
    print('using Anthropic Claude API to respond...')
    self.chatbot = Claude_model(api_key=self.api_token)
else:
    print('using OpenAI API to respond...')
    self.chatbot = OpenAI_model(api_key=self.api_token, api_name = self.api_name)
```

## Environment Variable Setup

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

Or pass directly:
```bash
--api_token sk-ant-api03-...
```

## Available Claude Models

- `claude-opus-4-1` - Most capable
- `claude-sonnet-4-20250514` - Balanced (recommended)
- `claude-3-5-sonnet-20241022` - Previous Sonnet version
- `claude-haiku-3-5-20241022` - Fastest/cheapest

## Example Commands

### Test on a subset (5 samples from easy MCQs)
```bash
python MCQ_qwq.py \
  --log_path logs/test_claude.txt \
  --api_name claude \
  --api_model claude-sonnet-4-20250514 \
  --api_token $ANTHROPIC_API_KEY \
  --strategy easy \
  --sample 5
```

### Run on medium difficulty (1000 questions)
```bash
python MCQ_qwq.py \
  --log_path logs/claude_medium_1k.txt \
  --api_name claude \
  --api_model claude-sonnet-4-20250514 \
  --api_token $ANTHROPIC_API_KEY \
  --strategy medium \
  --sample 1000
```

### Run case-based evaluation on all regulations
```bash
python direct_answer.py \
  --log_path logs/claude_cases.txt \
  --api_name claude \
  --api_model claude-sonnet-4-20250514 \
  --api_token $ANTHROPIC_API_KEY \
  --domains 'GDPR+HIPAA+AI_ACT+CCPA+ACLU'
```

## Notes

- Claude API has rate limits; use `--max_retry` flag to control retries
- Temperature defaults to 0.2 for consistent results
- Max tokens defaults to 1024
- Costs approximately $0.003 per 1K tokens for Sonnet
