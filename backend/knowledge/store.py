"""
ルールストア - ルールの保存・取得機能
"""
from typing import List

from core import Rule
from .loader import load_rules_from_json, save_rules_to_json


# グローバルルールストア（初回アクセス時にロード）
RULES: List[Rule] = load_rules_from_json()


def get_all_rules() -> List[Rule]:
    """全ルールを取得"""
    return RULES.copy()


def get_goal_rules() -> List[Rule]:
    """ゴールルール（最終結論を導くルール）を取得（rules.json順）"""
    return [r for r in RULES if r.is_goal_action]


def get_all_base_conditions() -> set:
    """全ての基本条件（他のルールの結論ではないもの）を取得"""
    all_conditions = set()
    all_actions = {r.action for r in RULES}

    for rule in RULES:
        for cond in rule.conditions:
            if cond not in all_actions:
                all_conditions.add(cond)

    return all_conditions


def get_derived_conditions() -> set:
    """導出可能な条件（他のルールの結論であるもの）を取得"""
    return {r.action for r in RULES}


def reload_rules() -> List[Rule]:
    """ルールを再読み込み（編集後に呼び出す）

    注意: リストをin-place更新することで、
    他モジュールからimportされた参照も最新データを指すようになる
    """
    global RULES
    new_rules = load_rules_from_json()
    RULES.clear()
    RULES.extend(new_rules)
    return RULES


def save_rules(rules_data: dict) -> bool:
    """ルールをJSONファイルに保存"""
    if save_rules_to_json(rules_data):
        reload_rules()
        return True
    return False
