# TASK-001: Project Setup

**Status**: todo
**Priority**: high

## Description
Initialize the Python package with pyproject.toml, directory structure, and basic configuration.

## Acceptance Criteria
- [ ] Create `pyproject.toml` with uv/pip compatible config
- [ ] Set up `src/pykabu_calendar/` package structure
- [ ] Add required dependencies: pykabutan, requests, beautifulsoup4, pandas, lxml
- [ ] Add optional dependency groups: `[dev]`, `[llm]`, `[browser]` (if needed later)
- [ ] Create `__init__.py` with version and public API exports
- [ ] Verify `uv pip install -e .` works

## Notes
- Use `uv` for package management
- Python 3.11+ required
- Follow src layout convention
