# JSON Schema 定義

本文件定義 skill-creator 使用的 JSON schema。

---

## evals.json

定義技能的 eval。位於技能目錄中的 `evals/evals.json`。

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "使用者的範例提示詞",
      "expected_output": "預期結果描述",
      "files": ["evals/files/sample1.pdf"],
      "expectations": [
        "輸出包含 X",
        "技能使用了腳本 Y"
      ]
    }
  ]
}
```

**欄位：**
- `skill_name`：與技能前置資料匹配的名稱
- `evals[].id`：唯一整數識別碼
- `evals[].prompt`：要執行的任務
- `evals[].expected_output`：人類可讀的成功描述
- `evals[].files`：選用的輸入檔案路徑列表（相對於技能根目錄）
- `evals[].expectations`：可驗證的陳述列表

---

## grading.json

評分 agent 的輸出。位於 `<run-dir>/grading.json`。

```json
{
  "expectations": [
    {
      "text": "輸出包含名稱 'John Smith'",
      "passed": true,
      "evidence": "在逐字稿步驟 3 中找到"
    }
  ],
  "summary": { "passed": 2, "failed": 1, "total": 3, "pass_rate": 0.67 },
  "execution_metrics": { ... },
  "timing": { ... },
  "claims": [ ... ],
  "user_notes_summary": { ... },
  "eval_feedback": { ... }
}
```

**重要**：expectations 陣列必須使用 `text`、`passed`、`evidence` 欄位——檢視器依賴這些確切的欄位名。

---

## timing.json

執行的掛鐘計時。位於 `<run-dir>/timing.json`。

**如何捕捉**：subagent 任務完成時，通知包含 `total_tokens` 和 `duration_ms`。立即儲存——它們不會持久化到其他地方。

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

---

## benchmark.json

Benchmark 模式的輸出。位於 `benchmarks/<timestamp>/benchmark.json`。

```json
{
  "metadata": {
    "skill_name": "pdf",
    "skill_path": "/path/to/pdf",
    "executor_model": "claude-sonnet-4-20250514",
    "timestamp": "2026-01-15T10:30:00Z",
    "evals_run": [1, 2, 3],
    "runs_per_configuration": 3
  },
  "runs": [
    {
      "eval_id": 1,
      "eval_name": "Ocean",
      "configuration": "with_skill",
      "run_number": 1,
      "result": {
        "pass_rate": 0.85,
        "passed": 6,
        "failed": 1,
        "total": 7,
        "time_seconds": 42.5,
        "tokens": 3800,
        "tool_calls": 18,
        "errors": 0
      },
      "expectations": [
        {"text": "...", "passed": true, "evidence": "..."}
      ],
      "notes": []
    }
  ],
  "run_summary": {
    "with_skill": {
      "pass_rate": {"mean": 0.85, "stddev": 0.05, "min": 0.80, "max": 0.90},
      "time_seconds": {"mean": 45.0, "stddev": 12.0},
      "tokens": {"mean": 3800, "stddev": 400}
    },
    "without_skill": { ... },
    "delta": {
      "pass_rate": "+0.50",
      "time_seconds": "+13.0",
      "tokens": "+1700"
    }
  },
  "notes": []
}
```

**重要**：檢視器讀取這些確切的欄位名。使用 `config` 而非 `configuration`，或將 `pass_rate` 放在 run 頂層而非 `result` 下，會導致檢視器顯示空值。

---

## comparison.json

盲測比較者的輸出。位於 `<grading-dir>/comparison-N.json`。

```json
{
  "winner": "A",
  "reasoning": "...",
  "rubric": { "A": { ... }, "B": { ... } },
  "output_quality": { "A": { ... }, "B": { ... } },
  "expectation_results": { "A": { ... }, "B": { ... } }
}
```

---

## analysis.json

事後分析者的輸出。位於 `<grading-dir>/analysis.json`。

```json
{
  "comparison_summary": { "winner": "A", ... },
  "winner_strengths": [...],
  "loser_weaknesses": [...],
  "instruction_following": { "winner": { ... }, "loser": { ... } },
  "improvement_suggestions": [
    { "priority": "high", "category": "instructions", "suggestion": "...", "expected_impact": "..." }
  ],
  "transcript_insights": { ... }
}
```
