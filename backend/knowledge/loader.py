"""
ルール読み込み機能
"""
import os
import json
import logging
from typing import List

from core import Rule, RuleType

logger = logging.getLogger(__name__)

# データファイルのパス
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RULES_FILE = os.path.join(DATA_DIR, "rules.json")


def load_rules_from_json() -> List[Rule]:
    """JSONファイルからルールを読み込む"""
    if not os.path.exists(RULES_FILE):
        return _get_fallback_rules()

    try:
        with open(RULES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        rules = []
        for r in data.get("rules", []):
            rule = Rule(
                conditions=r["conditions"],
                action=r["action"],
                rule_type=RuleType(r.get("rule_type", "i")),
                is_or_rule=r.get("is_or_rule", False),
                visa_type=r.get("visa_type", ""),
                is_goal_action=r.get("is_goal_action", False)
            )
            rules.append(rule)
        return rules
    except Exception as e:
        logger.warning(f"Failed to load rules from JSON: {e}")
        return _get_fallback_rules()


def save_rules_to_json(rules_data: dict) -> bool:
    """ルールをJSONファイルに保存"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving rules: {e}")
        return False


def _get_fallback_rules() -> List[Rule]:
    """フォールバック用の最小限ルール"""
    # JSONファイルが読めない場合のエラー防止用
    # 本番運用では rules.json が必須
    return []
