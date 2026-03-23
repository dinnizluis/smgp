# Feature Specification: Automatic Categorization

**Feature Branch**: `004-auto-categorization`
**Created**: 2026-03-22
**Status**: Implemented

## User Scenarios & Testing

### User Story 1 - Infer category from transaction description (Priority: P1)

As the system owner, I want the system to automatically assign categories to transactions based on keyword and regex rules so that most transactions are categorized without manual effort.

**Why this priority**: Manual categorization of hundreds of transactions is impractical — automation is the core value.

**Independent Test**: Import transactions with descriptions like "IFOOD" or "UBER" and verify they are auto-categorized to "Alimentação" and "Transporte" respectively.

**Acceptance Scenarios**:

1. **Given** a transaction with description "IFOOD *Restaurante", **When** category inference runs, **Then** the category is set to "Alimentação".
2. **Given** a transaction with description "UBER TRIP", **When** category inference runs, **Then** the category is set to "Transporte".
3. **Given** a transaction with description "UNKNOWN VENDOR XYZ", **When** category inference runs, **Then** the category remains "Não categorizado".
4. **Given** a transaction with description "Supermercado Extra", **When** category inference runs, **Then** the category is set to "Supermercado".
5. **Given** two rules matching the same description with different priorities, **When** inference runs, **Then** the highest priority rule wins.

---

### User Story 2 - Load rules from JSON file (Priority: P1)

As the system owner, I want categorization rules stored in a JSON file so that I can add, edit, or remove rules without changing code.

**Why this priority**: Rules are the configuration layer — externalizing them enables iteration without code changes.

**Independent Test**: Modify `category_rules.json`, restart the app, and verify new rules take effect.

**Acceptance Scenarios**:

1. **Given** a `category_rules.json` with keyword rules, **When** loaded, **Then** rules are available for inference.
2. **Given** a `category_rules.json` with regex rules, **When** loaded, **Then** regex patterns are compiled and matched.
3. **Given** a missing `category_rules.json` file, **When** loading, **Then** an empty rule list is returned (no crash).

---

### User Story 3 - Remove category rules (Priority: P3)

As the system owner, I want to remove all rules associated with a category so that deleted categories don't leave orphan rules.

**Why this priority**: Housekeeping — needed when categories are reorganized.

**Independent Test**: Call `remove_category_rules("Transporte")` and verify no rules suggest that category.

**Acceptance Scenarios**:

1. **Given** 3 rules mapping to "Transporte", **When** `remove_category_rules("Transporte")` is called, **Then** all 3 rules are removed and the function returns 3.

---

### Edge Cases

- Transaction description with accents (e.g., "ALIMENTAÇÃO") → normalized before matching (accents removed, lowercased)
- Invalid regex pattern in rules → skipped gracefully, other rules still applied
- Empty description → no match, defaults to "Não categorizado"

## Requirements

### Functional Requirements

- **FR-001**: System MUST support two rule types: `keyword` (substring match) and `regex` (pattern match)
- **FR-002**: System MUST normalize transaction descriptions before matching (lowercase, strip whitespace, remove accents)
- **FR-003**: Rules MUST have a priority field — highest priority match wins
- **FR-004**: Rules MUST be loaded from `data/category_rules.json`
- **FR-005**: System MUST handle missing rules file gracefully (return empty list)
- **FR-006**: System MUST skip invalid regex patterns without crashing
- **FR-007**: System MUST support removing all rules for a given category name

### Key Entities

- **Category Rule**: pattern (string), category (string), type (keyword|regex), priority (int)
- **Category**: id, name — persisted in SQLite

## Success Criteria

- **SC-001**: 80%+ of common transactions are auto-categorized on first import
- **SC-002**: Rule changes in JSON take effect without code changes

## Implementation References

- Rules engine: `application/use_cases.py` → `load_category_rules()`, `infer_category_for_transaction()`, `_normalize_text()`
- Rule removal: `application/use_cases.py` → `remove_category_rules()`
- Rules data: `data/category_rules.json`
- Tests: `tests/test_categorization.py`, `tests/test_use_cases.py` → `test_normalize_text()`, `test_load_rules_missing()`, `test_infer_with_invalid_regex()`
