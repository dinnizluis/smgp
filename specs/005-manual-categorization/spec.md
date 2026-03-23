# Feature Specification: Manual Categorization

**Feature Branch**: `005-manual-categorization`
**Created**: 2026-03-22
**Status**: Implemented

## User Scenarios & Testing

### User Story 1 - Reassign transaction category (Priority: P1)

As the system owner, I want to manually change a transaction's category via the dashboard so that I can correct auto-categorization errors or assign categories the system couldn't infer.

**Why this priority**: Auto-categorization doesn't cover everything — manual override is essential for data accuracy.

**Independent Test**: Find an uncategorized transaction in the dashboard, assign it a category, and verify it persists after page reload.

**Acceptance Scenarios**:

1. **Given** a transaction categorized as "Não categorizado", **When** I select "Alimentação" from the dropdown and save, **Then** the transaction's category is updated to "Alimentação" in the database.
2. **Given** a transaction categorized as "Transporte", **When** I change it to "Compras", **Then** the category is updated and the change persists.
3. **Given** a non-existent transaction ID, **When** update_category is called, **Then** no rows are affected and the function returns `False`.

---

### User Story 2 - Bulk category reassignment (Priority: P2)

As the system owner, I want to select multiple transactions and assign them the same category in one action so that I can efficiently categorize batches of similar transactions.

**Why this priority**: One-by-one categorization is tedious when multiple transactions belong to the same category.

**Independent Test**: Select 5 uncategorized transactions, assign all to "Alimentação", and verify all 5 are updated.

**Acceptance Scenarios**:

1. **Given** 5 transactions selected in the dashboard, **When** I choose "Supermercado" and apply, **Then** all 5 transactions have category "Supermercado".

---

### User Story 3 - Delete a category (Priority: P3)

As the system owner, I want to delete a category so that obsolete categories are removed and their transactions revert to uncategorized.

**Why this priority**: Housekeeping for category management.

**Independent Test**: Delete category "Transporte" and verify all its transactions are set to NULL category.

**Acceptance Scenarios**:

1. **Given** a category "Transporte" with 10 associated transactions, **When** deleted, **Then** the category is removed and all 10 transactions have category_id set to NULL.
2. **Given** the delete operation, **When** completed, **Then** associated rules in `category_rules.json` are also removed.

---

### Edge Cases

- Trying to delete "Não categorizado" → should be prevented (it's the default)
- Creating a new category inline during reassignment → supported via "Criar nova" option in UI

## Requirements

### Functional Requirements

- **FR-001**: System MUST allow updating a transaction's category by transaction ID
- **FR-002**: `TransactionRepository.update_category()` MUST return `True` if a row was affected, `False` otherwise
- **FR-003**: System MUST support deleting a category and reassigning its transactions to NULL
- **FR-004**: Category deletion MUST also remove associated rules from `category_rules.json`
- **FR-005**: Dashboard MUST provide dropdown with existing categories + "Criar nova" option

### Key Entities

- **Transaction**: category_id field (FK to categories)
- **Category**: id, name (unique)

## Success Criteria

- **SC-001**: Category changes persist across dashboard reloads
- **SC-002**: Deleted category's transactions revert to uncategorized

## Implementation References

- Repository: `infrastructure/repositories.py` → `TransactionRepository.update_category()`, `CategoryRepository.delete_by_name()`
- Dashboard UI: `app/dashboard.py` → category management expander
- Tests: `tests/test_repositories_update_category.py`, `tests/test_more_coverage.py`
