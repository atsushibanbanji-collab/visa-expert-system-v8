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
    action: str
    is_or_rule: bool = False
    visa_type: str = ""
    rule_type: str = "i"  # "i" for INITIAL, "m" for MIDDLE
    is_goal_action: bool = False  # ゴールアクションかどうか
    index: Optional[int] = None  # 編集時の対象インデックス（0始まり）
    insert_after: Optional[int] = None  # 挿入位置（0=先頭、N=N番目の後、None=末尾）


class DeleteRequest(BaseModel):
    index: int  # 削除対象のインデックス（0始まり）


class ReorderRequest(BaseModel):
    actions: List[str]


# ========== ビザタイプ管理関連 ==========

class VisaTypeRequest(BaseModel):
    code: str
    order: Optional[int] = None
