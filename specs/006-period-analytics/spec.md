# Feature Specification: Period Analytics

**Feature Branch**: `006-period-analytics`
**Created**: 2026-03-22
**Status**: Implemented

## User Scenarios & Testing

### User Story 1 - View weekly spending totals (Priority: P1)

As the system owner, I want to see the total spent in the current week and compare it with the previous week so that I understand my weekly spending trend.

**Why this priority**: Weekly comparison is the core insight — the MVP's primary value proposition.

**Independent Test**: Insert transactions across two weeks, query totals, and verify current/previous week sums and percentage change.

**Acceptance Scenarios**:

1. **Given** transactions totaling -500 this week and -400 last week, **When** week comparison is calculated, **Then** current=500, previous=400, pct_change=25%.
2. **Given** no transactions in the previous week, **When** comparison is calculated, **Then** previous=0 and pct_change=None (avoid division by zero).
3. **Given** today is Wednesday, **When** current week is calculated, **Then** it includes Monday through Sunday of the current ISO week.

---

### User Story 2 - View spending by period preset (Priority: P1)

As the system owner, I want to select predefined period presets (current month, last quarter, current year, etc.) so that I can quickly analyze spending across different time ranges.

**Why this priority**: Flexible period analysis extends the system beyond just weekly views.

**Independent Test**: Select "last_month" preset and verify the date range matches the previous calendar month.

**Acceptance Scenarios**:

1. **Given** today is 2025-03-15, **When** preset "current_week" is selected, **Then** the date range covers the current ISO week.
2. **Given** today is 2025-03-15, **When** preset "last_month" is selected, **Then** the range is 2025-02-01 to 2025-02-28.
3. **Given** today is 2025-03-15, **When** preset "last_4_weeks" is selected, **Then** the range covers 28 days ending yesterday.
4. **Given** today is 2025-03-15, **When** preset "current_year" is selected, **Then** the range is 2025-01-01 to 2025-12-31.
5. **Given** today is 2025-03-15, **When** preset "last_year" is selected, **Then** the range is 2024-01-01 to 2024-12-31.

---

### User Story 3 - View spending breakdown by category (Priority: P1)

As the system owner, I want to see how much I spent per category within a given period so that I can identify which categories consume the most.

**Why this priority**: Category breakdown is the actionable insight that helps reduce spending.

**Independent Test**: Insert categorized transactions, query category totals for a period, and verify sums per category.

**Acceptance Scenarios**:

1. **Given** transactions in "Alimentação" (-200) and "Transporte" (-100) within a period, **When** category totals are calculated, **Then** result includes both with correct sums.
2. **Given** a request for top 3 categories, **When** 5 categories have spending, **Then** only the top 3 by absolute value are returned.
3. **Given** a category with zero spending in the period, **When** category totals are calculated, **Then** that category is excluded from results.

---

### Edge Cases

- Period with no transactions → totals return 0, empty category list
- Custom date range where start > end → handled gracefully
- Period spanning year boundary → ISO week calculation handles correctly

## Requirements

### Functional Requirements

- **FR-001**: System MUST calculate total spending for any date range via `get_period_total()`
- **FR-002**: System MUST calculate category-wise totals via `get_period_category_totals()`
- **FR-003**: System MUST support sorted category totals with top-N limit via `get_sorted_period_category_totals()`
- **FR-004**: System MUST support period presets: current_week, last_week, current_quarter, last_quarter, current_semester, last_month, last_4_weeks, last_6_months, current_year, last_year
- **FR-005**: System MUST use ISO week numbering for weekly calculations
- **FR-006**: System MUST calculate week comparison with percentage change (handling division by zero)

### Key Entities

- **Period**: Defined by start_date and end_date (ISO format strings)
- **CategoryTotal**: category name + total amount for a period

## Success Criteria

- **SC-001**: All 10 period presets return correct date ranges
- **SC-002**: Category totals sum matches period total
- **SC-003**: Weekly comparison percentage is accurate within 0.01%

## Implementation References

- Period logic: `application/use_cases.py` → `compute_period_preset()`, `get_period_total()`, `get_period_category_totals()`, `get_sorted_period_category_totals()`
- Weekly logic: `application/use_cases.py` → `get_current_week_total()`, `get_previous_week_total()`, `get_week_comparison()`, `get_category_totals_current_week()`
- Repository queries: `infrastructure/repositories.py` → `TransactionRepository.sum_between()`, `sum_by_category_between()`
- Tests: `tests/test_use_cases.py` → `test_period_aggregation_and_categories()`, `test_compute_presets()`, `test_get_sorted_period_category_totals_*`
- Tests: `tests/test_weekly_consolidation.py` → `test_week_totals_and_comparison()`, `test_category_totals_current_week()`
