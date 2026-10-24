from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class StartSessionRequest(BaseModel):
    domain: str


class ObserveRequest(BaseModel):
    evidence: Dict[str, Any]


class AnswerDiagnosticRequest(BaseModel):
    question_id: str
    option_index: int


class TransferVerifyRequest(BaseModel):
    passed: bool
    note: str = ""


class TeachRequest(BaseModel):
    target: str
