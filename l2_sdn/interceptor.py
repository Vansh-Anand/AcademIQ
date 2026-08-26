import time
from typing import Optional, Tuple
from common.events.schemas import ShellCommandEvent
from .events import NormalizedCommandEvent, RawShellCommand
from .parser import BashlexCommandParser
from .normalizers import get_default_normalizer
from .canonicalizer import CommandCanonicalizer
from .toctou.resolver import TOCTOUResolver
from .toctou.verifier import TOCTOUVerifier
from .policy.matcher import CommandPolicyMatcher

class ShellInterceptor:
    def intercept(self, event: ShellCommandEvent) -> Tuple[str, NormalizedCommandEvent]:
        raise NotImplementedError

class DevelopmentShellInterceptor(ShellInterceptor):
    def __init__(self, policy_path: str = "config/policies/shell.yaml"):
        self.parser = BashlexCommandParser()
        self.normalizer = get_default_normalizer()
        self.canonicalizer = CommandCanonicalizer()
        self.toctou_resolver = TOCTOUResolver()
        self.toctou_verifier = TOCTOUVerifier()
        self.matcher = CommandPolicyMatcher(policy_path)
        
    def intercept(self, event: ShellCommandEvent) -> Tuple[str, NormalizedCommandEvent]:
        raw_cmd = RawShellCommand(
            command_text=event.raw_command,
            session_id=event.trace_id, # Simplify trace matching
            trace_id=event.trace_id
        )
        
        try:
            # 1. Parse
            parsed = self.parser.parse(raw_cmd.command_text)
            
            # Sub-check: unresolved substitutions
            if parsed.command_substitutions:
                # We can't safely resolve this. Fail closed.
                return "BLOCK", self._build_event(event, raw_cmd, "BLOCK", "SDN_UNRESOLVED_SUBSTITUTION")
                
            # 2. Normalize (Passes 1-4)
            normalized = self.normalizer.normalize(parsed)
            
            # 3. Canonicalize (Pass 5)
            canonical = self.canonicalizer.canonicalize(normalized)
            
            # 4. TOCTOU Lock identity
            identities = self.toctou_resolver.resolve(canonical)
            
            # 5. Policy Match
            decision, reason = self.matcher.match(canonical)
            
            # 6. Verify TOCTOU just before returning decision
            # (In reality, execution happens right after this, so L3 verifies it. 
            # But we verify it here as an immediate pre-flight check)
            toctou_valid, toctou_reason = self.toctou_verifier.verify(identities)
            
            if not toctou_valid:
                decision = "BLOCK"
                reason = toctou_reason
                
            out_event = NormalizedCommandEvent(
                event_id=f"sdn-{time.time_ns()}",
                session_id=raw_cmd.session_id,
                trace_id=raw_cmd.trace_id,
                original_command_hash=normalized.original_hash,
                canonical_command_hash=canonical.command_hash,
                normalization_passes=["VariableExpansion", "EncodingDecode", "ANSICQuoting", "AliasResolution", "Canonicalization"],
                obfuscation_detected=len(normalized.transformations_applied) > 0,
                policy_result=decision,
                matched_rule=reason,
                path_identities=[id.model_dump() for id in identities],
                security_decision=decision
            )
            
            return decision, out_event
            
        except Exception as e:
            # Fail closed on parsing error
            return "BLOCK", self._build_event(event, raw_cmd, "BLOCK", f"SDN_PROCESSING_ERROR: {e}")
            
    def _build_event(self, base_event: ShellCommandEvent, raw: RawShellCommand, decision: str, reason: str) -> NormalizedCommandEvent:
        return NormalizedCommandEvent(
            event_id=f"sdn-{time.time_ns()}",
            session_id=raw.session_id,
            trace_id=raw.trace_id,
            original_command_hash="unknown",
            canonical_command_hash="unknown",
            policy_result=decision,
            matched_rule=reason,
            security_decision=decision
        )

class LinuxLDPreloadInterceptor(ShellInterceptor):
    def intercept(self, event: ShellCommandEvent) -> Tuple[str, NormalizedCommandEvent]:
        raise NotImplementedError("Native Linux LD_PRELOAD interceptor is scaffolding. Execution on Windows is simulated.")

class LinuxEBPFUprobeInterceptor(ShellInterceptor):
    def intercept(self, event: ShellCommandEvent) -> Tuple[str, NormalizedCommandEvent]:
        raise NotImplementedError("Native Linux eBPF uprobe interceptor is scaffolding. Execution on Windows is simulated.")

class ExecutionGate:
    """
    Enforces that the command passed all L2 stages and TOCTOU before execution.
    """
    def execute_safely(self, interceptor: ShellInterceptor, event: ShellCommandEvent) -> bool:
        decision, out_event = interceptor.intercept(event)
        if decision == "ALLOW":
            # Real execution would happen here, followed by L3 telemetry collection.
            return True
        return False
