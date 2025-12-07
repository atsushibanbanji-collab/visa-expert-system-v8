"""
ビザ選定エキスパートシステム - 推論エンジン
Smalltalk資料のConsultation/WorkingMemoryクラスに相当
バックワードチェイニング（後向き推論）を実装
"""
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from knowledge_base import Rule, VISA_RULES, get_all_rules, get_goal_rules, get_derived_conditions


class FactStatus(Enum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"
    PENDING = "pending"


@dataclass
class WorkingMemory:
    """
    Smalltalk資料のWorkingMemoryクラスに相当
    診断における問題の状況（作業記憶）を扱う
    findings: 所見（利用者の回答）
    hypotheses: 仮説（ルールにより導出された事実）
    """
    findings: Dict[str, FactStatus] = field(default_factory=dict)
    hypotheses: Dict[str, FactStatus] = field(default_factory=dict)
    answer_history: List[Tuple[str, FactStatus]] = field(default_factory=list)

    def get_value(self, condition: str) -> Optional[FactStatus]:
        """作業記憶から指定された要素の値を取り出して返します"""
        if condition in self.findings:
            return self.findings[condition]
        if condition in self.hypotheses:
            return self.hypotheses[condition]
        return None

    def put_finding(self, condition: str, value: FactStatus):
        """利用者の回答を作業記憶に追加"""
        self.findings[condition] = value
        self.answer_history.append((condition, value))

    def put_hypothesis(self, condition: str, value: FactStatus):
        """導出された仮説を作業記憶に追加"""
        self.hypotheses[condition] = value

    def clear_after(self, condition: str):
        """指定した条件以降の回答と依存する仮説をクリア"""
        idx = -1
        for i, (cond, _) in enumerate(self.answer_history):
            if cond == condition:
                idx = i
                break

        if idx >= 0:
            # 該当条件以降の回答を削除
            to_remove = [c for c, _ in self.answer_history[idx:]]
            self.answer_history = self.answer_history[:idx]
            for cond in to_remove:
                if cond in self.findings:
                    del self.findings[cond]
            # 仮説もクリア（再計算が必要）
            self.hypotheses.clear()


@dataclass
class RuleState:
    """ルールの評価状態"""
    rule: Rule
    status: str = "pending"  # pending, evaluating, fired, blocked
    checked_conditions: Dict[str, FactStatus] = field(default_factory=dict)


class InferenceEngine:
    """
    Smalltalk資料のConsultationクラスに相当
    バックワードチェイニングによる推論を実装
    """

    def __init__(self):
        self.working_memory = WorkingMemory()
        self.rules = get_all_rules()
        self.rule_states: Dict[str, RuleState] = {}
        self.current_question: Optional[str] = None
        self.question_queue: List[str] = []
        self.derived_conditions = get_derived_conditions()
        self.reasoning_log: List[str] = []

        # ルール状態を初期化
        for rule in self.rules:
            self.rule_states[rule.id] = RuleState(rule=rule)

    def start_consultation(self):
        """診断を開始"""
        self.reasoning_log.append("診断を開始します。全ビザタイプ（E、B、L、H-1B、J-1）を並行評価します。")
        self._build_question_queue()
        return self._get_next_question()

    def _build_question_queue(self):
        """
        バックワードチェイニングに基づく質問順序を構築
        ゴールから逆算して必要な条件を特定
        ビザタイプごとにグループ化して質問を出す
        導出可能条件も質問として含める（知識のあるユーザーが上位条件で回答可能）
        """
        goal_rules = get_goal_rules()
        needed_conditions: Set[str] = set()  # 基本条件
        derived_needed: Set[str] = set()  # 導出可能条件
        processed: Set[str] = set()

        def collect_conditions(action: str, depth: int = 0):
            """アクションを導出するために必要な条件を再帰的に収集"""
            if action in processed:
                return
            processed.add(action)

            for rule in self.rules:
                if rule.action == action:
                    for cond in rule.conditions:
                        if cond in self.derived_conditions:
                            # 導出可能条件も質問対象に追加
                            derived_needed.add(cond)
                            collect_conditions(cond, depth + 1)
                        else:
                            needed_conditions.add(cond)

        # 全ゴールから逆算
        for goal_rule in goal_rules:
            collect_conditions(goal_rule.action)

        # ビザタイプの優先順序（E → L → B → H-1B → J-1）
        visa_type_order = {"E": 100, "L": 80, "B": 60, "H-1B": 40, "J-1": 20}
        visa_type_list = ["E", "L", "B", "H-1B", "J-1"]

        # ゴールルールの直接条件を特定
        goal_direct_conditions = set()
        for goal_rule in goal_rules:
            for cond in goal_rule.conditions:
                goal_direct_conditions.add(cond)

        # 条件の深さを計算（ゴールからの距離）
        condition_depth: Dict[str, int] = {}

        def calc_depth(action: str, depth: int = 0):
            for rule in self.rules:
                if rule.action == action:
                    for cond in rule.conditions:
                        if cond not in condition_depth or condition_depth[cond] > depth:
                            condition_depth[cond] = depth
                        if cond in self.derived_conditions:
                            calc_depth(cond, depth + 1)

        for goal_rule in goal_rules:
            calc_depth(goal_rule.action, 0)

        # 全条件（基本 + 導出可能）を統合
        all_conditions = needed_conditions | derived_needed

        # 条件をビザタイプごとに分類
        visa_conditions: Dict[str, List[str]] = {vt: [] for vt in visa_type_list}
        multi_visa_conditions: List[str] = []

        for cond in all_conditions:
            related_visa_types = set()
            for rule in self.rules:
                if cond in rule.conditions:
                    related_visa_types.add(rule.visa_type)

            if len(related_visa_types) > 1:
                multi_visa_conditions.append(cond)
                best_visa = max(related_visa_types, key=lambda vt: visa_type_order.get(vt, 0))
                visa_conditions[best_visa].append(cond)
            elif len(related_visa_types) == 1:
                visa_type = list(related_visa_types)[0]
                if visa_type in visa_conditions:
                    visa_conditions[visa_type].append(cond)

        # ルール内での条件定義順序を計算（ゴールルールから辿る）
        # E001: [国籍, 会社, 申請者] → 国籍=0, 会社=1, 申請者=2
        condition_order_in_rule: Dict[str, int] = {}

        def calc_condition_order(action: str, base_order: int = 0):
            """ゴールから再帰的に条件の順序を計算"""
            for rule in self.rules:
                if rule.action == action:
                    for idx, cond in enumerate(rule.conditions):
                        # ルール内での順序を記録（小さい=先に質問）
                        order = base_order * 1000 + idx
                        if cond not in condition_order_in_rule or condition_order_in_rule[cond] > order:
                            condition_order_in_rule[cond] = order
                        # 導出可能条件なら再帰
                        if cond in self.derived_conditions:
                            calc_condition_order(cond, order)

        for goal_rule in goal_rules:
            calc_condition_order(goal_rule.action, 0)

        # 各ビザタイプ内での優先順位を計算
        def get_condition_priority_within_visa(cond: str, visa_type: str) -> Tuple[int, int]:
            """
            ビザタイプ内での条件の優先度を計算
            戻り値: (メイン優先度, サブ優先度) - 大きい方が先に質問
            メイン優先度: ゴール直接条件 > 深さ順
            サブ優先度: ルール内での定義順序（小さい=先）の逆数
            """
            main_priority = 0

            # ゴールルールの直接条件にはボーナス
            if cond in goal_direct_conditions:
                main_priority += 10000

            # 基本条件を先に、導出可能条件を後に
            if cond not in self.derived_conditions:
                main_priority += 5000
            else:
                depth = condition_depth.get(cond, 0)
                main_priority += depth * 100

            # 複数のビザに関連する条件にはボーナス
            if cond in multi_visa_conditions:
                main_priority += 50

            # サブ優先度: ルール内での定義順序（小さい番号が先に来るように反転）
            order = condition_order_in_rule.get(cond, 9999)
            sub_priority = -order  # 小さい順序番号 → 大きい優先度

            return (main_priority, sub_priority)

        # 各ビザタイプ内で条件をソート（基本条件が先、導出可能条件が後）
        for visa_type in visa_type_list:
            visa_conditions[visa_type].sort(
                key=lambda c: get_condition_priority_within_visa(c, visa_type),
                reverse=True
            )

        # ビザタイプの順序で質問キューを構築
        self.question_queue = []
        for visa_type in visa_type_list:
            self.question_queue.extend(visa_conditions[visa_type])

    def _get_next_question(self) -> Optional[str]:
        """
        次の質問を取得

        ロジック:
        1. ゴールルールから順に、未解決の条件を探す
        2. 各ルールの条件を定義順に確認
        3. 条件が未回答なら、その条件を質問
        4. 条件がUNKNOWNで導出可能なら、その導出ルールを再帰的に探索
        5. 条件がTRUE/FALSEなら次の条件へ
        """
        goal_rules = get_goal_rules()

        for goal_rule in goal_rules:
            # ゴールルールがブロック/uncertainされていたらスキップ
            if self.rule_states[goal_rule.id].status in ["blocked", "uncertain"]:
                continue

            # ゴールルールの条件を順に確認
            question = self._find_next_question_for_rule(goal_rule)
            if question:
                self.current_question = question
                self._mark_related_rules_evaluating(question)
                return question

        return None

    def _find_next_question_for_rule(self, rule, visited: Set[str] = None) -> Optional[str]:
        """
        ルールの条件を順に確認し、次の質問を見つける

        ロジック:
        1. 条件を定義順に確認
        2. 未回答(None/PENDING)なら、その条件を質問として返す
        3. UNKNOWNで導出可能条件なら、導出ルールを再帰探索
        4. TRUE/FALSEなら次の条件へ
        5. ブロック伝播：FALSEがあればルール全体をスキップ（ANDルールの場合）
        """
        if visited is None:
            visited = set()

        if rule.id in visited:
            return None
        visited.add(rule.id)

        # ルールがブロック/uncertainされていたらスキップ
        if self.rule_states[rule.id].status in ["blocked", "uncertain"]:
            return None

        for cond in rule.conditions:
            val = self._get_effective_value(cond)

            # 未回答の条件
            if val is None or val == FactStatus.PENDING:
                # この条件を質問として返す
                if not self._should_skip_question(cond):
                    return cond

            # UNKNOWNで導出可能条件
            elif val == FactStatus.UNKNOWN and cond in self.derived_conditions:
                # 導出ルールを探す
                deriving_rules = [r for r in self.rules if r.action == cond]
                for dr in deriving_rules:
                    # 導出ルールがブロック/uncertainされていなければ再帰探索
                    if self.rule_states[dr.id].status not in ["blocked", "uncertain"]:
                        sub_question = self._find_next_question_for_rule(dr, visited.copy())
                        if sub_question:
                            return sub_question

            # FALSEの場合、ANDルールならこのルールはブロック
            elif val == FactStatus.FALSE:
                if not rule.is_or_rule:
                    return None

            # TRUE/UNKNOWNは次の条件へ

        return None

    def _mark_related_rules_evaluating(self, condition: str):
        """現在の質問に関連するルールを評価中状態にする"""
        # この条件をIF条件として使っているルールのみを評価中にする
        for rule_id, state in self.rule_states.items():
            if condition in state.rule.conditions:
                if state.status == "pending":
                    state.status = "evaluating"

    def _is_ancestor_condition_resolved(self, condition: str, visited: Set[str] = None, depth: int = 0) -> bool:
        """
        再帰的に上位の条件をチェックし、いずれかの上位条件がTRUEまたはFALSEで確定なら
        この条件は既に解決されたと判断する

        例：
        - E001のactionは「Eビザでの申請ができます」
        - E001の条件に「申請者がEビザの条件を満たします」がある
        - E005のactionは「申請者がEビザの条件を満たします」
        - E005の条件に「申請者がEビザのマネージャー以上の条件を満たします」がある
        - E006のactionは「申請者がEビザのマネージャー以上の条件を満たします」

        もし「申請者がEビザの条件を満たします」がTRUEなら、
        E006、E007等の下位条件はすべてスキップされるべき

        重要：
        - ORルールで導出されたTRUE（hypotheses）は、ユーザーのUNKNOWN回答（findings）より優先
        - ANDルールでblocked（FALSE導出）の場合も、その下位条件はスキップすべき
        """
        # 深度制限（安全装置）
        if depth > 20:
            return False

        if visited is None:
            visited = set()

        if condition in visited:
            return False
        visited.add(condition)

        # この条件を使っている全てのルールを取得
        parent_rules = [r for r in self.rules if condition in r.conditions]

        for rule in parent_rules:
            action = rule.action

            # まずhypotheses（推論結果）をチェック
            # ORルールで導出されたTRUEは、ユーザーのUNKNOWN回答より優先する
            if action in self.working_memory.hypotheses:
                hypo_val = self.working_memory.hypotheses[action]
                if hypo_val == FactStatus.TRUE:
                    # 推論によりTRUEが導出されている → この条件はスキップすべき
                    return True
                if hypo_val == FactStatus.FALSE:
                    # 推論によりFALSEが導出されている → この条件はスキップすべき
                    # （親がブロックされているので、この条件を聞いても意味がない）
                    return True

            # 次にfindings（ユーザー回答）をチェック
            if action in self.working_memory.findings:
                find_val = self.working_memory.findings[action]
                if find_val == FactStatus.TRUE:
                    # ユーザーが直接TRUEと回答 → この条件はスキップすべき
                    return True
                if find_val == FactStatus.FALSE:
                    # ユーザーが直接FALSEと回答 → この条件はスキップすべき
                    return True

            # さらに上位の条件を再帰的にチェック
            # rule.actionをconditionとして使っている、さらに上位のルールがあるか
            if self._is_ancestor_condition_resolved(action, visited, depth + 1):
                return True

        return False

    def _has_unresolved_prior_condition(self, condition: str) -> bool:
        """
        ルール内で、この条件より前の条件が未解決かチェック
        例: E001の条件が [国籍, 会社, 申請者] の場合
        - 「会社」を聞く前に「国籍」が解決している必要がある
        - 「申請者」を聞く前に「国籍」「会社」が解決している必要がある

        ORルールの場合は例外:
        - 前の条件がUNKNOWNでも、次の条件を聞ける
        - どちらか一方がTRUEなら発火するため
        """
        # この条件を使う全てのルールをチェック
        related_rules = [r for r in self.rules if condition in r.conditions]

        for rule in related_rules:
            # ORルールの場合、順序制約は緩和する
            # （どの条件がTRUEでも発火するため、並行して聞いてよい）
            if rule.is_or_rule:
                continue

            # このルール内での条件の位置を取得
            try:
                cond_index = rule.conditions.index(condition)
            except ValueError:
                continue

            # この条件より前の条件をチェック
            for i in range(cond_index):
                prior_cond = rule.conditions[i]
                # hypothesesのTRUE/FALSEを優先（導出された値を考慮）
                val = self._get_effective_value(prior_cond)

                # 前の条件が未解決（None, PENDING）の場合
                if val is None or val == FactStatus.PENDING:
                    # この前の条件はまだ質問されていない
                    return True

                # TRUE/FALSEが確定していれば、この前の条件は解決済み
                if val == FactStatus.TRUE or val == FactStatus.FALSE:
                    continue  # 次の前条件をチェック

                # UNKNOWNの場合、導出可能条件なら下位条件が解決するまで待つ
                if val == FactStatus.UNKNOWN and prior_cond in self.derived_conditions:
                    # 下位条件がまだ探索中かチェック
                    deriving_rules = [r for r in self.rules if r.action == prior_cond]
                    for dr in deriving_rules:
                        if self.rule_states[dr.id].status not in ["fired", "blocked", "uncertain"]:
                            # まだ評価中のルールがある
                            return True

        return False

    def _should_skip_question(self, condition: str) -> bool:
        """この質問をスキップすべきかチェック"""
        # この条件を使うルールを取得
        related_rules = [r for r in self.rules if condition in r.conditions]

        if not related_rules:
            return True

        # 【根本治療】再帰的に上位条件をチェック
        # いずれかの上位条件（祖先）が既にTRUEなら、この条件は聞く必要がない
        if self._is_ancestor_condition_resolved(condition):
            return True

        # 【順序制御】ルール内で前の条件が未解決なら、この条件はスキップ
        if self._has_unresolved_prior_condition(condition):
            return True

        # AND条件最適化：全ての関連ルールがブロックされているかチェック
        all_blocked = True
        for rule in related_rules:
            state = self.rule_states[rule.id]
            if state.status != "blocked":
                # ルールがまだブロックされていない場合
                # AND条件で他の条件がFALSEでないかチェック
                if not rule.is_or_rule:
                    is_blocked = False
                    for cond in rule.conditions:
                        if cond != condition:
                            val = self.working_memory.get_value(cond)
                            if val == FactStatus.FALSE:
                                is_blocked = True
                                break
                    if not is_blocked:
                        all_blocked = False
                        break
                else:
                    all_blocked = False
                    break

        return all_blocked

    def _expand_unknown_condition(self, condition: str):
        """
        「わからない」と回答された導出可能条件の下位条件を質問キューの先頭に挿入
        バックワードチェイニングの深さ優先探索を実現
        """
        # この条件を導出するルールを見つける
        deriving_rules = [r for r in self.rules if r.action == condition]

        if not deriving_rules:
            return

        # 下位条件を収集（まだ回答されていないもの）
        sub_conditions = []
        for rule in deriving_rules:
            for cond in rule.conditions:
                if cond not in sub_conditions:
                    val = self.working_memory.get_value(cond)
                    if val is None or val == FactStatus.PENDING:
                        sub_conditions.append(cond)

        if not sub_conditions:
            return

        # 下位条件をソート（基本条件を先に、導出可能条件を後に）
        def sub_cond_priority(cond):
            if cond not in self.derived_conditions:
                return 1000  # 基本条件優先
            return 0

        sub_conditions.sort(key=sub_cond_priority, reverse=True)

        # 質問キューの先頭に挿入（既存のものは重複を避けて削除）
        for cond in sub_conditions:
            if cond in self.question_queue:
                self.question_queue.remove(cond)

        # 先頭に逆順で挿入（最初の要素が最初に聞かれるように）
        for cond in reversed(sub_conditions):
            self.question_queue.insert(0, cond)

        self.reasoning_log.append(f"展開: 「{condition}」の下位条件を探索します")

    def answer_question(self, condition: str, answer: str) -> Dict[str, Any]:
        """質問に回答"""
        if answer == "yes":
            status = FactStatus.TRUE
        elif answer == "no":
            status = FactStatus.FALSE
        else:
            status = FactStatus.UNKNOWN

        self.working_memory.put_finding(condition, status)
        self.reasoning_log.append(f"回答: 「{condition}」→ {answer}")

        # 「わからない」の場合、導出可能条件なら下位条件を先頭に挿入
        if status == FactStatus.UNKNOWN and condition in self.derived_conditions:
            self._expand_unknown_condition(condition)

        # ルール評価と仮説導出をループで収束するまで繰り返す
        # （E003発火 → 投資条件TRUE導出 → E002発火 → 会社条件TRUE導出 のような連鎖を処理）
        max_iterations = 10
        for _ in range(max_iterations):
            prev_hypotheses = dict(self.working_memory.hypotheses)
            prev_statuses = {rid: s.status for rid, s in self.rule_states.items()}

            self._evaluate_rules()
            self._propagate_inferences()

            # 変化がなければ収束
            if (self.working_memory.hypotheses == prev_hypotheses and
                all(self.rule_states[rid].status == prev_statuses[rid] for rid in self.rule_states)):
                break

        # 次の質問を取得
        next_q = self._get_next_question()

        # 診断完了チェック
        is_complete = next_q is None or self._is_diagnosis_complete()

        result = {
            "next_question": next_q,
            "is_complete": is_complete,
            "derived_facts": list(self.working_memory.hypotheses.keys()),
            "rules_status": self._get_rules_display_info()
        }

        if is_complete:
            result["diagnosis_result"] = self._generate_result()

        return result

    def _get_effective_value(self, condition: str) -> Optional[FactStatus]:
        """
        条件の実効値を取得
        導出可能条件の場合、hypothesesのTRUEはfindingsのUNKNOWNより優先する
        （ユーザーが「わからない」と回答しても、下位ルールで導出されたTRUEを使う）
        """
        finding_val = self.working_memory.findings.get(condition)
        hypo_val = self.working_memory.hypotheses.get(condition)

        # 導出可能条件で、hypothesesにTRUEがある場合は優先
        if condition in self.derived_conditions:
            if hypo_val == FactStatus.TRUE:
                return FactStatus.TRUE
            if hypo_val == FactStatus.FALSE:
                # 全ての導出ルールがブロックされている場合のFALSE
                return FactStatus.FALSE

        # findingsがあればそれを返す
        if finding_val is not None:
            return finding_val

        # hypothesesがあればそれを返す
        if hypo_val is not None:
            return hypo_val

        return None

    def _evaluate_rules(self):
        """全ルールを評価してステータスを更新"""
        for rule_id, state in self.rule_states.items():
            rule = state.rule

            # 各条件をチェック
            all_true = True
            any_true = False
            any_false = False
            has_unknown = False

            for cond in rule.conditions:
                # 実効値を取得（hypothesesのTRUEをfindingsのUNKNOWNより優先）
                val = self._get_effective_value(cond)
                state.checked_conditions[cond] = val if val else FactStatus.PENDING

                if val == FactStatus.TRUE:
                    any_true = True
                elif val == FactStatus.FALSE:
                    any_false = True
                    all_true = False
                elif val == FactStatus.UNKNOWN:
                    has_unknown = True
                    all_true = False
                else:
                    all_true = False

            # ルールステータスを更新
            # blocked: FALSEが原因で不可（赤表示）
            # uncertain: UNKNOWNが原因で判定不能（黄色表示）
            if rule.is_or_rule:
                # ORルール: 1つでもTRUEなら発火
                if any_true:
                    state.status = "fired"
                else:
                    # 全条件がFALSEまたはUNKNOWN（解決不能）かチェック
                    all_resolved_negative = True
                    has_any_unknown = False
                    has_any_false = False
                    for cond in rule.conditions:
                        val = state.checked_conditions.get(cond)
                        if val == FactStatus.TRUE:
                            all_resolved_negative = False
                            break
                        elif val == FactStatus.UNKNOWN:
                            has_any_unknown = True
                            # UNKNOWNだが、導出可能条件でまだ評価中ならブロックしない
                            if cond in self.derived_conditions:
                                deriving_rules = [r for r in self.rules if r.action == cond]
                                for dr in deriving_rules:
                                    if self.rule_states[dr.id].status not in ["fired", "blocked", "uncertain"]:
                                        all_resolved_negative = False
                                        break
                                if not all_resolved_negative:
                                    break
                            # 基本条件のUNKNOWNは解決不能（uncertain扱い）
                        elif val == FactStatus.FALSE:
                            has_any_false = True
                        elif val is None or val == FactStatus.PENDING:
                            # まだ回答されていない条件がある
                            all_resolved_negative = False
                            break

                    if all_resolved_negative:
                        # UNKNOWNが含まれていれば uncertain、FALSEのみなら blocked
                        if has_any_unknown and not has_any_false:
                            state.status = "uncertain"
                        elif has_any_unknown:
                            # UNKNOWNとFALSE両方 → uncertain（判定不能を優先）
                            state.status = "uncertain"
                        else:
                            state.status = "blocked"
            else:
                # ANDルール: 全条件TRUEで発火
                if all_true:
                    state.status = "fired"
                elif any_false:
                    # FALSEがあればブロック
                    state.status = "blocked"
                elif has_unknown:
                    # UNKNOWNがある場合、このルールがゴールルールかどうかで判定を分ける
                    # 非ゴールルール（導出ルール）はUNKNOWNでuncertain
                    # ゴールルールは後続条件を聞く価値があるのでブロックしない
                    goal_rules = get_goal_rules()
                    is_goal_rule = rule.id in [gr.id for gr in goal_rules]
                    if not is_goal_rule:
                        state.status = "uncertain"

    def _propagate_inferences(self):
        """発火したルールから仮説を導出"""
        max_iterations = 100  # 無限ループ防止
        iteration = 0
        changed = True
        while changed and iteration < max_iterations:
            iteration += 1
            changed = False
            for rule_id, state in self.rule_states.items():
                if state.status == "fired":
                    action = state.rule.action
                    if self.working_memory.get_value(action) != FactStatus.TRUE:
                        self.working_memory.put_hypothesis(action, FactStatus.TRUE)
                        self.reasoning_log.append(f"導出: 「{action}」（ルール {rule_id} が発火）")
                        changed = True

                        # 依存ルールのブロック状態を更新
                        self._update_dependent_rules(action, FactStatus.TRUE)

                elif state.status in ["blocked", "uncertain"]:
                    action = state.rule.action
                    # OR条件でない場合のみブロック/uncertain伝播
                    if not state.rule.is_or_rule:
                        can_derive = False
                        for other_state in self.rule_states.values():
                            if other_state.rule.action == action and other_state.status not in ["blocked", "uncertain"]:
                                can_derive = True
                                break
                        if not can_derive and self.working_memory.get_value(action) != FactStatus.FALSE:
                            self.working_memory.put_hypothesis(action, FactStatus.FALSE)
                            changed = True
                            self._update_dependent_rules(action, FactStatus.FALSE)

    def _update_dependent_rules(self, condition: str, status: FactStatus):
        """条件のステータス変更に応じて依存ルールを更新"""
        for state in self.rule_states.values():
            if condition in state.rule.conditions:
                state.checked_conditions[condition] = status

    def _is_diagnosis_complete(self) -> bool:
        """診断完了かチェック"""
        goal_rules = get_goal_rules()

        for goal_rule in goal_rules:
            state = self.rule_states.get(goal_rule.id)
            if state and state.status not in ["fired", "blocked", "uncertain"]:
                # まだ評価中のゴールがある
                return False

        return True

    def _generate_result(self) -> Dict[str, Any]:
        """診断結果を生成"""
        applicable_visas = []
        conditional_visas = []
        unknown_conditions = []

        goal_rules = get_goal_rules()

        for goal_rule in goal_rules:
            state = self.rule_states.get(goal_rule.id)
            if state:
                if state.status == "fired":
                    applicable_visas.append({
                        "visa": goal_rule.action,
                        "type": goal_rule.visa_type
                    })
                elif state.status != "blocked":
                    # 条件付きで可能な場合
                    unknowns = []
                    for cond in goal_rule.conditions:
                        val = self.working_memory.get_value(cond)
                        if val == FactStatus.UNKNOWN:
                            unknowns.append(cond)
                    if unknowns:
                        conditional_visas.append({
                            "visa": goal_rule.action,
                            "type": goal_rule.visa_type,
                            "unknown_conditions": unknowns
                        })

        # わからない回答の一覧
        for cond, status in self.working_memory.findings.items():
            if status == FactStatus.UNKNOWN:
                unknown_conditions.append(cond)

        return {
            "applicable_visas": applicable_visas,
            "conditional_visas": conditional_visas,
            "unknown_conditions": unknown_conditions,
            "reasoning_log": self.reasoning_log
        }

    def _get_rules_display_info(self) -> List[Dict[str, Any]]:
        """推論画面表示用のルール情報を取得"""
        result = []

        for rule_id, state in self.rule_states.items():
            rule = state.rule
            conditions_info = []

            for cond in rule.conditions:
                val = self.working_memory.get_value(cond)
                is_derived = cond in self.derived_conditions

                if val == FactStatus.TRUE:
                    status = "true"
                elif val == FactStatus.FALSE:
                    status = "false"
                elif val == FactStatus.UNKNOWN:
                    status = "unknown"
                else:
                    status = "unchecked"

                conditions_info.append({
                    "text": cond,
                    "status": status,
                    "is_derived": is_derived
                })

            result.append({
                "id": rule.id,
                "name": rule.name,
                "visa_type": rule.visa_type,
                "conditions": conditions_info,
                "conclusion": rule.action,
                "status": state.status,
                "is_and_rule": not rule.is_or_rule,
                "operator": "AND" if not rule.is_or_rule else "OR"
            })

        return result

    def go_back(self, steps: int = 1) -> Dict[str, Any]:
        """前の質問に戻る"""
        if len(self.working_memory.answer_history) < steps:
            steps = len(self.working_memory.answer_history)

        if steps > 0:
            # 戻る地点の条件を取得
            target_idx = len(self.working_memory.answer_history) - steps
            if target_idx >= 0:
                target_cond = self.working_memory.answer_history[target_idx][0]

                # 戻る前に、これまでに質問された条件のリストを保持
                # （target_condを含めて、その地点までに質問された全ての条件）
                asked_conditions_up_to_target = [
                    cond for cond, _ in self.working_memory.answer_history[:target_idx + 1]
                ]

                self.working_memory.clear_after(target_cond)

                # ルール状態をリセット
                for state in self.rule_states.values():
                    state.status = "pending"
                    state.checked_conditions.clear()

                # 質問キューを再構築
                self._build_question_queue()

                # 現在の回答に基づいてルールを再評価
                self._evaluate_rules()
                self._propagate_inferences()

                self.current_question = target_cond

                # これまでに質問された全ての条件に関連するルールを「evaluating」状態にする
                # （巻き戻しても、それまでの履歴を表示する）
                for cond in asked_conditions_up_to_target:
                    self._mark_related_rules_evaluating(cond)

        return {
            "current_question": self.current_question,
            "answered_questions": [
                {"condition": c, "answer": s.value}
                for c, s in self.working_memory.answer_history
            ],
            "rules_status": self._get_rules_display_info()
        }

    def restart(self):
        """最初からやり直し"""
        self.__init__()
        return self.start_consultation()

    def get_current_state(self) -> Dict[str, Any]:
        """現在の状態を取得"""
        is_complete = self.current_question is None or self._is_diagnosis_complete()

        result = {
            "current_question": self.current_question,
            "answered_questions": [
                {"condition": c, "answer": s.value}
                for c, s in self.working_memory.answer_history
            ],
            "rules_status": self._get_rules_display_info(),
            "derived_facts": list(self.working_memory.hypotheses.keys()),
            "is_complete": is_complete
        }

        if is_complete:
            result["diagnosis_result"] = self._generate_result()

        return result

    def get_related_visa_types(self, condition: str) -> List[str]:
        """条件に関連するビザタイプを取得"""
        visa_types = set()
        for rule in self.rules:
            if condition in rule.conditions:
                visa_types.add(rule.visa_type)
        return list(visa_types)
