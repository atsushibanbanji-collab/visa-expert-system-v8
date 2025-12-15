"""
ビザ選定エキスパートシステム - 知識ベース
ビザ選定知識.txtに基づくルール定義
JSONファイルからルールを読み込み、将来的な編集機能に対応
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import os


class RuleType(Enum):
    INITIAL = "i"   # 開始ルール
    MIDDLE = "m"    # 中間ルール


@dataclass
class Rule:
    """Smalltalk資料のRuleクラスに相当"""
    id: str
    name: str
    conditions: List[str]  # 条件部
    action: str            # 結論部
    rule_type: RuleType    # ルールタイプ
    is_or_rule: bool = False  # OR条件かどうか
    visa_type: str = ""    # 関連するビザタイプ
    flag: str = None       # 発火状態フラグ

    def __post_init__(self):
        if self.flag is None:
            self.flag = "pending"


# データファイルのパス
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RULES_FILE = os.path.join(DATA_DIR, "rules.json")


def _load_rules_from_json() -> List[Rule]:
    """JSONファイルからルールを読み込む"""
    if not os.path.exists(RULES_FILE):
        return _get_hardcoded_rules()

    try:
        with open(RULES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        rules = []
        for r in data.get("rules", []):
            rule = Rule(
                id=r["id"],
                name=r["name"],
                conditions=r["conditions"],
                action=r["action"],
                rule_type=RuleType(r["rule_type"]),
                is_or_rule=r.get("is_or_rule", False),
                visa_type=r.get("visa_type", "")
            )
            rules.append(rule)
        return rules
    except Exception as e:
        print(f"Warning: Failed to load rules from JSON: {e}")
        return _get_hardcoded_rules()


def _load_goal_actions_from_json() -> List[str]:
    """JSONファイルからゴールアクションを読み込む"""
    if not os.path.exists(RULES_FILE):
        return _get_hardcoded_goal_actions()

    try:
        with open(RULES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("goal_actions", _get_hardcoded_goal_actions())
    except Exception:
        return _get_hardcoded_goal_actions()


def _get_hardcoded_goal_actions() -> List[str]:
    """ハードコードされたゴールアクション（フォールバック用）"""
    return [
        "Eビザでの申請ができます",
        "Blanket Lビザでの申請ができます",
        "Lビザ（Individual）での申請ができます",
        "Bビザの申請ができます",
        "契約書に基づくBビザの申請ができます",
        "B-1 in lieu of H-1Bビザの申請ができます",
        "B-1 in lieu of H3ビザの申請ができます",
        "H-1Bビザでの申請ができます",
        "J-1ビザの申請ができます",
    ]


def _get_hardcoded_rules() -> List[Rule]:
    """ハードコードされたルール（フォールバック用）"""
    return _HARDCODED_RULES.copy()


# ハードコードされたルール（JSONファイルが読み込めない場合のフォールバック）
_HARDCODED_RULES: List[Rule] = [
    # ========== Eビザ関連ルール ==========
    Rule(
        id="E001",
        name="Eビザ申請可能",
        conditions=[
            "申請者と会社の国籍が同じです",
            "会社がEビザの条件を満たします",
            "申請者がEビザの条件を満たします"
        ],
        action="Eビザでの申請ができます",
        rule_type=RuleType.MIDDLE,
        visa_type="E"
    ),
    Rule(
        id="E002",
        name="会社Eビザ条件",
        conditions=[
            "会社がEビザの投資の条件を満たします",
            "会社がEビザの貿易の条件を満たします"
        ],
        action="会社がEビザの条件を満たします",
        rule_type=RuleType.MIDDLE,
        is_or_rule=True,
        visa_type="E"
    ),
    Rule(
        id="E003",
        name="投資条件",
        conditions=[
            "減価償却前の設備や建物が30万ドル以上財務諸表の資産に計上されています",
            "30万ドル以上で企業を買収した会社か、買収された会社です",
            "まだ十分な売り上げがなく、これまでに人件費などのランニングコストを含め、30万ドル以上支出しています",
            "会社設立のために、30万ドル以上支出しました（不動産を除く）"
        ],
        action="会社がEビザの投資の条件を満たします",
        rule_type=RuleType.INITIAL,
        is_or_rule=True,
        visa_type="E"
    ),
    Rule(
        id="E004",
        name="貿易条件",
        conditions=[
            "会社の行う貿易の50％が日米間です",
            "会社の行う貿易は継続的です",
            "貿易による利益が会社の経費の80％以上をカバーしています"
        ],
        action="会社がEビザの貿易の条件を満たします",
        rule_type=RuleType.INITIAL,
        visa_type="E"
    ),
    Rule(
        id="E005",
        name="申請者Eビザ条件",
        conditions=[
            "申請者がEビザのマネージャー以上の条件を満たします",
            "申請者がEビザのスタッフの条件を満たします",
            "EビザTDY(short-term needs)の条件を満たします"
        ],
        action="申請者がEビザの条件を満たします",
        rule_type=RuleType.MIDDLE,
        is_or_rule=True,
        visa_type="E"
    ),
    Rule(
        id="E006",
        name="マネージャー以上条件",
        conditions=[
            "米国拠点でEビザでマネージャー以上として認められるポジションに就きます",
            "マネージャー以上のポジションの業務を遂行する十分な能力があります"
        ],
        action="申請者がEビザのマネージャー以上の条件を満たします",
        rule_type=RuleType.MIDDLE,
        visa_type="E"
    ),
    Rule(
        id="E007",
        name="Eビザマネージャーポジション",
        conditions=[
            "CEOなどのオフィサーのポジションに就きます",
            "経営企画のマネージャーなど、米国拠点の経営に関わるポジションに就きます",
            "評価・雇用に責任を持つ複数のフルタイムのスタッフを部下に持つマネージャー以上のポジションに就きます"
        ],
        action="米国拠点でEビザでマネージャー以上として認められるポジションに就きます",
        rule_type=RuleType.INITIAL,
        is_or_rule=True,
        visa_type="E"
    ),
    Rule(
        id="E008",
        name="マネージャー能力",
        conditions=[
            "米国拠点のポジションの業務に深く関連する業務の経験が2年以上あります",
            "マネジメント経験が2年以上あります"
        ],
        action="マネージャー以上のポジションの業務を遂行する十分な能力があります",
        rule_type=RuleType.MIDDLE,
        visa_type="E"
    ),
    Rule(
        id="E009",
        name="マネジメント経験",
        conditions=[
            "2年以上のマネージャー経験があります",
            "マネジメントが求められるプロジェクトマネージャーなどの2年以上の経験があります"
        ],
        action="マネジメント経験が2年以上あります",
        rule_type=RuleType.INITIAL,
        is_or_rule=True,
        visa_type="E"
    ),
    Rule(
        id="E010",
        name="Eビザスタッフ条件",
        conditions=[
            "理系の大学院卒で、米国拠点の技術系の業務に深く関連する3年以上の業務経験があります",
            "理系の学部卒で、米国拠点の技術系の業務に深く関連する4年以上の業務経験があります",
            "米国拠点の業務に深く関連する5年以上の業務経験があります"
        ],
        action="申請者がEビザのスタッフの条件を満たします",
        rule_type=RuleType.INITIAL,
        is_or_rule=True,
        visa_type="E"
    ),
    Rule(
        id="E011",
        name="TDY条件",
        conditions=[
            "2年以内の期間で、目的を限定した派遣理由を説明できます",
            "米国拠点の業務に深く関連する2年以上の業務経験があります"
        ],
        action="EビザTDY(short-term needs)の条件を満たします",
        rule_type=RuleType.INITIAL,
        visa_type="E"
    ),

    # ========== Lビザ関連ルール ==========
    Rule(
        id="L001",
        name="Blanket Lビザ申請可能",
        conditions=[
            "アメリカ以外からアメリカへのグループ内での異動です",
            "会社がBlanket Lビザの条件を満たします",
            "申請者がBlanket Lビザの条件を満たします"
        ],
        action="Blanket Lビザでの申請ができます",
        rule_type=RuleType.MIDDLE,
        visa_type="L"
    ),
    Rule(
        id="L002",
        name="会社Blanket Lビザ条件",
        conditions=[
            "アメリカにある子会社の売り上げの合計が25百万ドル以上です",
            "アメリカにある子会社が1,000人以上ローカル採用をしています",
            "1年間に10人以上Lビザのペティション申請をしています"
        ],
        action="会社がBlanket Lビザの条件を満たします",
        rule_type=RuleType.INITIAL,
        is_or_rule=True,
        visa_type="L"
    ),
    Rule(
        id="L003",
        name="申請者Blanket Lビザ条件",
        conditions=[
            "直近3年のうち1年以上、アメリカ以外のグループ会社に所属していました",
            "Blanket Lビザのマネージャーまたはスタッフの条件を満たします"
        ],
        action="申請者がBlanket Lビザの条件を満たします",
        rule_type=RuleType.MIDDLE,
        visa_type="L"
    ),
    Rule(
        id="L004",
        name="Blanket Lビザマネージャーまたはスタッフ",
        conditions=[
            "Blanket Lビザのマネージャーの条件を満たします",
            "Blanket Lビザスタッフの条件を満たします"
        ],
        action="Blanket Lビザのマネージャーまたはスタッフの条件を満たします",
        rule_type=RuleType.MIDDLE,
        is_or_rule=True,
        visa_type="L"
    ),
    Rule(
        id="L005",
        name="Blanket Lマネージャー条件",
        conditions=[
            "マネージャーとしての経験があります",
            "アメリカでの業務はマネージャーとみなされます"
        ],
        action="Blanket Lビザのマネージャーの条件を満たします",
        rule_type=RuleType.INITIAL,
        visa_type="L"
    ),
    Rule(
        id="L006",
        name="Blanket Lスタッフ条件",
        conditions=[
            "specialized knowledgeがあります",
            "アメリカでの業務はspecialized knowledgeを必要とします"
        ],
        action="Blanket Lビザスタッフの条件を満たします",
        rule_type=RuleType.INITIAL,
        visa_type="L"
    ),
    Rule(
        id="L007",
        name="Individual Lビザ申請可能",
        conditions=[
            "アメリカ以外からアメリカへのグループ内での異動です",
            "申請者がLビザ（Individual）の条件を満たします"
        ],
        action="Lビザ（Individual）での申請ができます",
        rule_type=RuleType.MIDDLE,
        visa_type="L"
    ),
    Rule(
        id="L008",
        name="申請者Individual Lビザ条件",
        conditions=[
            "直近3年のうち1年以上、アメリカ以外のグループ会社に所属していました",
            "Lビザ（Individual）のマネージャーまたはスタッフの条件を満たします"
        ],
        action="申請者がLビザ（Individual）の条件を満たします",
        rule_type=RuleType.MIDDLE,
        visa_type="L"
    ),
    Rule(
        id="L009",
        name="Individual Lマネージャー条件",
        conditions=[
            "マネージャーとしての経験があります",
            "アメリカでの業務はマネージャーとみなされます",
            "アメリカでは大卒、フルタイムの部下が2名以上います"
        ],
        action="Lビザ（Individual）のマネージャーの条件を満たします",
        rule_type=RuleType.INITIAL,
        visa_type="L"
    ),
    Rule(
        id="L010",
        name="Individual Lスタッフ条件",
        conditions=[
            "specialized knowledgeがあります",
            "アメリカでの業務はspecialized knowledgeを必要とします"
        ],
        action="Lビザ（Individual）のスタッフの条件を満たします",
        rule_type=RuleType.INITIAL,
        visa_type="L"
    ),
    Rule(
        id="L011",
        name="Individual Lマネージャーまたはスタッフ",
        conditions=[
            "Lビザ（Individual）のマネージャーの条件を満たします",
            "Lビザ（Individual）のスタッフの条件を満たします"
        ],
        action="Lビザ（Individual）のマネージャーまたはスタッフの条件を満たします",
        rule_type=RuleType.MIDDLE,
        is_or_rule=True,
        visa_type="L"
    ),

    # ========== Bビザ関連ルール ==========
    Rule(
        id="B001",
        name="Bビザ申請可能",
        conditions=[
            "Bビザの申請条件を満たす（ESTAの認証は通る）",
            "Bビザの申請条件を満たす（ESTAの認証は通らない）"
        ],
        action="Bビザの申請ができます",
        rule_type=RuleType.MIDDLE,
        is_or_rule=True,
        visa_type="B"
    ),
    Rule(
        id="B002",
        name="Bビザ条件(ESTA可)",
        conditions=[
            "アメリカでの活動は商用の範囲です",
            "1回の滞在期間は90日を越えます",
            "1回の滞在期間は6か月を越えません"
        ],
        action="Bビザの申請条件を満たす（ESTAの認証は通る）",
        rule_type=RuleType.INITIAL,
        visa_type="B"
    ),
    Rule(
        id="B003",
        name="Bビザ条件(ESTA不可)",
        conditions=[
            "アメリカでの活動は商用の範囲です",
            "1回の滞在期間は6か月を越えません"
        ],
        action="Bビザの申請条件を満たす（ESTAの認証は通らない）",
        rule_type=RuleType.INITIAL,
        visa_type="B"
    ),
    Rule(
        id="B004",
        name="契約書Bビザ",
        conditions=[
            "アメリカの会社に販売した装置や設備のための作業をします",
            "装置や設備の販売を示す契約書や発注書があります",
            "1回の滞在期間は6か月を越えません"
        ],
        action="契約書に基づくBビザの申請ができます",
        rule_type=RuleType.INITIAL,
        visa_type="B"
    ),
    Rule(
        id="B005",
        name="B-1 in lieu of H-1B",
        conditions=[
            "H-1Bビザが必要な専門性の高い作業をします",
            "1回の滞在期間は6か月を越えません"
        ],
        action="B-1 in lieu of H-1Bビザの申請ができます",
        rule_type=RuleType.INITIAL,
        visa_type="B"
    ),
    Rule(
        id="B006",
        name="研修Bビザ",
        conditions=[
            "研修内容は商用の範囲です",
            "研修期間は６か月以内です"
        ],
        action="Bビザの申請ができます",
        rule_type=RuleType.INITIAL,
        visa_type="B"
    ),
    Rule(
        id="B007",
        name="B-1 in lieu of H3",
        conditions=[
            "研修内容は商用の範囲です",
            "研修期間は６か月以内です"
        ],
        action="B-1 in lieu of H3ビザの申請ができます",
        rule_type=RuleType.INITIAL,
        visa_type="B"
    ),

    # ========== H-1Bビザ関連ルール ==========
    Rule(
        id="H001",
        name="H-1Bビザ申請可能",
        conditions=[
            "大卒以上で、専攻内容と業務内容が一致しています",
            "大卒以上で、専攻内容と業務内容が異なりますが、実務経験が3年以上あります",
            "大卒以上ではありませんが、実務経験が(高卒は12年以上、高専卒は3年以上）あります"
        ],
        action="H-1Bビザでの申請ができます",
        rule_type=RuleType.INITIAL,
        is_or_rule=True,
        visa_type="H-1B"
    ),

    # ========== J-1ビザ関連ルール ==========
    Rule(
        id="J001",
        name="J-1ビザ申請可能",
        conditions=[
            "研修にOJTが含まれます",
            "研修期間は18か月以内です",
            "申請者に研修に必要な英語力はあります"
        ],
        action="J-1ビザの申請ができます",
        rule_type=RuleType.INITIAL,
        visa_type="J-1"
    ),
]


# JSONから読み込んだルール（初回アクセス時にロード）
VISA_RULES: List[Rule] = _load_rules_from_json()


def get_all_rules() -> List[Rule]:
    """全ルールを取得"""
    return VISA_RULES.copy()


def get_rules_by_visa_type(visa_type: str) -> List[Rule]:
    """ビザタイプでルールをフィルタ"""
    return [r for r in VISA_RULES if r.visa_type == visa_type]


# ビザタイプの質問順序
VISA_TYPE_ORDER = {"E": 0, "L": 1, "H-1B": 2, "B": 3, "J-1": 4}

def get_goal_rules() -> List[Rule]:
    """ゴールルール（最終結論を導くルール）を取得（E→L→H-1B→B→J-1順）"""
    goal_actions = _load_goal_actions_from_json()
    goal_rules = [r for r in VISA_RULES if r.action in goal_actions]
    return sorted(goal_rules, key=lambda r: VISA_TYPE_ORDER.get(r.visa_type, 99))


def get_all_base_conditions() -> set:
    """全ての基本条件（他のルールの結論ではないもの）を取得"""
    all_conditions = set()
    all_actions = {r.action for r in VISA_RULES}

    for rule in VISA_RULES:
        for cond in rule.conditions:
            if cond not in all_actions:
                all_conditions.add(cond)

    return all_conditions


def get_derived_conditions() -> set:
    """導出可能な条件（他のルールの結論であるもの）を取得"""
    return {r.action for r in VISA_RULES}


def reload_rules():
    """ルールを再読み込み（編集後に呼び出す）"""
    global VISA_RULES
    VISA_RULES = _load_rules_from_json()
    return VISA_RULES


def save_rules(rules_data: dict) -> bool:
    """ルールをJSONファイルに保存（将来の編集機能用）"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, ensure_ascii=False, indent=2)
        reload_rules()
        return True
    except Exception as e:
        print(f"Error saving rules: {e}")
        return False
