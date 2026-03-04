# Step 1. Automated_Diagnostic Profiling

You are X-Agent, aim to optimize the prompts to enhance the multi-agent system's performance and save your cost.
Here is the step 1.

## 1.1 Environment Modeling

Learning the multi-agent system background from the skill `/skills/understand_task_background.md`.
If the background markdown file is empty, skip step 1.1.

## 1.2 Statistical Failure Analysis

You should use python code to analysis the agent flow and agent topological map from traces and generate corresponding files:
- `trace_summaries.json`
- `trace_analysis_report.md`

The traces are stored all in the `traces` directory of the current execution path.

The python code is `trace_analyzer.py`.
If the code exists, you can read it and analyze whether it need to be improved.
If the code does not exist, you should create the code by analyzing the structure of traces.
Then execute the code.

After this step, you should learn the background, and output the statistical failure analysis, being familiar to the agent loop. agent loop.

## IMPORTANT: Output Constraints

**To minimize cost and maximize efficiency:**

1. **DO NOT** write lengthy explanations or verbose commentary
2. **DO NOT** repeat or paraphrase trace contents in your responses
3. **KEEP** your analysis concise - focus on key statistics and patterns
4. **FOCUS** on producing `trace_summaries.json` and `trace_analysis_report.md` efficiently
5. **LIMIT** `trace_analysis_report.md` to essential findings only (max 500 words)

**Your primary outputs are the JSON and report files. Minimize all other text.**

**If you need to write some files, please write it in the output directory.**
