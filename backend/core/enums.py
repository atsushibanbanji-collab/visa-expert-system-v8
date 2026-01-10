"""
列挙型定義
"""
from enum import Enum


class RuleType(Enum):
    """ルールタイプ"""
    INITIAL = "i"   # 開始ルール（基本条件のみで構成）
    MIDDLE = "m"    # 中間ルール（導出条件を含む）


class FactStatus(Enum):
    """事実のステータス"""
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"
    PENDING = "pending"


class RuleStatus(Enum):
    """ルールの評価状態"""
    PENDING = "pending"       # 未評価
    EVALUATING = "evaluating" # 評価中
    FIRED = "fired"           # 発火（条件充足）
    BLOCKED = "blocked"       # ブロック（FALSEにより不可）
    UNCERTAIN = "uncertain"   # 不確定（UNKNOWNにより判定不能）

    @classmethod
    def is_resolved(cls, status: "RuleStatus") -> bool:
        """ルールが解決済み（発火、ブロック、または不確定）かどうか"""
        return status in (cls.FIRED, cls.BLOCKED, cls.UNCERTAIN)

