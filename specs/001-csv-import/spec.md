# Feature Specification: CSV Transaction Import

**Feature Branch**: `001-csv-import`
**Created**: 2026-03-22
**Status**: Implemented

## User Scenarios & Testing

### User Story 1 - Import CSV file (Priority: P1)

As the system owner, I want to upload a CSV file with my bank transactions so that they are parsed and persisted in the local database for financial analysis.

**Why this priority**: This is the primary data entry mechanism — without import, the system has no data.

**Independent Test**: Upload a valid CSV and verify transactions appear in the database.

**Acceptance Scenarios**:

1. **Given** a valid CSV with columns date, description, and amount, **When** the file is uploaded, **Then** all rows are parsed into Transaction objects with correct field values.
2. **Given** a CSV with Brazilian date format (dd/mm/yyyy), **When** imported, **Then** dates are converted to ISO 8601 (YYYY-MM-DD).
3. **Given** a CSV with amounts in Brazilian format (R$ 1.234,56), **When** imported, **Then** amounts are converted to float (1234.56).
4. **Given** a CSV with amounts in parentheses (e.g., (25.50)), **When** imported, **Then** amounts are parsed as negative values.

---

### User Story 2 - Flexible column detection (Priority: P1)

As the system owner, I want the importer to auto-detect column names regardless of naming variations so that I can import CSVs from different banks without manual mapping.

**Why this priority**: Different banks use different column headers — this removes friction from the import process.

**Independent Test**: Import CSVs with different column name variants and verify all parse correctly.

**Acceptance Scenarios**:

1. **Given** a CSV with columns "Data", "Descrição", "Valor", **When** imported, **Then** columns are mapped to date, description, amount.
2. **Given** a CSV with columns "date", "title", "value", **When** imported, **Then** columns are mapped correctly.
3. **Given** a CSV missing a required column (e.g., no amount column), **When** imported, **Then** an `InvalidCSVError` is raised with a descriptive message.

---

### User Story 3 - Account type detection (Priority: P2)

As the system owner, I want the system to guess whether a CSV contains credit card or checking account transactions based on the filename so I don't have to specify it manually every time.

**Why this priority**: Convenience feature that reduces manual steps during import.

**Independent Test**: Upload files with names containing "nubank" or "cartão" and verify account_type is set to "credit".

**Acceptance Scenarios**:

1. **Given** a file named "nubank-fatura-jan.csv", **When** the account type is guessed, **Then** it returns "credit".
2. **Given** a file named "extrato-itau.csv", **When** the account type is guessed, **Then** it returns "checking" (default).
3. **Given** a UI label "Cartão de Crédito (Credit Card)", **When** mapped to account_type, **Then** it returns "credit".

---

### Edge Cases

- Empty CSV → `InvalidCSVError` raised
- CSV with only headers and no data rows → empty list returned
- CSV with extra unrecognized columns → ignored gracefully
- Malformed row (missing fields) → `InvalidCSVError` raised
- CSV uploaded as bytes (Streamlit UploadedFile) → handled via `parse_csv(file)` accepting file-like objects

## Requirements

### Functional Requirements

- **FR-001**: System MUST accept CSV file upload via Streamlit file uploader or file path
- **FR-002**: System MUST auto-detect date, description, and amount columns from common variants
- **FR-003**: System MUST normalize dates to ISO 8601 format (YYYY-MM-DD)
- **FR-004**: System MUST normalize monetary amounts (handle R$, dot/comma locale, parentheses)
- **FR-005**: System MUST return `List[Transaction]` from parsing — never persist directly
- **FR-006**: System MUST assign default account_type "checking" unless overridden
- **FR-007**: System MUST raise `InvalidCSVError` for invalid or unparseable files

### Key Entities

- **Transaction**: id, date (ISO), description, amount (float), account_type (checking/credit), category_id (nullable)
- **InvalidCSVError**: Custom exception for CSV parsing failures

## Success Criteria

- **SC-001**: Real 3-month bank CSV imports without errors
- **SC-002**: Import of 5,000 transactions completes in < 3 seconds
- **SC-003**: Column name variants from at least 3 Brazilian banks are auto-detected

## Implementation References

- Parser: `importers/csv_importer.py` → `parse_csv()`
- Account detection: `app/dashboard.py` → `guess_account_type()`, `file_type_to_account_type()`
- Tests: `tests/test_importer.py`, `tests/test_csv_importer_more.py`, `tests/test_csv_importer_variations.py`, `tests/test_account_type_detection.py`
