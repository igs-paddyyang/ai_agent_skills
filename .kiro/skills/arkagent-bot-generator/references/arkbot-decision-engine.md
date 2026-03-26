# Decision Engine + Skill Runtime 實作要點

本文件涵蓋 Decision Engine（決策引擎層）、Skill Runtime（技能執行層）與 Integration（整合層）的實作細節。

---

## 1. Skill Metadata Schema（skill.json）

每個 Skill Package 必須包含 `skill.json`，讓 Registry 能自動發現與載入：

```json
{
  "skill_id": "string (唯一識別，snake_case)",
  "intent": "string (DASHBOARD | RESEARCH | CASUAL)",
  "description": "string (給 LLM 理解的自然語言描述，20-50 字)",
  "examples": ["string (使用者可能的輸入範例，3-5 個)"],
  "required_params": ["string"],
  "optional_params": ["string"],
  "tags": ["string (關鍵字標籤，用於 Rule Match)"],
  "priority": "number (fallback 排序，數字越大優先級越高)",
  "enabled": "boolean (灰度控制開關)"
}
```

必填欄位：skill_id, intent, description, examples, required_params
選填欄位：optional_params, tags, priority, enabled（預設 true）

### 範例 skill.json

```json
{
  "skill_id": "web_scraper",
  "intent": "RESEARCH",
  "description": "爬取指定網頁並產出結構化摘要，支援多種網站格式",
  "examples": ["幫我爬取這個網頁", "分析這個網站的內容", "摘要這篇文章"],
  "required_params": ["url"],
  "optional_params": ["format"],
  "tags": ["scrape", "爬取", "網頁", "摘要"],
  "priority": 80,
  "enabled": true
}
```

### Skill Package 結構

```
{skill_name}/
├── skill.json        # Skill Metadata（Registry 用）
├── skill.py          # 主程式（必須有 run() 方法）
├── config.json       # Skill 設定（選用）
└── tests/            # 測試（開發階段用，runtime 不需要）
```

## 2. SkillRegistry（src/skill_registry.py）

掃描 `skills/` 目錄，載入所有 skill.json：

```python
class SkillRegistry:
    def __init__(self, skill_dir: str):
        """掃描 skill_dir 下所有子目錄的 skill.json"""
        self.skills = {}  # skill_id → metadata dict
        self._load_all(skill_dir)

    def _load_all(self, skill_dir):
        """遍歷子目錄，載入 skill.json，缺欄位跳過 + log 警告"""

    def filter_by_intent(self, intent: str) -> list:
        """回傳 intent 匹配且 enabled=True 的 Skill 列表"""

    def get_skill(self, skill_id: str) -> dict | None:
        """依 skill_id 取得 metadata"""
```

載入錯誤處理：
- 缺少必填欄位 → 跳過該 Skill，log 警告
- JSON 解析失敗 → 跳過，log 警告
- skill_id 重複 → log 錯誤，取第一個

支援 in-memory 模式（方便測試）：
```python
registry = SkillRegistry(skill_dir=None)
registry.skills = {"test_skill": {...}}  # 直接注入
```

## 3. SkillResolver（src/skill_resolver.py）

三階段決策引擎，從候選 Skill 中選出最適合的一個：

```python
class SkillResolver:
    def __init__(self, registry: SkillRegistry, llm_client=None):
        self.registry = registry
        self.llm_client = llm_client

    async def resolve(self, user_input: str, intent: str, state=None) -> dict | None:
        """主流程：取候選 → Rule Match → LLM Select → Fallback"""
        candidates = self.registry.filter_by_intent(intent)
        if not candidates:
            return None

        # 階段 1：Rule Match
        result = self._rule_match(user_input, candidates)
        if result:
            return {"skill_id": result["skill_id"], "reason": f"tag 命中", "method": "rule"}

        # 階段 2：LLM Select
        result = await self._llm_select(user_input, candidates)
        if result:
            return result

        # 階段 3：Fallback
        fallback = sorted(candidates, key=lambda s: s.get("priority", 0), reverse=True)[0]
        return {"skill_id": fallback["skill_id"], "reason": "fallback (priority)", "method": "fallback"}

    def _rule_match(self, text: str, candidates: list) -> dict | None:
        """遍歷候選 Skill 的 tags，case-insensitive 比對使用者輸入"""

    async def _llm_select(self, user_input: str, candidates: list) -> dict | None:
        """呼叫 LLM 精選，解析 JSON，驗證 skill_id 存在於候選中"""
```

### Resolver 輸出格式

```json
{
  "skill_id": "selected_skill_id",
  "reason": "選擇原因",
  "method": "rule | llm | fallback"
}
```

## 4. Skill Prompt 建構（src/skill_prompt.py）

```python
def build_prompt(user_input: str, candidates: list) -> str:
    """建構 LLM 選擇 Prompt"""
```

Prompt 結構：
1. 系統指令：你是 Skill 選擇器，從候選中選出最適合的
2. 使用者輸入
3. 候選 Skill 列表（每個包含 skill_id + description + examples）
4. 輸出格式要求：`{"skill_id": "xxx", "reason": "xxx"}`

控制 Prompt 長度：候選 > 10 個時，先用 Intent 過濾控制數量。

## 5. Hybrid Router（src/hybrid_router.py）

整合 Intent Router + Skill Resolver：

```python
async def route(user_input: str) -> dict:
    """
    完整路由流程：
    1. Intent Router 粗分類
    2. CASUAL → 直接回傳 {"skill_id": "chat_skill", "method": "fast_path"}
    3. 其餘 → SkillResolver.resolve()
    4. 無結果 → 回傳 None
    """
```

CASUAL 快速路徑的設計理由：閒聊不需要精選 Skill，直接進入 chat_skill 減少延遲。

## 6. Executor + Sandbox（src/executor.py）

動態載入 skill.py 並在隔離環境中執行：

```python
class Executor:
    def __init__(self, registry: SkillRegistry, skill_dir: str):
        self.registry = registry
        self.skill_dir = skill_dir

    async def execute(self, skill_id: str, user_input: str) -> dict:
        """
        1. 從 Registry 取得 metadata
        2. 動態載入 skill_dir/{skill_id}/skill.py
        3. 在 subprocess 中執行 run(user_input)
        4. 捕獲 stdout/stderr，設定 timeout 30 秒
        5. 回傳結果或錯誤訊息
        """
```

Sandbox 隔離要點：
- 使用 `subprocess` 執行，非 `importlib` 直接載入
- 捕獲 stdout/stderr
- timeout 30 秒，超時 `process.kill()` 強制終止
- Skill 拋出例外 → 捕獲並回傳錯誤訊息，主程序不受影響
- 無對應 Skill → 回傳友善提示：「目前沒有對應的 Skill，請透過 skill-creator 建立」

## 7. Integration — 升級 arkbot_core.py

將 Foundation 的 `process_message()` 升級為完整流程：

```python
async def process_message(user_input: str):
    """
    升級後流程：
    1. Hybrid Router 路由
    2. 結果為 chat_skill → 走原有 CASUAL 邏輯
    3. 結果為具體 skill_id → Executor 執行
    4. 結果為 None → 回傳友善提示
    5. 原有 Foundation 邏輯作為 fallback（向後相容）
    """
```

向後相容策略：
- 現有的 RESEARCH、REVENUE 等手動實作的邏輯保留
- 當 Registry 中有對應 Skill 時，優先走 Executor
- 當 Registry 中無對應 Skill 時，fallback 到原有邏輯
- 這樣現有功能不受影響，新 Skill 可以逐步接管

## 8. 測試要點

### Registry 測試（tests/test_skill_registry.py）
- 載入 3 個 skill.json，驗證 skills 長度
- `filter_by_intent("RESEARCH")` 回傳正確子集
- `enabled=false` 的 Skill 被過濾
- 缺欄位的 skill.json 被跳過

### Resolver 測試（tests/test_skill_resolver.py）
- Rule Match：「爬取網頁」命中 scrape tag
- Rule Match：「分析活動影響」回傳 None
- LLM Select：正常回傳合法 skill_id
- LLM Select：格式錯誤回傳 None
- Fallback：回傳 priority 最高者
- 候選為空：回傳 None

### Executor 測試（tests/test_executor.py）
- 正常執行：載入 skill.py 並呼叫 run()
- Sandbox 隔離：Skill 拋出例外不影響主程序
- Timeout：超過 30 秒強制終止
- 無 Skill：回傳友善提示

### 整合測試
- 端到端 CASUAL：直接回傳 chat_skill
- 端到端 RESEARCH：Intent=RESEARCH → 正確 skill_id
- 端到端無 Skill：回傳友善提示
- 向後相容：Foundation 功能不受影響
