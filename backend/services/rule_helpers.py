"""
ルール操作のヘルパー関数
"""
from typing import List, Set

from knowledge_base import VISA_RULES, VISA_TYPE_ORDER, _load_goal_actions_from_json


def rule_to_dict(rule) -> dict:
    """ルールオブジェクトをdict形式に変換（actionが識別子）"""
    return {
        "conditions": rule.conditions,
        "action": rule.action,
        "is_or_rule": rule.is_or_rule,
        "visa_type": rule.visa_type,
        "rule_type": rule.rule_type.value
    }


def rules_to_dict_list(rules: list) -> list:
    """ルールリストをdictリストに変換"""
    return [rule_to_dict(r) for r in rules]


def build_rules_data(rules: list, goal_actions: Set[str] = None) -> dict:
    """ルールリストをJSON保存用のdict形式に変換"""
    if goal_actions is None:
        goal_actions = _load_goal_actions_from_json()
    return {
        "rules": rules_to_dict_list(rules),
        "goal_actions": list(goal_actions)
    }


def find_rule_by_action(action: str):
    """actionでルールを検索"""
    return next((r for r in VISA_RULES if r.action == action), None)


def rules_excluding_action(exclude_action: str = None) -> list:
    """指定actionを除外したルールリストを返す"""
    if exclude_action:
        return [r for r in VISA_RULES if r.action != exclude_action]
    return list(VISA_RULES)


def sort_rules_by_action(rules: list) -> list:
    """action名順でソート（ビザタイプ順 → action名順）"""
    return sorted(rules, key=lambda r: (VISA_TYPE_ORDER.get(r.visa_type, 99), r.action))


def sort_rules_by_dependency(rules: list, goal_actions: Set[str]) -> list:
    """依存関係順でソート（ビザタイプ順 → 深度順）"""
    depth_cache = {}

    def get_depth(rule) -> int:
        if rule.id in depth_cache:
            return depth_cache[rule.id]
        if rule.action in goal_actions:
            depth_cache[rule.id] = 0
            return 0
        max_parent_depth = -1
        for other in rules:
            if rule.action in other.conditions:
                max_parent_depth = max(max_parent_depth, get_depth(other))
        depth_cache[rule.id] = 999 if max_parent_depth == -1 else max_parent_depth + 1
        return depth_cache[rule.id]

    for rule in rules:
        get_depth(rule)
    return sorted(rules, key=lambda r: (VISA_TYPE_ORDER.get(r.visa_type, 99), depth_cache.get(r.id, 999)))


def request_to_dict(rule) -> dict:
    """RuleRequestをdict形式に変換"""
    return {
        "conditions": rule.conditions,
        "action": rule.action,
        "is_or_rule": rule.is_or_rule,
        "visa_type": rule.visa_type,
        "rule_type": rule.rule_type
    }
