# Feature Specification: Import Batch Tracking

**Feature Branch**: `008-batch-tracking`
**Created**: 2026-03-22
**Status**: Implemented

## User Scenarios & Testing

### User Story 1 - Track import metadata (Priority: P1)

As the system owner, I want each file import to be logged with metadata (source, file type, row counts) so that I can audit what was imported and when.

**Why this priority**: Auditability — knowing what was imported, when, and how many rows succeeded/failed prevents confusion.

**Independent Test**: Import a CSV, then query the import_batches table and verify a batch record exists with correct metadata.

**Acceptance Scenarios**:

1. **Given** a CSV file is imported, **When** the import completes, **Then** an import batch record is created with source, file_type, and timestamps.
2. **Given** a batch is created, **When** transactions are processed, **Then** the batch is updated with rows_parsed, inserted, and failed counts.
3. **Given** a batch ID, **When** queried, **Then** the full batch metadata is returned.

---

### Edge Cases

- Import with all duplicates → batch shows rows_parsed=N, inserted=0, failed=0
- Import with parse errors → batch shows failed count

## Requirements

### Functional Requirements

- **FR-001**: System MUST create an import batch record before processing transactions
- **FR-002**: System MUST update batch with final counts (rows_parsed, inserted, failed) after processing
- **FR-003**: Each transaction MUST reference its batch_id
- **FR-004**: System MUST support querying batch by ID

### Key Entities

- **ImportBatch**: id, source, file_type, rows_parsed, inserted, failed, notes, created_at

## Success Criteria

- **SC-001**: Every import creates a traceable batch record
- **SC-002**: Batch counts accurately reflect import results

## Implementation References

- Repository: `infrastructure/repositories.py` → `ImportBatchRepository.create_batch()`, `update_counts()`, `get_batch()`
- Schema: `infrastructure/database.py` → `import_batches` table
- Tests: `tests/test_import_batch.py` → `test_create_and_update_batch()`
