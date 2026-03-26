# Changelog

## v0.2.0 - LLM Refactor & Dashboard Improvements

### Changed
- Simplified focus states from three (ALIGNED, EXPLORING, DRIFTING) to two: **FOCUSED** and **DRIFTING**
- Replaced two-prompt LLM flow (classify + assess) with a single unified prompt
  - Removed per-page activity classification (no more BROWSING/IMPLEMENTATION categories)
  - State assessment now uses page titles and content directly — goal-aware by design
  - Returns `relevant_percent` and `irrelevant_percent` instead of category breakdown
- Notification cooldown changed from check-based to time-based (2 minutes)
- Config structure simplified — no more nested `llm.config`, provider fields are flat
- Default provider changed from AWS Bedrock to **Ollama** (`qwen2.5:latest`)
- `DEFAULT_CONFIG` removed from `config.py` — relies on `config.json` only
- Default config auto-created at `~/.drift-watcher/config.json` on first run from `config.default.json`

### Added
- Dashboard session history sidebar (grouped by date, collapsible)
- "Back to Live" button when viewing past sessions
- Dark/light theme toggle
- Relevant vs irrelevant activity breakdown on dashboard
- Auto-kill server on agent stop (Ctrl+C); `--keep-server` flag to override
- `config.default.json` — default config shipped with package
- `config.examples.json` — provider config reference
- Provider selection via `llm.provider` field in config (`ollama` or `bedrock`)
- CSS and JS extracted to separate files (`dashboard.css`, `dashboard.js`)

### Fixed
- ActivityProcessor was creating its own LLMReasoner defaulting to Bedrock
- OllamaClient parameter mismatch (`model_id` vs `model`)
- Dashboard CSS/JS not included in installed package (`pyproject.toml` updated)
- Config deep merge causing provider field leakage between defaults and user config
- Removed `drift-watcher-switch` command (no longer needed — edit config directly)

---

## v0.1.0 - System-Wide Installation

### Added
- System-wide installation via `pip install .`
- CLI commands: `drift-watcher`, `drift-watcher-server`, `drift-watcher-goal`
- Auto-start event server when running agent
- Centralized data directory at `~/.drift-watcher/`
- Proper Python package structure with `pyproject.toml`

### Changed
- Renamed `src/` to `drift_watcher/` for proper package naming
- Moved documentation to `docs/` directory
- Moved assets to `assets/` directory
- Simplified LLM reasoning (removed redundant relevance check)
- Moved prompts to class-level constants in `LLMReasoner`
