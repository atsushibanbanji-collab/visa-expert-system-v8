"""
ルール操作のヘルパー関数
"""


def rule_to_dict(rule) -> dict:
    """ルールオブジェクトをdict形式に変換（actionが識別子）"""
    return {
        "conditions": rule.conditions,
        "action": rule.action,
        "is_or_rule": rule.is_or_rule,
        "rule_type": rule.rule_type.value,
        "is_goal_action": rule.is_goal_action
    }


def rules_to_dict_list(rules: list) -> list:
    """ルールリストをdictリストに変換"""
    return [rule_to_dict(r) for r in rules]


def build_rules_data(rules: list) -> dict:
    """ルールリストをJSON保存用のdict形式に変換"""
    return {
        "rules": rules_to_dict_list(rules)
    }


def request_to_dict(rule) -> dict:
    """RuleRequestをdict形式に変換"""
    return {
        "conditions": rule.conditions,
        "action": rule.action,
        "is_or_rule": rule.is_or_rule,
        "rule_type": rule.rule_type,
        "is_goal_action": rule.is_goal_action
    }
