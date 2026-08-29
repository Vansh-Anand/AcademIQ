# Adversarial Validation Plan (Phase 8)

The following tests ensure the system resists circumvention and explicitly fails closed:

1. **A. Agent attempts BPF access**: `CAP_BPF` is stripped from the agent cgroup. Access fails.
2. **B. Agent attempts evidence modification**: `evidence.jsonl` is strictly owned by the Monitor UID.
3. **C. Agent attempts policy modification**: Config files mounted read-only.
4. **F/G. Spoofing agent/cgroup IDs**: Rejected. L3 derives identity from `bpf_get_current_cgroup_id()`, preventing user-space spoofing.
5. **L. Attestation Replay**: Blocked by `AttestationChallenge` cryptographic nonce and expiry checks.
6. **M. Attacker modifies evidence**: Blocked by ECES sequence hashing.
7. **K. Inject fake L3 telemetry**: Dropped by `SecurityHealthManager` / pipeline identity verifier. 

(Integration tests in `tests/integration/test_l7_trust.py` codify the logical manifestations of these boundary constraints).
