from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


SEVERITY_CVSS = {
    Severity.CRITICAL: 9.0,
    Severity.HIGH: 7.0,
    Severity.MEDIUM: 5.0,
    Severity.LOW: 3.0,
    Severity.INFO: 0.0,
}


@dataclass
class Finding:
    module: str
    severity: Severity
    title: str
    endpoint: str
    evidence: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    cwe: str = ""
    cvss: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if self.cvss == 0.0:
            self.cvss = SEVERITY_CVSS.get(self.severity, 0.0)
