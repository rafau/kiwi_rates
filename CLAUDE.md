# Claude Instructions for Kiwi Rates Project

## Startup

Always read `PROJECT_SPEC.md` when starting work on this project to understand:
- Current architecture and design decisions
- Implementation status
- Bank module pattern
- Data models and storage strategy

## Documentation Maintenance

**IMPORTANT:** Keep documentation in sync with code changes.

When making code changes, always update:

1. **PROJECT_SPEC.md** - Update relevant sections:
   - Repository Structure (if files added/moved/removed)
   - Implementation Status (if features completed)
   - Technical details (if architecture changes)

2. **README.md** - Update relevant sections:
   - Project Structure (if files added/moved/removed)
   - Setup instructions (if dependencies or steps change)
   - How It Works (if process changes)
   - Adding More Banks (if extension pattern changes)

## Development Principles

- Follow Test-Driven Development (TDD)
- Update existing tests when making changes
- Don't write code that isn't called by anything
- Ask clarifying questions when needed
- Keep bank-specific code in separate modules (`src/{bank}/`)
- Keep shared utilities bank-agnostic (`storage.py`, `html_generator.py`)

## Bank Module Pattern

When adding new banks, follow the established pattern:
- `src/{bank}/__init__.py` - Export main scraper function
- `src/{bank}/extractor.py` - Extract API keys/tokens
- `src/{bank}/parser.py` - Parse bank-specific data format
- `src/{bank}/scraper.py` - Orchestrate scraping process

Shared utilities work with all banks automatically.
