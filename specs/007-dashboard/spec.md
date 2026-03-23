# Feature Specification: Interactive Dashboard

**Feature Branch**: `007-dashboard`
**Created**: 2026-03-22
**Status**: Implemented

## User Scenarios & Testing

### User Story 1 - View financial summary for a period (Priority: P1)

As the system owner, I want to open the dashboard and immediately see my spending summary for the selected period so that I understand my financial situation in under 2 minutes.

**Why this priority**: The dashboard is the primary interface — this is the core user experience.

**Independent Test**: Open the dashboard with transaction data and verify the summary shows period total, previous period comparison, and percentage change.

**Acceptance Scenarios**:

1. **Given** transactions exist in the database, **When** the dashboard loads, **Then** period total, previous period total, and percentage change are displayed.
2. **Given** a custom period is selected via date picker, **When** the dashboard refreshes, **Then** metrics reflect the selected date range.
3. **Given** a preset (e.g., "Semana Atual") is selected, **When** the dashboard refreshes, **Then** metrics reflect the preset's date range.

---

### User Story 2 - Upload and import transactions (Priority: P1)

As the system owner, I want to upload a CSV or PDF file through the dashboard so that new transactions are imported and immediately visible.

**Why this priority**: Import is the primary data entry — the dashboard must support it directly.

**Independent Test**: Upload a CSV via the dashboard, confirm transactions, and verify they appear in the database.

**Acceptance Scenarios**:

1. **Given** a CSV file is uploaded, **When** parsed, **Then** a preview table shows the transactions before persistence.
2. **Given** the preview is displayed, **When** I confirm import, **Then** transactions are persisted with batch tracking metadata.
3. **Given** a PDF file is uploaded, **When** the file type is detected as PDF, **Then** the appropriate PDF parser is used (Nubank or Itaú).
4. **Given** during preview, **When** I assign categories to individual rows, **Then** those categories are applied during persistence.

---

### User Story 3 - View category breakdown chart (Priority: P2)

As the system owner, I want to see a bar chart showing spending by category so that I can visually identify where my money goes.

**Why this priority**: Visual representation makes spending patterns immediately obvious.

**Independent Test**: View the chart with categorized transactions and verify categories and amounts are correctly rendered.

**Acceptance Scenarios**:

1. **Given** categorized transactions for a period, **When** the chart is displayed, **Then** it shows top 8 categories sorted by spending (descending).
2. **Given** the toggle to exclude "Não categorizado" is enabled, **When** the chart renders, **Then** uncategorized spending is excluded.
3. **Given** the chart mode is set to "% do total", **When** rendered, **Then** bars show percentage of total spending instead of absolute values.

---

### User Story 4 - Manage categories (Priority: P3)

As the system owner, I want to manage categories directly from the dashboard so that I can create, reassign, and delete categories without touching the database.

**Why this priority**: Category management is a secondary workflow but needed for ongoing maintenance.

**Independent Test**: Open the category management expander, reassign a transaction's category, and verify persistence.

**Acceptance Scenarios**:

1. **Given** the "Gerenciar categorização" expander is opened, **When** I filter uncategorized transactions, **Then** only transactions with "Não categorizado" are shown.
2. **Given** I select a new category for a transaction, **When** I apply the change, **Then** the transaction's category is updated in the database.
3. **Given** I delete a category, **When** confirmed, **Then** the category is removed and its transactions revert to uncategorized.

---

### Edge Cases

- No transactions in database → dashboard loads with empty state, no crashes
- File upload with no data → error message displayed
- Session state preservation across Streamlit reruns

## Requirements

### Functional Requirements

- **FR-001**: Dashboard MUST use Streamlit with wide layout
- **FR-002**: Dashboard MUST support CSV and PDF file upload
- **FR-003**: Dashboard MUST auto-detect file format (CSV vs PDF) from file extension
- **FR-004**: Dashboard MUST show period metrics with previous period comparison
- **FR-005**: Dashboard MUST support preset and custom period selection
- **FR-006**: Dashboard MUST render Altair bar charts for category breakdown
- **FR-007**: Dashboard MUST support category management (reassign, create new, delete)
- **FR-008**: Dashboard MUST track import batches with metadata

### Key Entities

- **DashboardSummary**: period_start, period_end, current (total), previous (total), pct_change, categories (list)

## Success Criteria

- **SC-001**: User can understand weekly financial situation in < 2 minutes
- **SC-002**: Dashboard loads in < 3 seconds with 5,000+ transactions
- **SC-003**: All CRUD operations on categories persist correctly

## Implementation References

- Main entry: `app/dashboard.py` → `main()`
- Summary logic: `app/dashboard.py` → `get_dashboard_summary()`
- Tests: `tests/test_dashboard_run.py`, `tests/test_dashboard_summary.py`, `tests/test_dashboard_helpers.py`
