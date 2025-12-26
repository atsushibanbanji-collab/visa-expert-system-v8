"""
ルールの整合性チェック機能
"""
from collections import Counter
from typing import List, Optional

from knowledge_base import VISA_RULES, get_all_rules, _load_goal_actions_from_json


def find_rule_by_action(action: str):
    """actionでルールを検索"""
    return next((r for r in VISA_RULES if r.action == action), None)


def check_rules_integrity(visa_type: Optional[str] = None) -> List[dict]:
    """ルールの整合性をチェックし、問題のリストを返す"""
    rules = get_all_rules()
    if visa_type:
        rules = [r for r in rules if r.visa_type == visa_type]

    issues = []
    all_actions = {r.action for r in VISA_RULES}
    goal_actions = _load_goal_actions_from_json()

    # 到達不能なルールをチェック
    for rule in rules:
        for cond in rule.conditions:
            if cond in all_actions and not any(r.action == cond for r in VISA_RULES):
                issues.append({
                    "type": "unreachable",
                    "action": rule.action,
                    "message": f"条件「{cond}」を導出するルールがありません"
                })

    # 循環参照をチェック
    def check_cycle(action: str, visited: set, path: list):
        if action in visited:
            return path + [action]
        visited.add(action)
        path.append(action)
        rule = find_rule_by_action(action)
        if rule:
            for cond in rule.conditions:
                if cond in all_actions:
                    cycle = check_cycle(cond, visited.copy(), path.copy())
                    if cycle:
                        return cycle
        return None

    for rule in rules:
        cycle = check_cycle(rule.action, set(), [])
        if cycle and len(cycle) > 1:
            issues.append({
                "type": "cycle",
                "actions": cycle,
                "message": f"ルールに循環参照があります: {' -> '.join(cycle)}"
            })

    # 孤立ルールをチェック（THENが他で使われていない + ゴールでもない）
    for rule in rules:
        if rule.action not in goal_actions:
            if not any(rule.action in r.conditions for r in VISA_RULES if r.action != rule.action):
                issues.append({
                    "type": "orphan",
                    "action": rule.action,
                    "message": f"THEN「{rule.action}」はどこからも参照されていません"
                })

    # actionの一意性をチェック
    action_counts = Counter(r.action for r in VISA_RULES)
    for action, count in action_counts.items():
        if count > 1:
            issues.append({
                "type": "duplicate_action",
                "action": action,
                "count": count,
                "message": f"THEN「{action}」が{count}回使用されています"
            })

    return issues
