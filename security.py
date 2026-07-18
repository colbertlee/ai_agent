import re
from typing import Dict, Callable, List


class SecurityModule:
    def __init__(self):
        self.sensitive_patterns = [
            r'password', r'api[_-]?key', r'secret', r'token', r'private',
        ]
        self.dangerous_patterns = [
            r'rm -rf', r'del /f', r'exec\(', r'eval\(',
            r'import os', r'subprocess\.', r'os\.system',
        ]

    def check_input(self, user_input: str) -> Dict[str, bool]:
        for p in self.dangerous_patterns:
            if re.search(p, user_input, re.IGNORECASE):
                return {"blocked": True, "reason": f"Dangerous: {p}"}
        return {"blocked": False, "reason": ""}

    def check_output(self, output: str) -> Dict[str, bool]:
        for p in self.sensitive_patterns:
            if re.search(p, output, re.IGNORECASE):
                return {"blocked": True, "reason": "Sensitive info"}
        return {"blocked": False, "reason": ""}

    def sanitize_output(self, output: str) -> str:
        for p in self.sensitive_patterns:
            output = re.sub(p, "[REDACTED]", output, flags=re.IGNORECASE)
        return output


_security_instance = None

def set_security_instance(instance):
    global _security_instance
    _security_instance = instance

def get_security_instance():
    global _security_instance
    if _security_instance is None:
        _security_instance = SecurityModule()
    return _security_instance
