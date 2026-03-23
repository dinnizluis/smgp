# Feature Specification: Duplicate Detection

**Feature Branch**: `003-duplicate-detection`
**Created**: 2026-03-22
**Status**: Implemented

## User Scenarios & Testing

### User Story 1 - Prevent duplicate transactions on import (Priority: P1)

As the system owner, I want the system to skip transactions that already exist in the database so that re-importing the same file doesn't create duplicates.

**Why this priority**: Data integrity is critical — duplicate transactions corrupt all analytics.

**Independent Test**: Import a CSV, then import the same CSV again and verify the transaction count doesn't change.

**Acceptance Scenarios**:

1. **Given** a transaction with date=2025-01-15, amount=-25.50, description="UBER TRIP" already in the database, **When** the same transaction is imported again, **Then** it is skipped and the count remains unchanged.
2. **Given** two transactions with same date and description but different amounts, **When** both are imported, **Then** both are inserted (they are not duplicates).
3. **Given** a fresh database with no transactions, **When** a CSV with 10 unique rows is imported, **Then** all 10 are inserted.
4. **Given** a CSV with 10 rows where 3 already exist in the database, **When** imported, **Then** only 7 new rows are inserted.

---

### Edge Cases

- Two transactions on the same day, same amount, same description (e.g., two identical coffee purchases) → treated as duplicate. This is an accepted trade-off for data integrity.
- Re-import after category change → not re-inserted (deduplication ignores category)

## Requirements

### Functional Requirements

- **FR-001**: System MUST check for duplicates before inserting a transaction
- **FR-002**: Duplicate is defined as matching: date + amount + description (RN-01 from Notion)
- **FR-003**: Duplicate check MUST be performed in `TransactionRepository.insert()` — returns `False` if duplicate
- **FR-004**: `TransactionRepository.is_duplicate()` MUST be available as a standalone check

### Key Entities

- **Transaction**: Deduplication key = (date, amount, description)

## Success Criteria

- **SC-001**: Re-importing the same 3-month CSV produces zero new rows
- **SC-002**: No duplicate transactions exist after multiple import cycles

## Implementation References

- Duplicate check: `infrastructure/repositories.py` → `TransactionRepository.is_duplicate()`, `TransactionRepository.insert()`
- Integration test: `tests/test_import_flow.py` → `test_import_flow_unique_count()`
- Repository test: `tests/test_repositories.py` → `test_repositories_insert_and_deduplicate()`
- More tests: `tests/test_repositories_more.py` → `test_transaction_duplicate_and_get_delete()`
