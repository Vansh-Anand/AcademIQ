# Phase D: ECES Durable Storage with SQLite

## Overview
Phase D upgrades the Evidentiary Causal Event Store (ECES) from a single-file JSONL (`.data/evidence/evidence.jsonl`) into a durable, queryable, append-only SQLite database. This transition proves that cryptographic evidence chains can persist across process restarts, be indexed by session, and survive external tampering without losing their tamper-evident properties.

## Architecture

### Previous Storage Architecture
The legacy implementation used a flat JSONL file. While atomic (`os.fsync`) and tamper-evident (via cryptographic verification), it lacked structured querying capabilities. Reading a specific session's chain required a full O(N) scan of the entire log, making it inefficient for long-term forensic persistence.

### New SQLite Storage Architecture
The new architecture introduces the `EvidenceStore` Abstract Base Class.
- **Legacy Support**: The JSONL logic was preserved as `JsonlEvidenceStore` to ensure full backward compatibility with older components and tests.
- **SQLite Support**: The `SQLiteEvidenceStore` provides a high-performance relational backend.

### Schema Design
The SQLite database (`eces.db`) uses two tables:
1. `genesis`: Stores the root `GenesisRecord` for the chain.
2. `evidence`: Stores the individual `EvidenceRecord` items.

```sql
CREATE TABLE IF NOT EXISTS evidence (
    chain_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    event_id TEXT NOT NULL UNIQUE,
    timestamp_ns INTEGER NOT NULL,
    source_layer TEXT NOT NULL,
    event_type TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    PRIMARY KEY (chain_id, sequence_number)
)
```
An index `idx_session_id` was added to `session_id` to allow fast O(log N) retrieval of isolated sessions.

## Serialization and Canonicalization
To guarantee deterministic hashing, the actual Pydantic objects are stored directly in the `record_json` column using `record.model_dump_json()`. When the verification tool reads these records, it loads them via `json.loads(row)` and then passes the payload dictionary into AcademIQ's existing `CanonicalSerializer`. This ensures that key-ordering, whitespace, and Unicode representations remain perfectly aligned with the original cryptographic hash generated in memory, preventing false-positive tampering alerts.

## Append-Only Enforcement
Since standard SQLite does not natively support immutable rows, append-only semantics are enforced at the application level:
1. The `SQLiteEvidenceStore` class explicitly only executes `INSERT` statements.
2. The `PRIMARY KEY (chain_id, sequence_number)` and `UNIQUE (event_id)` database constraints prevent accidental overwrites or duplicate sequence injections.

> [!CAUTION]
> This is a **tamper-evident** persistence layer, not a strictly **tamper-proof** one. A malicious actor with root file-system access can still run `UPDATE evidence SET...`, but the cryptographic verification tool will immediately detect the intrusion.

## Process Restart Validation
The storage was explicitly verified to persist across process restarts. In "Scenario B" of the benchmark, the Python process writes 100 events, terminates, and a fresh instance of `SQLiteEvidenceStore` is instantiated against the same `eces.db` file. The recovered `latest_event_hash` matches perfectly, proving durability.

## Tamper Detection Methodology
The standalone utility `python -m l6_eces.verify_chain --database <path>` was built to evaluate the cryptographic chain offline.
During the benchmark:
- **Payload Tampering**: A stored 1KB JSON payload was maliciously altered using a direct `UPDATE` query. The verification tool immediately flagged `PAYLOAD_HASH_MISMATCH` at the exact sequence number.
- **Hash Tampering**: A `previous_hash` value was maliciously altered using a direct `UPDATE` query. The verification tool correctly flagged a `CHAIN_BREAK`.

## Performance Metrics
Performance was tested by appending 100 1KB-payload events. 

*Note: The time reflects the SQLite disk persistence + the `model_dump_json()` serialization overhead.*
- **Mean Append Latency:** ~24.3 ms
- **Median Append Latency:** ~23.2 ms
- **p95 Append Latency:** ~48.6 ms
- **Mean Verification Latency (100 records):** ~468 ms

## Limitations
- **File System Level:** If the attacker simply deletes the entire `eces.db` file, the evidence is lost. Real-world deployments should couple this SQLite database with a Write-Once-Read-Many (WORM) storage volume or an offsite append-only remote syslog.
- **No DB Triggers:** Currently, we rely on application-level enforcement and primary keys. We could add SQLite `CREATE TRIGGER ... RAISE(ABORT, 'Append Only')` to prevent `UPDATE` and `DELETE` at the engine level for an extra layer of defense against accidental administrative changes.
