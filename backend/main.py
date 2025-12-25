"""
ビザ選定エキスパートシステム - FastAPI メインアプリケーション
"""
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from inference_engine import InferenceEngine
from knowledge_base import (
    get_all_rules, get_goal_rules, VISA_RULES, save_rules, reload_rules,
    RuleType, VISA_TYPE_ORDER, _load_goal_actions_from_json
)


# ========== ヘルパー関数 ==========

def _rule_to_dict(rule) -> dict:
    """ルールオブジェクトをdict形式に変換"""
    return {
        "id": rule.id,
        "name": rule.name,
        "conditions": rule.conditions,
        "action": rule.action,
        "is_or_rule": rule.is_or_rule,
        "visa_type": rule.visa_type,
        "rule_type": rule.rule_type.value
    }


def _rules_to_dict_list(rules: list) -> list:
    """ルールリストをdictリストに変換"""
    return [_rule_to_dict(r) for r in rules]


def _build_rules_data(rules: list, goal_actions: set = None) -> dict:
    """ルールリストをJSON保存用のdict形式に変換"""
    if goal_actions is None:
        goal_actions = _load_goal_actions_from_json()
    return {
        "rules": _rules_to_dict_list(rules),
        "goal_actions": list(goal_actions)
    }


def _find_rule(rule_id: str):
    """ルールIDでルールを検索"""
    return next((r for r in VISA_RULES if r.id == rule_id), None)


def _save_rules_excluding(exclude_id: str = None) -> list:
    """指定IDを除外したルールリストを返す"""
    if exclude_id:
        return [r for r in VISA_RULES if r.id != exclude_id]
    return list(VISA_RULES)


def _sort_rules_by_id(rules: list) -> list:
    """ID番号順でソート（ビザタイプ順 → ID番号順）"""
    def extract_id_number(rule_id: str) -> int:
        match = re.search(r'\d+', rule_id)
        return int(match.group()) if match else 999
    return sorted(rules, key=lambda r: (VISA_TYPE_ORDER.get(r.visa_type, 99), extract_id_number(r.id)))


def _sort_rules_by_dependency(rules: list, goal_actions: set) -> list:
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

app = FastAPI(
    title="ビザ選定エキスパートシステム",
    description="オブジェクト指向設計によるビザ選定支援システム",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# セッション管理（実運用ではRedisなどを使用）
sessions: Dict[str, InferenceEngine] = {}


class StartRequest(BaseModel):
    session_id: str


class AnswerRequest(BaseModel):
    session_id: str
    answer: str  # "yes", "no", "unknown"


class GoBackRequest(BaseModel):
    session_id: str
    steps: int = 1


class RuleRequest(BaseModel):
    id: str
    name: str
    conditions: List[str]
    action: str
    is_or_rule: bool = False
    visa_type: str = ""
    rule_type: str = "i"  # "i" for INITIAL, "m" for MIDDLE


@app.get("/")
async def root():
    return {"message": "ビザ選定エキスパートシステム API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/consultation/start")
async def start_consultation(request: StartRequest):
    """診断を開始"""
    engine = InferenceEngine()
    first_question = engine.start_consultation()

    sessions[request.session_id] = engine

    return {
        "session_id": request.session_id,
        "current_question": first_question,
        "related_visa_types": engine.get_related_visa_types(first_question) if first_question else [],
        "rules_status": engine._get_rules_display_info(),
        "is_complete": first_question is None
    }


@app.post("/api/consultation/answer")
async def answer_question(request: AnswerRequest):
    """質問に回答"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    engine = sessions[request.session_id]

    if not engine.current_question:
        raise HTTPException(status_code=400, detail="No current question")

    result = engine.answer_question(engine.current_question, request.answer)

    response = {
        "session_id": request.session_id,
        "current_question": result["next_question"],
        "related_visa_types": engine.get_related_visa_types(result["next_question"]) if result["next_question"] else [],
        "rules_status": result["rules_status"],
        "derived_facts": result["derived_facts"],
        "is_complete": result["is_complete"]
    }

    if result["is_complete"]:
        response["diagnosis_result"] = result.get("diagnosis_result")

    return response


@app.post("/api/consultation/back")
async def go_back(request: GoBackRequest):
    """前の質問に戻る"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    engine = sessions[request.session_id]
    result = engine.go_back(request.steps)

    return {
        "session_id": request.session_id,
        "current_question": result["current_question"],
        "related_visa_types": engine.get_related_visa_types(result["current_question"]) if result["current_question"] else [],
        "answered_questions": result["answered_questions"],
        "rules_status": result["rules_status"]
    }


@app.post("/api/consultation/restart")
async def restart_consultation(request: StartRequest):
    """最初からやり直し"""
    engine = InferenceEngine()
    first_question = engine.start_consultation()

    sessions[request.session_id] = engine

    return {
        "session_id": request.session_id,
        "current_question": first_question,
        "related_visa_types": engine.get_related_visa_types(first_question) if first_question else [],
        "rules_status": engine._get_rules_display_info(),
        "is_complete": first_question is None
    }


@app.get("/api/consultation/state/{session_id}")
async def get_state(session_id: str):
    """現在の状態を取得"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    engine = sessions[session_id]
    state = engine.get_current_state()

    return {
        "session_id": session_id,
        **state,
        "related_visa_types": engine.get_related_visa_types(state["current_question"]) if state["current_question"] else []
    }


# ========== 管理機能 ==========

@app.get("/api/rules")
async def get_rules(visa_type: Optional[str] = None, sort: Optional[str] = "visa_type"):
    """ルール一覧を取得

    sort: "visa_type" (E→L→H-1B→B→J-1順), "none" (JSON保存順)
    """
    reload_rules()
    rules = get_all_rules()

    if visa_type:
        rules = [r for r in rules if r.visa_type == visa_type]
    if sort == "visa_type":
        rules = sorted(rules, key=lambda r: VISA_TYPE_ORDER.get(r.visa_type, 99))

    return {"rules": _rules_to_dict_list(rules)}


@app.get("/api/rules/{rule_id}")
async def get_rule(rule_id: str):
    """特定のルールを取得"""
    reload_rules()
    rule = _find_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return _rule_to_dict(rule)


@app.get("/api/visa-types")
async def get_visa_types():
    """利用可能なビザタイプを取得"""
    return {
        "visa_types": [
            {"code": "E", "name": "Eビザ（投資家・貿易）", "description": "投資家や貿易業者向けのビザ"},
            {"code": "L", "name": "Lビザ（企業内転勤）", "description": "グループ企業間の転勤者向けビザ"},
            {"code": "B", "name": "Bビザ（商用）", "description": "短期商用目的のビザ"},
            {"code": "H-1B", "name": "H-1Bビザ（専門職）", "description": "専門的職業従事者向けビザ"},
            {"code": "J-1", "name": "J-1ビザ（研修）", "description": "研修・交流目的のビザ"},
        ]
    }


@app.get("/api/validation/check")
async def validate_rules(visa_type: Optional[str] = None):
    """ルールの整合性チェック"""
    reload_rules()
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
                    "rule_id": rule.id,
                    "message": f"条件「{cond}」を導出するルールがありません"
                })

    # 循環参照をチェック
    def check_cycle(rule_id: str, visited: set, path: list):
        if rule_id in visited:
            return path + [rule_id]
        visited.add(rule_id)
        path.append(rule_id)
        rule = _find_rule(rule_id)
        if rule:
            for cond in rule.conditions:
                if cond in all_actions:
                    for dep_rule in (r for r in VISA_RULES if r.action == cond):
                        cycle = check_cycle(dep_rule.id, visited.copy(), path.copy())
                        if cycle:
                            return cycle
        return None

    for rule in rules:
        cycle = check_cycle(rule.id, set(), [])
        if cycle and len(cycle) > 1:
            issues.append({
                "type": "cycle",
                "rule_ids": cycle,
                "message": f"ルールに循環参照があります: {' -> '.join(cycle)}"
            })

    # 孤立ルールをチェック（THENが他で使われていない + ゴールでもない）
    for rule in rules:
        if rule.action not in goal_actions:
            if not any(rule.action in r.conditions for r in VISA_RULES if r.id != rule.id):
                issues.append({
                    "type": "orphan",
                    "rule_id": rule.id,
                    "message": f"ルール「{rule.name}」のTHEN「{rule.action}」はどこからも参照されていません"
                })

    return {"status": "ok", "message": "問題ありません"} if not issues else {"status": "issues_found", "issues": issues}




# ========== ルール管理 CRUD ==========

def _request_to_dict(rule: 'RuleRequest') -> dict:
    """RuleRequestをdict形式に変換"""
    return {
        "id": rule.id,
        "name": rule.name,
        "conditions": rule.conditions,
        "action": rule.action,
        "is_or_rule": rule.is_or_rule,
        "visa_type": rule.visa_type,
        "rule_type": rule.rule_type
    }


@app.post("/api/rules")
async def create_rule(rule: RuleRequest):
    """新しいルールを作成"""
    reload_rules()
    if _find_rule(rule.id):
        raise HTTPException(status_code=400, detail=f"Rule with ID {rule.id} already exists")

    rules_data = _build_rules_data(VISA_RULES)
    rules_data["rules"].append(_request_to_dict(rule))

    if not save_rules(rules_data):
        raise HTTPException(status_code=500, detail="Failed to save rule")
    return {"status": "created", "rule_id": rule.id}


@app.put("/api/rules/{rule_id}")
async def update_rule(rule_id: str, rule: RuleRequest):
    """既存ルールを更新"""
    reload_rules()
    if not _find_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")

    rules_data = _build_rules_data(_save_rules_excluding(rule_id))
    rules_data["rules"].append(_request_to_dict(rule))

    if not save_rules(rules_data):
        raise HTTPException(status_code=500, detail="Failed to save rule")
    return {"status": "updated", "rule_id": rule.id}


@app.delete("/api/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """ルールを削除"""
    reload_rules()
    if not _find_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")

    if not save_rules(_build_rules_data(_save_rules_excluding(rule_id))):
        raise HTTPException(status_code=500, detail="Failed to delete rule")
    return {"status": "deleted", "rule_id": rule_id}


class ReorderRequest(BaseModel):
    rule_ids: List[str]


@app.post("/api/rules/reorder")
async def reorder_rules(request: ReorderRequest):
    """ルールの順序を変更"""
    reload_rules()
    rules_map = {r.id: r for r in VISA_RULES}

    reordered = []
    for rule_id in request.rule_ids:
        if rule_id in rules_map:
            reordered.append(rules_map.pop(rule_id))
    reordered.extend(rules_map.values())

    if not save_rules(_build_rules_data(reordered)):
        raise HTTPException(status_code=500, detail="Failed to save rule order")
    return {"status": "reordered", "count": len(reordered)}


class AutoOrganizeRequest(BaseModel):
    mode: str = "dependency"  # "dependency" or "id"


@app.post("/api/rules/auto-organize")
async def auto_organize_rules(request: AutoOrganizeRequest = AutoOrganizeRequest()):
    """ルールを自動整理

    mode:
    - "dependency": 依存関係に基づいて整理（ビザタイプ順→深度順）
    - "id": IDのナンバリング順に整理（ビザタイプ順→ID番号順）
    """
    reload_rules()
    goal_actions = _load_goal_actions_from_json()

    if request.mode == "id":
        sorted_rules = _sort_rules_by_id(VISA_RULES)
    else:
        sorted_rules = _sort_rules_by_dependency(VISA_RULES, goal_actions)

    if not save_rules(_build_rules_data(sorted_rules, goal_actions)):
        raise HTTPException(status_code=500, detail="Failed to save organized rules")
    return {"status": "organized", "count": len(sorted_rules)}


@app.post("/api/rules/reload")
async def reload_all_rules():
    """ルールをJSONファイルから再読み込み"""
    reload_rules()
    return {"status": "reloaded", "count": len(VISA_RULES)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
