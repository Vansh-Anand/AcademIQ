import re
import copy
from typing import Dict, Any, List

class EvidenceRedactionPolicy:
    """
    Redacts sensitive information from events before canonicalization.
    Modes: MINIMAL, STANDARD, FORENSIC
    """
    
    SENSITIVE_KEYS = {
        "password", "secret", "token", "api_key", "apikey", 
        "auth", "credential", "private_key", "access_key"
    }
    
    # Simple regex to catch bearer tokens or typical secret formats in raw strings
    TOKEN_REGEX = re.compile(r"(Bearer\s+[A-Za-z0-9\-\._~+/]+=*)")
    
    def __init__(self, mode: str = "STANDARD"):
        self.mode = mode
        
    def redact(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        if self.mode == "FORENSIC":
            # Forensic mode keeps everything for strict investigation
            # provided legal policy allows it.
            return event_dict
            
        redacted = copy.deepcopy(event_dict)
        self._traverse_and_redact(redacted)
        return redacted
        
    def _traverse_and_redact(self, obj: Any):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if any(sensitive in k.lower() for sensitive in self.SENSITIVE_KEYS):
                    obj[k] = "[REDACTED]"
                elif isinstance(v, str):
                    if self.mode == "STANDARD":
                        obj[k] = self.TOKEN_REGEX.sub("[REDACTED_TOKEN]", v)
                elif isinstance(v, (dict, list)):
                    self._traverse_and_redact(v)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    if self.mode == "STANDARD":
                        obj[i] = self.TOKEN_REGEX.sub("[REDACTED_TOKEN]", item)
                elif isinstance(item, (dict, list)):
                    self._traverse_and_redact(item)
