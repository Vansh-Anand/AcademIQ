import time
from typing import Optional, Dict, Any

from common.events.schemas import ShellCommandEvent
from common.schemas.security import SecurityDecision, DecisionEnum

from .parser import ShlexCommandParser
from .normalizers import get_default_normalizer
from .canonicalizer import ASTCanonicalizer
from .toctou.resolver import TOCTOUResolver
from .policy.matcher import SemanticPolicyMatcher

class L2Interceptor:
    def __init__(self, policy_path: str = "config/policies/sdn.yaml"):
        self.parser = ShlexCommandParser()
        self.normalizer = get_default_normalizer()
        self.canonicalizer = ASTCanonicalizer()
        self.toctou = TOCTOUResolver()
        self.matcher = SemanticPolicyMatcher(policy_path)
        
    def intercept(self, event: ShellCommandEvent) -> SecurityDecision:
        """
        Intercepts a shell command event, parses, normalizes, canonicalizes,
        applies TOCTOU locks, and evaluates against policy.
        """
        raw_cmd = event.raw_command
        
        try:
            # 1. Parse
            ast = self.parser.parse(raw_cmd)
            
            # 2. Normalize
            norm_ast = self.normalizer.normalize(ast)
            
            # 3. Canonicalize
            canon_ast = self.canonicalizer.canonicalize(norm_ast)
            
            # 4. TOCTOU Lock
            locked_ast = self.toctou.resolve_and_lock(canon_ast)
            
            # 5. Semantic Match
            is_allowed, reason = self.matcher.match(locked_ast)
            
            if is_allowed:
                return SecurityDecision(
                    decision=DecisionEnum.ALLOW,
                    reason_codes=["SDN_POLICY_ALLOW"],
                    risk_score=0.0,
                    confidence=1.0,
                    source_layers=["L2"],
                    related_event_ids=[event.event_id],
                    timestamp_ns=time.time_ns()
                ), locked_ast
            else:
                return SecurityDecision(
                    decision=DecisionEnum.BLOCK,
                    reason_codes=["SDN_POLICY_VIOLATION"],
                    risk_score=100.0,
                    confidence=1.0,
                    source_layers=["L2"],
                    related_event_ids=[event.event_id],
                    timestamp_ns=time.time_ns()
                ), locked_ast
                
        except Exception as e:
            # Fail closed on any parsing or processing errors
            return SecurityDecision(
                decision=DecisionEnum.BLOCK,
                reason_codes=["SDN_PROCESSING_ERROR"],
                risk_score=100.0,
                confidence=1.0,
                source_layers=["L2"],
                related_event_ids=[event.event_id],
                timestamp_ns=time.time_ns()
            ), None
