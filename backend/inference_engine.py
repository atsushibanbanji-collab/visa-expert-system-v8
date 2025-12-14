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


class RuleStatus(Enum):
    """ルールの評価状態を表すEnum"""
    PENDING = "pending"
    EVALUATING = "evaluating"
    FIRED = "fired"
    BLOCKED = "blocked"
    UNCERTAIN = "uncertain"

    @classmethod
    def is_resolved(cls, status: "RuleStatus") -> bool:
        """ルールが解決済み（発火、ブロック、または不確定）かどうか"""
        return status in (cls.FIRED, cls.BLOCKED, cls.UNCERTAIN)

    @classmethod
    def is_negative(cls, status: "RuleStatus") -> bool:
        """ルールが否定的な結果（ブロックまたは不確定）かどうか"""
        return status in (cls.BLOCKED, cls.UNCERTAIN)


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
    status: RuleStatus = RuleStatus.PENDING
    checked_conditions: Dict[str, FactStatus] = field(default_factory=dict)


class InferenceEngine:
    """
    Smalltalk資料のConsultationクラスに相当
    バックワードチェイニングによる推論を実装
    """

    # クラス定数: 反復処理の最大回数
    MAX_EVALUATION_ITERATIONS = 10
    MAX_PROPAGATION_ITERATIONS = 100

    # FactStatus → 表示用文字列のマッピング
    FACT_STATUS_DISPLAY = {
        FactStatus.TRUE: "true",
        FactStatus.FALSE: "false",
        FactStatus.UNKNOWN: "unknown",
    }

    def __init__(self):
        self.working_memory = WorkingMemory()
        self.rules = get_all_rules()
        self.rule_states: Dict[str, RuleState] = {}
        self.current_question: Optional[str] = None
        self.derived_conditions = get_derived_conditions()
        self.reasoning_log: List[str] = []

        # ルール状態を初期化
        for rule in self.rules:
            self.rule_states[rule.id] = RuleState(rule=rule)

    def start_consultation(self):
        """診断を開始"""
        self.reasoning_log.append("診断を開始します。全ビザタイプ（E、B、L、H-1B、J-1）を並行評価します。")
        return self._get_next_question()

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
            # ゴールルールが解決済み（FIRED/BLOCKED）ならスキップ
            # FIRED: すでに申請可能と判定されたので、さらなる質問は不要
            # BLOCKED: 不可と判定されたので、さらなる質問は不要
            # UNCERTAIN: 探索を続ける（導出可能条件の下位ルールがまだ評価できる可能性）
            if self.rule_states[goal_rule.id].status in (RuleStatus.BLOCKED, RuleStatus.FIRED):
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

        # ルールが解決済み（FIRED/BLOCKED）ならスキップ
        # FIRED: ORルールで1つの条件がTRUEなら、残りの条件を質問する必要なし
        # BLOCKED: ANDルールでFALSEがあれば、他の条件を質問する必要なし
        # UNCERTAIN: 質問を続ける（導出可能条件の下位ルールがまだ評価できる可能性）
        if self.rule_states[rule.id].status in (RuleStatus.BLOCKED, RuleStatus.FIRED):
            return None

        for cond in rule.conditions:
            val = self._get_effective_value(cond)

            # 未回答の条件 → 質問として返す
            if val is None or val == FactStatus.PENDING:
                return cond

            # UNKNOWNで導出可能条件
            elif val == FactStatus.UNKNOWN and cond in self.derived_conditions:
                # 導出ルールを探す
                deriving_rules = self._get_deriving_rules(cond)
                for dr in deriving_rules:
                    # 導出ルールがFIRED/BLOCKEDなら再帰探索不要
                    if self.rule_states[dr.id].status not in (RuleStatus.BLOCKED, RuleStatus.FIRED):
                        sub_question = self._find_next_question_for_rule(dr, visited.copy())
                        if sub_question:
                            return sub_question

            # FALSEの場合、ANDルールならこのルールはブロック
            elif val == FactStatus.FALSE:
                if not rule.is_or_rule:
                    return None

            # TRUEの場合、ORルールならこのルールは発火済み（質問不要）
            elif val == FactStatus.TRUE:
                if rule.is_or_rule:
                    return None

            # UNKNOWNは次の条件へ

        return None

    def _mark_related_rules_evaluating(self, condition: str):
        """現在の質問に関連するルールを評価中状態にする"""
        # この条件をIF条件として使っているルールのみを評価中にする
        for rule_id, state in self.rule_states.items():
            if condition in state.rule.conditions:
                if state.status == RuleStatus.PENDING:
                    state.status = RuleStatus.EVALUATING

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

        # ルール評価と仮説導出をループで収束するまで繰り返す
        # （E003発火 → 投資条件TRUE導出 → E002発火 → 会社条件TRUE導出 のような連鎖を処理）
        for _ in range(self.MAX_EVALUATION_ITERATIONS):
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


    def _get_deriving_rules(self, condition: str) -> List[Rule]:
        """条件を導出するルールを取得"""
        return [r for r in self.rules if r.action == condition]

    def _is_deriving_rule_still_evaluating(self, condition: str) -> bool:
        """導出可能条件に対して、まだ評価中の導出ルールがあるかチェック"""
        if condition not in self.derived_conditions:
            return False
        deriving_rules = self._get_deriving_rules(condition)
        for dr in deriving_rules:
            if not RuleStatus.is_resolved(self.rule_states[dr.id].status):
                return True
        return False

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
                    state.status = RuleStatus.FIRED
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
                                deriving_rules = self._get_deriving_rules(cond)
                                for dr in deriving_rules:
                                    if not RuleStatus.is_resolved(self.rule_states[dr.id].status):
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
                        state.status = RuleStatus.UNCERTAIN if has_any_unknown else RuleStatus.BLOCKED
            else:
                # ANDルール: 全条件TRUEで発火
                if all_true:
                    state.status = RuleStatus.FIRED
                elif any_false:
                    # FALSEがあればブロック
                    state.status = RuleStatus.BLOCKED
                elif has_unknown:
                    # UNKNOWNがある場合でも、全条件を質問してから判定する
                    # 「わからない」は「いいえ」ではなく「保留（はい寄り）」
                    # 最終的に「この条件を満たせば申請できます」と顧客に伝えるため
                    # 全条件が回答済みかチェック
                    all_answered = True
                    for cond in rule.conditions:
                        val = self._get_effective_value(cond)
                        if val is None or val == FactStatus.PENDING:
                            all_answered = False
                            break

                    if all_answered:
                        # 全条件回答済みでUNKNOWNあり → uncertain
                        state.status = RuleStatus.UNCERTAIN
                    # まだ未回答条件があれば、evaluating状態を維持（質問を続ける）

    def _propagate_inferences(self):
        """発火したルールから仮説を導出"""
        iteration = 0
        changed = True
        while changed and iteration < self.MAX_PROPAGATION_ITERATIONS:
            iteration += 1
            changed = False
            for rule_id, state in self.rule_states.items():
                if state.status == RuleStatus.FIRED:
                    action = state.rule.action
                    if self.working_memory.get_value(action) != FactStatus.TRUE:
                        self.working_memory.put_hypothesis(action, FactStatus.TRUE)
                        self.reasoning_log.append(f"導出: 「{action}」（ルール {rule_id} が発火）")
                        changed = True

                        # 依存ルールのブロック状態を更新
                        self._update_dependent_rules(action, FactStatus.TRUE)

                elif RuleStatus.is_negative(state.status):
                    action = state.rule.action
                    # OR条件でない場合のみブロック/uncertain伝播
                    if not state.rule.is_or_rule:
                        can_derive = False
                        for other_state in self.rule_states.values():
                            if other_state.rule.action == action and not RuleStatus.is_negative(other_state.status):
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
            if state and not RuleStatus.is_resolved(state.status):
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
                if state.status == RuleStatus.FIRED:
                    applicable_visas.append({
                        "visa": goal_rule.action,
                        "type": goal_rule.visa_type,
                        "rule_id": goal_rule.id
                    })
                elif state.status != RuleStatus.BLOCKED:
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
                            "rule_id": goal_rule.id,
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

                status = self.FACT_STATUS_DISPLAY.get(val, "unchecked")

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
                "status": state.status.value,  # Enum → 文字列に変換
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
                    state.status = RuleStatus.PENDING
                    state.checked_conditions.clear()

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
