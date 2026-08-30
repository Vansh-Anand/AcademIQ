import os
import pytest
import sqlite3
import json

from l6_eces.storage.sqlite_store import SQLiteEvidenceStore
from l6_eces.chain.store import JsonlEvidenceStore
from l6_eces.chain.schemas import GenesisRecord, EvidenceRecord
from l6_eces.chain.writer import EvidenceChainWriter
from l6_eces.crypto.hasher import HashProvider
from l6_eces.crypto.signer import SoftwareSigner
from common.events.schemas import ToolInvocationEvent

def create_event(seq: int, session: str = "test-session"):
    return ToolInvocationEvent(
        event_id=f"evt-{seq}",
        timestamp_ns=1000 + seq,
        agent_id="agent1",
        session_id=session,
        trace_id=f"trace-{seq}",
        layer="L2",
        tool_name="test_tool",
        arguments={"arg": seq}
    )

def test_sqlite_store_append_and_retrieve(tmp_path):
    db_path = str(tmp_path / "eces.db")
    hasher = HashProvider()
    signer = SoftwareSigner()
    signer.generate_key()
    
    store = SQLiteEvidenceStore(db_path)
    writer = EvidenceChainWriter(store, hasher, signer)
    
    evt1 = create_event(1)
    evt2 = create_event(2)
    
    writer.append_event(evt1, source_layer="L5_Risk")
    writer.append_event(evt2, source_layer="L5_Risk")
    
    records = store.read_all()
    assert len(records) == 3 # Genesis + 2 evidence
    
    assert records[0]["_type"] == "genesis"
    assert records[1]["_type"] == "evidence"
    assert records[1]["data"]["event_id"] == "evt-1"
    assert records[2]["data"]["event_id"] == "evt-2"

def test_sqlite_store_persistence(tmp_path):
    db_path = str(tmp_path / "eces.db")
    hasher = HashProvider()
    signer = SoftwareSigner()
    signer.generate_key()
    
    # Process A
    store_a = SQLiteEvidenceStore(db_path)
    writer_a = EvidenceChainWriter(store_a, hasher, signer)
    writer_a.append_event(create_event(1), source_layer="TEST")
    
    head_a = store_a.get_chain_head()
    
    # Process B (simulated by new instance)
    store_b = SQLiteEvidenceStore(db_path)
    head_b = store_b.get_chain_head()
    
    assert head_a.chain_id == head_b.chain_id
    assert head_a.latest_sequence == head_b.latest_sequence
    assert head_a.latest_event_hash == head_b.latest_event_hash

def test_jsonl_backward_compatibility(tmp_path):
    # Ensure JsonlEvidenceStore still works as expected
    store_dir = str(tmp_path / "jsonl_evidence")
    hasher = HashProvider()
    signer = SoftwareSigner()
    signer.generate_key()
    
    store = JsonlEvidenceStore(store_dir)
    writer = EvidenceChainWriter(store, hasher, signer)
    writer.append_event(create_event(1), source_layer="TEST")
    
    records = store.read_all()
    assert len(records) == 2
    assert records[0]["_type"] == "genesis"
    assert records[1]["_type"] == "evidence"

def test_tamper_detection(tmp_path):
    db_path = str(tmp_path / "eces_tamper.db")
    hasher = HashProvider()
    signer = SoftwareSigner()
    signer.generate_key()
    
    store = SQLiteEvidenceStore(db_path)
    writer = EvidenceChainWriter(store, hasher, signer)
    writer.append_event(create_event(1), source_layer="TEST")
    writer.append_event(create_event(2), source_layer="TEST")
    
    from l6_eces.forensics.verifier import EvidenceVerifier
    verifier = EvidenceVerifier(signer)
    
    # Should be valid initially
    res = verifier.verify_chain(store.read_all())
    assert res.valid is True
    
    # Tamper with the database payload
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT chain_id, sequence_number, record_json FROM evidence WHERE sequence_number=1")
        row = cursor.fetchone()
        
        tampered_data = json.loads(row[2])
        tampered_data["payload"]["arguments"]["arg"] = 999 # malicious change
        
        conn.execute("UPDATE evidence SET record_json = ? WHERE sequence_number=1", 
                     (json.dumps(tampered_data),))
        conn.commit()
        
    # Should detect payload hash mismatch
    res_tampered = verifier.verify_chain(store.read_all())
    assert res_tampered.valid is False
    assert res_tampered.failure_type == "PAYLOAD_HASH_MISMATCH"

def test_multiple_session_isolation(tmp_path):
    db_path = str(tmp_path / "eces_sessions.db")
    store = SQLiteEvidenceStore(db_path)
    hasher = HashProvider()
    signer = SoftwareSigner()
    signer.generate_key()
    
    writer = EvidenceChainWriter(store, hasher, signer)
    
    writer.append_event(create_event(1, "session-A"), source_layer="TEST")
    writer.append_event(create_event(2, "session-B"), source_layer="TEST")
    writer.append_event(create_event(3, "session-A"), source_layer="TEST")
    
    records = store.read_all()
    session_a = [r for r in records if r["_type"] == "genesis" or r["data"].get("session_id") == "session-A"]
    session_b = [r for r in records if r["_type"] == "genesis" or r["data"].get("session_id") == "session-B"]
    
    assert len(session_a) == 3 # Genesis + 2 events
    assert len(session_b) == 2 # Genesis + 1 event
