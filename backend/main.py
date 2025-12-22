"""
ビザ選定エキスパートシステム - FastAPI メインアプリケーション
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json

from inference_engine import InferenceEngine
from knowledge_base import get_all_rules, get_goal_rules, VISA_RULES, save_rules, reload_rules, RuleType, VISA_TYPE_ORDER

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
    rules = get_all_rules()

    if visa_type:
        rules = [r for r in rules if r.visa_type == visa_type]

    # ソート（sort=noneの場合はJSON保存順のまま）
    if sort == "visa_type":
        rules = sorted(rules, key=lambda r: VISA_TYPE_ORDER.get(r.visa_type, 99))

    return {
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "conditions": r.conditions,
                "action": r.action,
                "is_or_rule": r.is_or_rule,
                "visa_type": r.visa_type,
                "rule_type": r.rule_type.value
            }
            for r in rules
        ]
    }


@app.get("/api/rules/{rule_id}")
async def get_rule(rule_id: str):
    """特定のルールを取得"""
    for rule in VISA_RULES:
        if rule.id == rule_id:
            return {
                "id": rule.id,
                "name": rule.name,
                "conditions": rule.conditions,
                "action": rule.action,
                "is_or_rule": rule.is_or_rule,
                "visa_type": rule.visa_type,
                "rule_type": rule.rule_type.value
            }

    raise HTTPException(status_code=404, detail="Rule not found")


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
    rules = get_all_rules()
    if visa_type:
        rules = [r for r in rules if r.visa_type == visa_type]

    issues = []
    all_actions = {r.action for r in VISA_RULES}
    all_conditions = set()
    for r in VISA_RULES:
        all_conditions.update(r.conditions)

    # 到達不能なルールをチェック
    for rule in rules:
        for cond in rule.conditions:
            if cond in all_actions:
                # この条件は他のルールの結論
                producing_rules = [r for r in VISA_RULES if r.action == cond]
                if not producing_rules:
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

        rule = next((r for r in VISA_RULES if r.id == rule_id), None)
        if rule:
            for cond in rule.conditions:
                if cond in all_actions:
                    dep_rules = [r for r in VISA_RULES if r.action == cond]
                    for dep_rule in dep_rules:
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
    from knowledge_base import _load_goal_actions_from_json
    goal_actions = _load_goal_actions_from_json()

    for rule in rules:
        action = rule.action
        # ゴールアクションならスキップ
        if action in goal_actions:
            continue
        # 他のルールの条件として使われているかチェック
        is_used = any(action in r.conditions for r in VISA_RULES if r.id != rule.id)
        if not is_used:
            issues.append({
                "type": "orphan",
                "rule_id": rule.id,
                "message": f"ルール「{rule.name}」のTHEN「{action}」はどこからも参照されていません"
            })

    if not issues:
        return {"status": "ok", "message": "問題ありません"}

    return {"status": "issues_found", "issues": issues}




# ========== ルール管理 CRUD ==========

@app.post("/api/rules")
async def create_rule(rule: RuleRequest):
    """新しいルールを作成"""
    # 既存ルールと重複チェック
    for r in VISA_RULES:
        if r.id == rule.id:
            raise HTTPException(status_code=400, detail=f"Rule with ID {rule.id} already exists")

    # 現在のルールをJSONとして取得
    rules_data = {
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "conditions": r.conditions,
                "action": r.action,
                "is_or_rule": r.is_or_rule,
                "visa_type": r.visa_type,
                "rule_type": r.rule_type.value
            }
            for r in VISA_RULES
        ],
        "goal_actions": [
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
    }

    # 新しいルールを追加
    rules_data["rules"].append({
        "id": rule.id,
        "name": rule.name,
        "conditions": rule.conditions,
        "action": rule.action,
        "is_or_rule": rule.is_or_rule,
        "visa_type": rule.visa_type,
        "rule_type": rule.rule_type
    })

    if save_rules(rules_data):
        return {"status": "created", "rule_id": rule.id}
    else:
        raise HTTPException(status_code=500, detail="Failed to save rule")


@app.put("/api/rules/{rule_id}")
async def update_rule(rule_id: str, rule: RuleRequest):
    """既存ルールを更新"""
    found = False
    for r in VISA_RULES:
        if r.id == rule_id:
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Rule not found")

    # 現在のルールをJSONとして取得（更新対象を除外）
    rules_data = {
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "conditions": r.conditions,
                "action": r.action,
                "is_or_rule": r.is_or_rule,
                "visa_type": r.visa_type,
                "rule_type": r.rule_type.value
            }
            for r in VISA_RULES if r.id != rule_id
        ],
        "goal_actions": [
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
    }

    # 更新されたルールを追加
    rules_data["rules"].append({
        "id": rule.id,
        "name": rule.name,
        "conditions": rule.conditions,
        "action": rule.action,
        "is_or_rule": rule.is_or_rule,
        "visa_type": rule.visa_type,
        "rule_type": rule.rule_type
    })

    if save_rules(rules_data):
        return {"status": "updated", "rule_id": rule.id}
    else:
        raise HTTPException(status_code=500, detail="Failed to save rule")


@app.delete("/api/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """ルールを削除"""
    found = False
    for r in VISA_RULES:
        if r.id == rule_id:
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Rule not found")

    # 現在のルールをJSONとして取得（削除対象を除外）
    rules_data = {
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "conditions": r.conditions,
                "action": r.action,
                "is_or_rule": r.is_or_rule,
                "visa_type": r.visa_type,
                "rule_type": r.rule_type.value
            }
            for r in VISA_RULES if r.id != rule_id
        ],
        "goal_actions": [
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
    }

    if save_rules(rules_data):
        return {"status": "deleted", "rule_id": rule_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete rule")


class ReorderRequest(BaseModel):
    rule_ids: List[str]


@app.post("/api/rules/reorder")
async def reorder_rules(request: ReorderRequest):
    """ルールの順序を変更"""
    # 現在のルールをIDでマップ化
    rules_map = {r.id: r for r in VISA_RULES}

    # 指定された順序で並び替え
    reordered = []
    for rule_id in request.rule_ids:
        if rule_id in rules_map:
            reordered.append(rules_map[rule_id])
            del rules_map[rule_id]

    # 指定されなかったルールは末尾に追加
    reordered.extend(rules_map.values())

    # JSONに保存
    rules_data = {
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "conditions": r.conditions,
                "action": r.action,
                "is_or_rule": r.is_or_rule,
                "visa_type": r.visa_type,
                "rule_type": r.rule_type.value
            }
            for r in reordered
        ],
        "goal_actions": [
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
    }

    if save_rules(rules_data):
        return {"status": "reordered", "count": len(reordered)}
    else:
        raise HTTPException(status_code=500, detail="Failed to save rule order")


@app.post("/api/rules/auto-organize")
async def auto_organize_rules():
    """ルールを依存関係に基づいて自動整理

    整理ロジック:
    1. ビザタイプ順（E→L→H-1B→B→J-1）
    2. 各ビザタイプ内で依存深度順（ゴールルール→中間ルール→初期ルール）
    """
    from knowledge_base import _load_goal_actions_from_json

    goal_actions = _load_goal_actions_from_json()

    # 全ルールのactionをマップ
    action_to_rule = {r.action: r for r in VISA_RULES}

    # 依存深度を計算（ゴール=0、ゴールの条件=1、...）
    depth_cache = {}

    def get_depth(rule) -> int:
        if rule.id in depth_cache:
            return depth_cache[rule.id]

        # ゴールルールは深度0
        if rule.action in goal_actions:
            depth_cache[rule.id] = 0
            return 0

        # このルールのactionを条件として持つルールを探す
        max_parent_depth = -1
        for other in VISA_RULES:
            if rule.action in other.conditions:
                parent_depth = get_depth(other)
                max_parent_depth = max(max_parent_depth, parent_depth)

        # 親がいない場合は最大深度（初期ルール）
        if max_parent_depth == -1:
            depth_cache[rule.id] = 999
        else:
            depth_cache[rule.id] = max_parent_depth + 1

        return depth_cache[rule.id]

    # 各ルールの深度を計算
    for rule in VISA_RULES:
        get_depth(rule)

    # ビザタイプ順→深度順でソート
    sorted_rules = sorted(
        VISA_RULES,
        key=lambda r: (VISA_TYPE_ORDER.get(r.visa_type, 99), depth_cache.get(r.id, 999))
    )

    # JSONに保存
    rules_data = {
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "conditions": r.conditions,
                "action": r.action,
                "is_or_rule": r.is_or_rule,
                "visa_type": r.visa_type,
                "rule_type": r.rule_type.value
            }
            for r in sorted_rules
        ],
        "goal_actions": list(goal_actions)
    }

    if save_rules(rules_data):
        return {"status": "organized", "count": len(sorted_rules)}
    else:
        raise HTTPException(status_code=500, detail="Failed to save organized rules")


@app.post("/api/rules/reload")
async def reload_all_rules():
    """ルールをJSONファイルから再読み込み"""
    reload_rules()
    return {"status": "reloaded", "count": len(VISA_RULES)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
