# Changelog

## v0.1.0 - System-Wide Installation

### Added
- System-wide installation via `pip install .`
- CLI commands: `drift-watcher`, `drift-watcher-server`, `drift-watcher-goal`, `drift-watcher-switch`
- Auto-start event server when running agent
- Interactive quit prompt to stop server
- Centralized data directory at `~/.drift-watcher/`
- Proper Python package structure with `pyproject.toml`

### Changed
- Renamed `src/` to `drift_watcher/` for proper package naming
- Moved documentation to `docs/` directory
- Moved assets to `assets/` directory
- Simplified LLM reasoning (removed redundant relevance check)
- Moved prompts to class-level constants in `LLMReasoner`

### Improved
- Cleaner root directory structure
- Single command to start everything: `drift-watcher --goal "..."`
- Better user experience with auto-start and quit options
- Organized documentation and assets

### Backwards Compatible
- All legacy scripts still work (`main.py`, `run_server.py`, etc.)
- Development workflow unchanged
- Existing data files compatible
