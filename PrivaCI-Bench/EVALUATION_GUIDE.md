# HOW TO EVALUATE A MODEL ON PRIVACI-BENCH BENCHMARK

PrivaCI-Bench evaluates LLMs on their ability to reason about privacy regulations using Contextual Integrity (CI) theory. It provides two main evaluation tasks.

## OVERVIEW: THE TWO EVALUATION TASKS

### TASK 1: DIRECT ANSWER (Case Classification)
```
Script:      direct_answer.py
Dataset:     Case dataset (74+ cases per regulation)
Task:        Given a privacy case, classify as:
             (A) Prohibited by regulation
             (B) Permitted by regulation
             (C) Not related to regulation

Data Size:   GDPR (3137), HIPAA (214), AI_ACT (3000), ACLU (69), CCPA (74)
Metric:      Accuracy (% correct classifications)

Example:
  INPUT:  "Meta stored user passwords"
          Regulations: Article 32, Article 33
  OUTPUT: Choice: A. Prohibited
  EVAL:   Check if matches expected violation
```

### TASK 2: ATTRIBUTE EXTRACTION (MCQ)
```
Script:      MCQ_qwq.py
Dataset:     MCQ dataset (3700 easy + 7400 medium + 3700 hard per regulation)
Task:        Given a scenario, identify contextual integrity attribute:
             - Who (sender/recipient/subject)
             - What (information type)
             - Why (purpose)
             - How (consent form)

Data Size:   14,800 MCQs per regulation across 3 difficulties
Metric:      Accuracy (% correct attribute selections)

Example:
  INPUT:  Scenario: "Company collects user browsing history for personalized ads"
          Attribute: recipient
          Choices: A. Company, B. User, C. Analytics firm, D. Ad network
  OUTPUT: Choice: D
  EVAL:   Check if matches correct answer
```

## PREPARATION: BEFORE YOU RUN EVALUATION

### 1. CONFIGURE config.py

Open `PrivaCI-Bench/config.py` and set:

```python
# For local model evaluation
HF_TOKEN = "your_huggingface_token"          # Get from https://huggingface.co/settings/tokens
HF_HOME = "/path/to/cache"                   # Optional: cache directory for models

# For API-based evaluation
api_key = "your_openai_key"                  # For OpenAI/API-compatible services
api_model = "gpt-4o-mini"                    # Default API model
```

**Note**: Paths (HF_cases_path, HF_KBs_path, HF_MCQ_path) are auto-detected.

### 2. VERIFY DATASETS ARE LOADED

Test that datasets are accessible:

```bash
python -c "
from utils import get_local_case_dataset, get_local_KB_dataset
cases = get_local_case_dataset()
kbs = get_local_KB_dataset()
print('Available case domains:', list(cases.keys()))
print('Available KB domains:', list(kbs.keys()))
"
```

Should output: `GDPR, HIPAA, AI_ACT, ACLU, CCPA`

## EVALUATION METHOD 1: DIRECT ANSWER (CASE-BASED EVALUATION)

This tests: **Can the model classify privacy cases correctly?**

### Command Syntax

```bash
python direct_answer.py \
  --log_path <log_file> \
  --model <model_id> \
  --domains <regulations> \
  [--prompt_template <template>] \
  [--api_name <api_type>] \
  [--api_model <model>] \
  [--api_token <token>] \
  [--seed 42]
```

### Examples

**Basic Example - Local Model:**
```bash
python direct_answer.py \
  --log_path logs/ccpa_test.txt \
  --model Qwen/Qwen2.5-7B-Instruct \
  --domains CCPA
```

**Basic Example - API Model:**
```bash
python direct_answer.py \
  --log_path logs/ccpa_gpt.txt \
  --domains CCPA \
  --api_name gpt-4o-mini \
  --api_model gpt-4o-mini \
  --api_token sk-xxxxxx
```

**Multiple Regulations:**
```bash
python direct_answer.py \
  --log_path logs/all_regulations.txt \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --domains GDPR+HIPAA+CCPA+AI_ACT
```

### Ablation Studies (Testing Different Prompts)

**Baseline (no context):**
```bash
python direct_answer.py \
  --log_path logs/ablation/baseline.txt \
  --model Qwen/Qwen2.5-7B-Instruct \
  --domains CCPA \
  --prompt_template prompts/direct_answer_prompt.txt
```

**With CI Elements (sender/recipient/purpose etc):**
```bash
python direct_answer.py \
  --log_path logs/ablation/with_ci.txt \
  --model Qwen/Qwen2.5-7B-Instruct \
  --domains CCPA \
  --prompt_template prompts/direct_answer_prompt_with_ci_element.txt
```

**With CI + Regulations:**
```bash
python direct_answer.py \
  --log_path logs/ablation/with_ci_law.txt \
  --model Qwen/Qwen2.5-7B-Instruct \
  --domains CCPA \
  --prompt_template prompts/direct_answer_prompt_with_ci_element_with_law.txt
```

### Important Parameters

| Parameter | Description |
|-----------|-------------|
| `--log_path` | Output file for results and logs |
| `--model` | HuggingFace model ID (e.g., `Qwen/Qwen2.5-7B-Instruct`) |
| `--domains` | Regulations to evaluate (GDPR, HIPAA, CCPA, AI_ACT, ACLU) |
| | Use '+' to combine: `GDPR+HIPAA+CCPA` |
| `--prompt_template` | Which prompt to use (see templates below) |
| `--api_name` | If using API: 'gpt-4o-mini', 'deepseek', etc. |
| `--api_model` | API model name |
| `--api_token` | API authentication token |
| `--seed` | Random seed (default: 42) |
| `--temperature` | Sampling temperature (0.2 = deterministic, default) |
| `--generation_round` | Retry attempts if parse fails (default: 10) |
| `--max_new_tokens` | Max output tokens from model (default: 1024) |

## EVALUATION METHOD 2: MCQ (ATTRIBUTE EXTRACTION)

This tests: **Can the model extract contextual integrity attributes correctly?**

### Command Syntax

```bash
python MCQ_qwq.py \
  --log_path <log_file> \
  --model <model_id> \
  --strategy <difficulty> \
  [--sample <num_questions>] \
  [--api_name <api_type>] \
  [--api_token <token>]
```

### Examples

**Easy Difficulty:**
```bash
python MCQ_qwq.py \
  --log_path logs/mcq_easy.txt \
  --model Qwen/Qwen2.5-7B-Instruct \
  --strategy easy
```

**Medium Difficulty (Most Common):**
```bash
python MCQ_qwq.py \
  --log_path logs/mcq_medium.txt \
  --model Qwen/Qwen2.5-7B-Instruct \
  --strategy medium
```

**Hard Difficulty:**
```bash
python MCQ_qwq.py \
  --log_path logs/mcq_hard.txt \
  --model Qwen/Qwen2.5-7B-Instruct \
  --strategy hard
```

**Sample Subset (Faster Testing):**
```bash
python MCQ_qwq.py \
  --log_path logs/mcq_sample.txt \
  --model Qwen/Qwen2.5-7B-Instruct \
  --strategy medium \
  --sample 500
```

**Using API:**
```bash
python MCQ_qwq.py \
  --log_path logs/mcq_gpt.txt \
  --api_name gpt-4o-mini \
  --api_model gpt-4o-mini \
  --api_token sk-xxxxxx \
  --strategy hard
```

### Important Parameters

| Parameter | Description |
|-----------|-------------|
| `--log_path` | Output file for results |
| `--model` | HuggingFace model ID |
| `--strategy` | Difficulty: 'easy' (3700), 'medium' (7400), 'hard' (3700) |
| `--sample` | Limit questions (0 = all). Use for faster testing. |
| `--api_name` | API type if using cloud models |
| `--api_model` | API model name |
| `--api_token` | API authentication token |
| `--seed` | Random seed (default: 42) |
| `--temperature` | Sampling temperature (default: 0.2) |
| `--generation_round` | Retry attempts (default: 10) |

## PROMPT TEMPLATES (Direct Answer only)

The paper tests different prompt formulations:

### 1. Baseline (Minimal Information)

**Template:** `prompts/direct_answer_prompt.txt`

```
Determine the relationship between the provided event and the {domain} 
regulations. You have three options:
(A) The event is prohibited
(B) The event is permitted
(C) The event is not related

Event: {event}
```

**Use Case:** Tests raw reasoning without domain context

### 2. With Contextual Integrity (Domain Context)

**Template:** `prompts/direct_answer_prompt_with_ci_element.txt`

```
...along with Contextual Integrity elements:
- Sender: {sender}, Role: {sender_role}
- Recipient: {recipient}, Role: {recipient_role}
- Subject: {subject}, Role: {subject_role}
- Information Type: {information_type}
- Purpose: {purpose}
- Consent Form: {consent_form}
```

**Use Case:** Tests reasoning with structured domain knowledge

### 3. With CI + Regulation Snippets (Full Context)

**Template:** `prompts/direct_answer_prompt_with_ci_element_with_law.txt`

```
All of above PLUS:

Reference Law Clauses
{domain} regulations: {clauses}
```

**Use Case:** Tests reasoning with explicit regulation content

## UNDERSTANDING THE OUTPUT

When you run an evaluation, two files are created:

### 1. Detailed Log: `logs/your_log.txt`

Contains:
- Command line arguments used
- Per-case evaluation details:
  - Domain and case index
  - Model's parsed decision
  - Expected answer
  - Whether prediction was correct
- Running accuracy after each case
- Final accuracy per domain

**Example entry:**
```
=== domain: CCPA --- case: 0
sample_id: 0 --- result:True --- answer: prohibit
{'decision': 'A. Prohibited', 'explanation': '...'}

domain: CCPA --- num_sample: 74 --- accuracy:0.81
```

### 2. Results Summary: `logs/your_log_results.txt`

Contains only the final accuracy per domain:

```
domain: CCPA --- num_sample: 74 --- accuracy:0.81
domain: GDPR --- num_sample: 3137 --- accuracy:0.78
```

### What the Accuracy Metric Means

```
Accuracy = Correct Predictions / Total Predictions

Examples:
- 0.85 = Model correctly classified 85% of cases
- 0.50 = Model got 50% correct (random guessing for 3-class is ~33%)
- 0.95 = Model achieved 95% accuracy (near human-level)
```

## COMMON MODEL CHOICES & RECOMMENDATIONS

### Local Models (Open-Source)

**Qwen/Qwen2.5-7B-Instruct (RECOMMENDED)**
- Pros: Fast, good reasoning, efficient
- Cons: ~7B params, needs GPU
- Expected accuracy: 50-70%

**meta-llama/Llama-3.1-8B-Instruct**
- Pros: Well-known, solid reasoning
- Cons: Similar size/speed to Qwen
- Expected accuracy: 50-65%

**Qwen/QwQ-32B-Preview**
- Pros: Superior reasoning with CoT
- Cons: Needs more compute (32B)
- Expected accuracy: 60-75%

### API-Based Models (Cloud)

**gpt-4o-mini (RECOMMENDED FOR ACCURACY)**
- Pros: Highest accuracy, no local setup
- Cons: API costs, rate limits
- Expected accuracy: 75-90%
- Cost: ~$0.15 per 1000 input tokens

**deepseek-r1**
- Pros: Strong reasoning, reasonable cost
- Cons: API availability varies
- Expected accuracy: 70-85%

## QUICK START: EVALUATE CCPA IN 5 MINUTES

### Option A: Quick Test with Local Model

```bash
cd /Users/meerakumar/Desktop/Carnegie\ Mellon/10-743/PrivaCI-Bench
python direct_answer.py \
  --log_path logs/ccpa_quick.txt \
  --model Qwen/Qwen2.5-7B-Instruct \
  --domains CCPA

# Check result:
cat logs/ccpa_quick_results.txt
```

### Option B: Quick Test with API (Fastest)

```bash
python direct_answer.py \
  --log_path logs/ccpa_api.txt \
  --domains CCPA \
  --api_name gpt-4o-mini \
  --api_model gpt-4o-mini \
  --api_token sk-xxxxxx
```

**Note:** Requires OpenAI API key and credits

### Option C: MCQ Test (Easier, Faster)

```bash
python MCQ_qwq.py \
  --log_path logs/ccpa_mcq.txt \
  --model Qwen/Qwen2.5-7B-Instruct \
  --strategy easy \
  --sample 100
```

This evaluates on 100 easy questions only (~2-3 minutes)

## ANALYZING & COMPARING RESULTS

### Comparing Models

Run same evaluation with different models, then compare final accuracies:

```
Model A (Qwen):       0.62
Model B (Llama):      0.59
Model C (GPT-4o):     0.81

Conclusion: GPT-4o significantly outperforms open-source models
```

### Ablation Analysis (Prompt Engineering Impact)

Run model with 3 different prompts and compare:

```
Baseline (no context):       0.45
+ CI elements:               0.58 (+13% improvement)
+ CI + Regulation content:   0.71 (+26% improvement)

Conclusion: Providing regulation content is critical
```

### Domain Comparison

Run same model on multiple domains:

```
GDPR:    0.76 (most comprehensive regulation)
HIPAA:   0.68 (medical-specific)
CCPA:    0.64 (simpler, newer)
AI_ACT:  0.60 (complex, emerging)

Conclusion: GDPR is best understood, AI_ACT is hardest
```

### Difficulty Analysis (MCQ)

Test same model on different MCQ difficulties:

```
Easy:     0.78
Medium:   0.65
Hard:     0.48

Conclusion: Model struggles with edge cases
```

## TROUBLESHOOTING

### ISSUE: "CUDA out of memory"

**Solution 1:** Use smaller model
```bash
--model Qwen/Qwen2.5-7B-Instruct  # instead of 32B
```

**Solution 2:** Use API instead (no GPU needed)
```bash
--api_name gpt-4o-mini
```

**Solution 3:** Limit GPUs
```bash
export CUDA_VISIBLE_DEVICES=0
```

### ISSUE: "Model not found" or "401 Unauthorized"

**Solution:**
1. Check HF_TOKEN in config.py
2. Run: `huggingface-cli login`
3. Get token from: https://huggingface.co/settings/tokens

### ISSUE: "Dataset not found"

**Solution:**
1. Verify HF_cache/ exists with subdirectories
2. Run: `python -c "from utils import get_local_case_dataset; get_local_case_dataset()"`
3. Check path in config.py matches actual location

### ISSUE: "Cannot parse model output"

**Solution:**
1. Increase `--generation_round` (try 20 instead of 10)
2. Lower `--temperature` (try 0.1 for more deterministic)
3. Check prompt template exists at specified path

### ISSUE: "API rate limit exceeded"

**Solution:**
1. Use `--sample` to evaluate fewer questions
2. Add delay between requests (modify code if needed)
3. Use local models instead
4. Wait before retrying

## SUMMARY: MINIMAL WORKING EXAMPLE

1. **Edit config.py:**
   ```python
   HF_TOKEN = "your_token"
   ```

2. **Run CCPA case-based evaluation:**
   ```bash
   python direct_answer.py \
     --log_path logs/test.txt \
     --model Qwen/Qwen2.5-7B-Instruct \
     --domains CCPA
   ```

3. **Check results:**
   ```bash
   cat logs/test_results.txt
   ```

4. **Expected output:**
   ```
   domain: CCPA --- num_sample: 74 --- accuracy:0.60-0.70
   ```

That's it! You're now evaluating models on PrivaCI-Bench.
