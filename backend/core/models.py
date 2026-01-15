"""
データモデル定義
"""
from typing import List
from dataclasses import dataclass
from .enums import RuleType


@dataclass
class Rule:
    """ルールクラス

    Smalltalk資料のRuleクラスに相当。
    idとnameはactionから自動生成される（actionが一意な識別子）。
    """
    conditions: List[str]      # 条件部
    action: str                # 結論部（一意な識別子）
    rule_type: RuleType        # ルールタイプ
    is_or_rule: bool = False   # OR条件かどうか
    is_goal_action: bool = False  # ゴールアクションかどうか
    flag: str = None           # 発火状態フラグ

    def __post_init__(self):
        if self.flag is None:
            self.flag = "pending"

    @property
    def id(self) -> str:
        """actionを識別子として使用"""
        return self.action

    @property
    def name(self) -> str:
        """actionを名前として使用"""
        return self.action
