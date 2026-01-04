"""
推論エンジン - バックワードチェイニング実装
"""
from typing import Dict, List, Optional, Set, Any

from core import Rule, FactStatus, RuleStatus, VISA_TYPE_ORDER
from knowledge import get_all_rules, get_goal_rules, get_derived_conditions
from .working_memory import WorkingMemory, RuleState
from .evaluator import RuleEvaluator


class InferenceEngine:
    """推論エンジンクラス

    Smalltalk資料のConsultationクラスに相当。
    バックワードチェイニングによる推論を実装。
    """

    MAX_EVALUATION_ITERATIONS = 10
    MAX_PROPAGATION_ITERATIONS = 100

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

        for rule in self.rules:
            self.rule_states[rule.id] = RuleState(rule=rule)

        self.evaluator = RuleEvaluator(
            self.working_memory,
            self.rule_states,
            self.derived_conditions,
            self.rules
        )

    def start_consultation(self) -> Optional[str]:
        """診断を開始"""
        self.reasoning_log.append("診断を開始します。全ビザタイプ（E、B、L、H-1B、J-1）を並行評価します。")
        return self._get_next_question()

    def answer_question(self, condition: str, answer: str) -> Dict[str, Any]:
        """質問に回答"""
        status = {"yes": FactStatus.TRUE, "no": FactStatus.FALSE}.get(answer, FactStatus.UNKNOWN)
        self.working_memory.put_finding(condition, status)
        self.reasoning_log.append(f"回答: 「{condition}」→ {answer}")

        for _ in range(self.MAX_EVALUATION_ITERATIONS):
            prev_hypotheses = dict(self.working_memory.hypotheses)
            prev_statuses = {rid: s.status for rid, s in self.rule_states.items()}

            self.evaluator.evaluate_all_rules()
            self._propagate_inferences()

            if (self.working_memory.hypotheses == prev_hypotheses and
                all(self.rule_states[rid].status == prev_statuses[rid] for rid in self.rule_states)):
                break

        next_q = self._get_next_question()
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

    def _get_next_question(self) -> Optional[str]:
        """次の質問を取得"""
        goal_rules = get_goal_rules()

        for goal_rule in goal_rules:
            if self.rule_states[goal_rule.id].status in (RuleStatus.BLOCKED, RuleStatus.FIRED):
                continue

            question = self._find_next_question_for_rule(goal_rule)
            if question:
                self.current_question = question
                self.evaluator.mark_related_rules_evaluating(question)
                return question

        return None

    def _find_next_question_for_rule(self, rule: Rule, visited: Set[str] = None) -> Optional[str]:
        """ルールの条件を確認し、次の質問を見つける"""
        if visited is None:
            visited = set()

        if rule.id in visited:
            return None
        visited.add(rule.id)

        if self.rule_states[rule.id].status in (RuleStatus.BLOCKED, RuleStatus.FIRED):
            return None

        for cond in rule.conditions:
            val = self.evaluator.get_effective_value(cond)

            if val is None or val == FactStatus.PENDING:
                return cond

            elif val == FactStatus.UNKNOWN and cond in self.derived_conditions:
                deriving_rules = self.evaluator.get_deriving_rules(cond)
                for dr in deriving_rules:
                    if self.rule_states[dr.id].status not in (RuleStatus.BLOCKED, RuleStatus.FIRED):
                        sub_question = self._find_next_question_for_rule(dr, visited.copy())
                        if sub_question:
                            return sub_question

            elif val == FactStatus.FALSE:
                if not rule.is_or_rule:
                    return None

            elif val == FactStatus.TRUE:
                if rule.is_or_rule:
                    return None

        return None

    def _propagate_inferences(self):
        """発火したルールから仮説を導出"""
        for _ in range(self.MAX_PROPAGATION_ITERATIONS):
            changed = False
            for state in self.rule_states.values():
                if state.status == RuleStatus.FIRED:
                    action = state.rule.action
                    if self.working_memory.get_value(action) != FactStatus.TRUE:
                        self.working_memory.put_hypothesis(action, FactStatus.TRUE)
                        self.reasoning_log.append(f"導出: 「{action}」（ルールが発火）")
                        changed = True
                        self._update_dependent_rules(action, FactStatus.TRUE)

                    # ANDルールが発火した場合、UNKNOWNだった上流条件もTRUEとして導出
                    if not state.rule.is_or_rule:
                        for cond in state.rule.conditions:
                            finding_val = self.working_memory.findings.get(cond)
                            hypo_val = self.working_memory.hypotheses.get(cond)
                            if finding_val == FactStatus.UNKNOWN and hypo_val != FactStatus.TRUE:
                                self.working_memory.put_hypothesis(cond, FactStatus.TRUE)
                                self.reasoning_log.append(f"推論: 「{cond}」→ true（発火ルールの上流条件）")
                                changed = True
                                self._update_dependent_rules(cond, FactStatus.TRUE)

                elif RuleStatus.is_negative(state.status):
                    action = state.rule.action
                    if not state.rule.is_or_rule:
                        can_derive = any(
                            s.rule.action == action and not RuleStatus.is_negative(s.status)
                            for s in self.rule_states.values()
                        )
                        if not can_derive and self.working_memory.get_value(action) != FactStatus.FALSE:
                            self.working_memory.put_hypothesis(action, FactStatus.FALSE)
                            changed = True
                            self._update_dependent_rules(action, FactStatus.FALSE)

            if not changed:
                break

    def _update_dependent_rules(self, condition: str, status: FactStatus):
        """条件のステータス変更に応じて依存ルールを更新"""
        for state in self.rule_states.values():
            if condition in state.rule.conditions:
                state.checked_conditions[condition] = status

    def _is_diagnosis_complete(self) -> bool:
        """診断完了かチェック"""
        return all(
            RuleStatus.is_resolved(self.rule_states[g.id].status)
            for g in get_goal_rules()
        )

    def _generate_result(self) -> Dict[str, Any]:
        """診断結果を生成"""
        applicable_visas = []
        conditional_visas = []
        unknown_conditions = []

        for goal_rule in get_goal_rules():
            state = self.rule_states.get(goal_rule.id)
            if state:
                if state.status == RuleStatus.FIRED:
                    applicable_visas.append({
                        "visa": goal_rule.action,
                        "type": goal_rule.visa_type,
                        "rule_id": goal_rule.id
                    })
                elif state.status != RuleStatus.BLOCKED:
                    unknowns = [
                        cond for cond in goal_rule.conditions
                        if self.working_memory.get_value(cond) == FactStatus.UNKNOWN
                    ]
                    if unknowns:
                        conditional_visas.append({
                            "visa": goal_rule.action,
                            "type": goal_rule.visa_type,
                            "rule_id": goal_rule.id,
                            "unknown_conditions": unknowns
                        })

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

        # 元のルール順序でインデックスを取得
        rule_index_map = {r.id: idx for idx, r in enumerate(self.rules)}

        for state in self.rule_states.values():
            rule = state.rule
            conditions_info = [
                {
                    "text": cond,
                    "status": self.FACT_STATUS_DISPLAY.get(
                        self.evaluator.get_effective_value(cond), "unchecked"
                    ),
                    "is_derived": cond in self.derived_conditions
                }
                for cond in rule.conditions
            ]

            result.append({
                "id": rule.id,
                "index": rule_index_map.get(rule.id, 0),
                "action": rule.action,
                "visa_type": rule.visa_type,
                "conditions": conditions_info,
                "conclusion": rule.action,
                "status": state.status.value,
                "is_and_rule": not rule.is_or_rule,
                "operator": "AND" if not rule.is_or_rule else "OR"
            })

        result.sort(key=lambda r: VISA_TYPE_ORDER.get(r["visa_type"], 99))
        return result

    def go_back(self, steps: int = 1) -> Dict[str, Any]:
        """前の質問に戻る"""
        if len(self.working_memory.answer_history) < steps:
            steps = len(self.working_memory.answer_history)

        if steps > 0:
            target_idx = len(self.working_memory.answer_history) - steps
            if target_idx >= 0:
                target_cond = self.working_memory.answer_history[target_idx][0]
                asked_conditions = [
                    cond for cond, _ in self.working_memory.answer_history[:target_idx + 1]
                ]

                self.working_memory.clear_after(target_cond)

                for state in self.rule_states.values():
                    state.status = RuleStatus.PENDING
                    state.checked_conditions.clear()

                self.evaluator.evaluate_all_rules()
                self._propagate_inferences()
                self.current_question = target_cond

                for cond in asked_conditions:
                    self.evaluator.mark_related_rules_evaluating(cond)

        return {
            "current_question": self.current_question,
            "answered_questions": [
                {"condition": c, "answer": s.value}
                for c, s in self.working_memory.answer_history
            ],
            "rules_status": self._get_rules_display_info()
        }

    def restart(self) -> Optional[str]:
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
        return list({r.visa_type for r in self.rules if condition in r.conditions})
