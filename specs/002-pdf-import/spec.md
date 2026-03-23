# Feature Specification: PDF Statement Import

**Feature Branch**: `002-pdf-import`
**Created**: 2026-03-22
**Status**: Implemented

## User Scenarios & Testing

### User Story 1 - Import Nubank PDF statement (Priority: P1)

As the system owner, I want to import a Nubank credit card PDF statement so that I can track credit card expenses without manually converting to CSV.

**Why this priority**: Nubank is the most commonly used credit card — direct PDF import removes the CSV conversion step.

**Independent Test**: Upload a Nubank PDF statement and verify transactions are parsed with correct dates, descriptions, and amounts.

**Acceptance Scenarios**:

1. **Given** a valid Nubank credit card PDF, **When** parsed, **Then** transactions are extracted with date, description, and amount.
2. **Given** a Nubank PDF with multiple pages, **When** parsed, **Then** all transactions across pages are captured.
3. **Given** a Nubank PDF, **When** parsed, **Then** all returned transactions have account_type "credit".

---

### User Story 2 - Import Itaú PDF statement (Priority: P2)

As the system owner, I want to import an Itaú credit card PDF statement so I have a second bank supported.

**Why this priority**: Itaú is a secondary bank — extends import coverage.

**Independent Test**: Upload an Itaú PDF and verify transactions are parsed correctly.

**Acceptance Scenarios**:

1. **Given** a valid Itaú credit card PDF, **When** parsed, **Then** transactions are extracted with date, description, and amount.
2. **Given** an Itaú PDF, **When** parsed, **Then** all returned transactions have account_type "credit".

---

### Edge Cases

- Corrupted PDF → graceful error handling
- PDF with no recognizable transaction patterns → empty list or error
- PDF from unsupported bank → not handled (out of scope)

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse Nubank credit card PDFs using pdfplumber
- **FR-002**: System MUST parse Itaú credit card PDFs using pdfplumber
- **FR-003**: System MUST extract date, description, and amount via regex heuristics
- **FR-004**: System MUST return `List[Transaction]` — same interface as CSV importer
- **FR-005**: System MUST set account_type to "credit" for PDF imports

### Key Entities

- **Transaction**: Same entity as CSV import — id, date, description, amount, account_type

## Success Criteria

- **SC-001**: Nubank PDF with 30+ transactions parses correctly
- **SC-002**: Itaú PDF with 30+ transactions parses correctly

## Implementation References

- Nubank parser: `importers/nubank_pdf_importer.py` → `parse_nubank_pdf()`
- Itaú parser: `importers/itau_pdf_importer.py` → `parse_itau_pdf()`
- Shared interface: Both return `List[Transaction]`
