# SMGP Constitution

## Core Principles

### I. Layered Architecture

The system follows a modular layered architecture with strict dependency direction:

```
Streamlit (app/) → Application (application/) → Domain (domain/) + Importers (importers/) → Infrastructure (infrastructure/) → SQLite
```

- **UI layer** (`app/`) handles presentation only. It MUST NOT access the database directly.
- **Application layer** (`application/`) orchestrates use cases and business logic.
- **Domain layer** (`domain/`) defines models and pure business rules. It MUST NOT depend on SQLite or any infrastructure detail.
- **Importers** (`importers/`) transform external data into domain objects. They MUST NOT persist data — they only parse and return.
- **Infrastructure layer** (`infrastructure/`) isolates all SQL and database access behind repositories.

### II. Simplicity First

This is a solo personal project. Avoid over-engineering at all costs:

- No ORMs — use raw SQL via repositories
- No microservices — single-process application
- No Docker — local execution only
- No abstractions for hypothetical future requirements
- Prefer flat, readable code over clever patterns
- Functions should be small and clear
- Code readability > code cleverness

### III. Test-First for New Features (NON-NEGOTIABLE)

All new features MUST follow test-first development:

1. Write acceptance tests derived from spec scenarios
2. Verify tests fail (Red)
3. Implement the minimum code to pass (Green)
4. Refactor if needed

Tests use real SQLite databases (via `tmp_path`), not mocks. This ensures integration correctness.

### IV. Specification as Source of Truth

- Every feature has a spec in `specs/NNN-feature-name/spec.md`
- Specs define WHAT and WHY, not HOW
- Acceptance scenarios in specs map directly to test functions
- When behavior changes, update the spec first, then the code

### V. Data Integrity

- Deduplication is mandatory: same date + amount + description = duplicate
- All transactions get a default category ("Não categorizado") if unassigned
- Negative amounts = expenses, positive amounts = income
- Dates are always stored in ISO 8601 format (YYYY-MM-DD)

## Technology Stack

- **Language**: Python 3.10+
- **UI**: Streamlit
- **Database**: SQLite (local file at `data/smgp.db`)
- **Data Processing**: Pandas
- **Testing**: pytest + pytest-cov
- **Charts**: Altair
- **PDF Parsing**: pdfplumber

No additional frameworks, ORMs, or infrastructure tools unless explicitly justified.

## Development Workflow

1. **New feature**: Write spec (`/speckit.specify`) → Plan (`/speckit.plan`) → Tasks (`/speckit.tasks`) → Implement (`/speckit.implement`)
2. **Bug fix**: Update spec acceptance scenario → Fix code → Verify test
3. **Refactor**: Check spec → Refactor code → All spec scenarios still pass
4. **All changes**: Must pass `pytest` before completion

## Code Conventions

- Source code: English
- Domain terms (category names, UI labels): Portuguese (product language)
- Type hints on all function signatures
- Repository classes isolate all SQL — no raw SQL outside `infrastructure/`
- Importers return `List[Transaction]` — caller decides what to do with them

## Governance

This constitution governs all development on SMGP. Amendments require:

- Documented rationale
- Review of impact on existing specs and code

**Version**: 1.0.0 | **Ratified**: 2026-03-22 | **Last Amended**: 2026-03-22
