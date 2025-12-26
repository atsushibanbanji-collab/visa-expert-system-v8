"""
Pydantic スキーマ定義
"""
from pydantic import BaseModel
from typing import List, Optional


# ========== 診断関連 ==========

class StartRequest(BaseModel):
    session_id: str


class AnswerRequest(BaseModel):
    session_id: str
    answer: str  # "yes", "no", "unknown"


class GoBackRequest(BaseModel):
    session_id: str
    steps: int = 1


# ========== ルール管理関連 ==========

class RuleRequest(BaseModel):
    conditions: List[str]
    action: str  # 一意な識別子
    is_or_rule: bool = False
    visa_type: str = ""
    rule_type: str = "i"  # "i" for INITIAL, "m" for MIDDLE
    original_action: Optional[str] = None  # 編集時の元のaction


class DeleteRequest(BaseModel):
    action: str


class ReorderRequest(BaseModel):
    actions: List[str]


class AutoOrganizeRequest(BaseModel):
    mode: str = "dependency"  # "dependency" or "action"
