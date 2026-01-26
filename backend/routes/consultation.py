"""
診断関連のAPIエンドポイント
"""
from typing import Dict
from fastapi import APIRouter, HTTPException

from engine import InferenceEngine
from knowledge import reload_rules
from schemas import StartRequest, AnswerRequest, GoBackRequest
from services.validation import check_rules_integrity

router = APIRouter(prefix="/api/consultation", tags=["consultation"])

# セッション管理（実運用ではRedisなどを使用）
sessions: Dict[str, InferenceEngine] = {}


@router.post("/start")
async def start_consultation(request: StartRequest):
    """診断を開始"""
    from core import FactStatus

    reload_rules()

    # 整合性チェック - エラーがあれば診断を開始できない
    issues = check_rules_integrity()
    if issues:
        issue_messages = [i["message"] for i in issues]
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ルールに問題があるため診断を開始できません",
                "issues": issue_messages
            }
        )

    engine = InferenceEngine()

    # 問診票からのinitial_factsを適用
    if request.initial_facts:
        for fact in request.initial_facts:
            status = FactStatus.TRUE if fact.value else FactStatus.FALSE
            engine.working_memory.put_finding(fact.fact_name, status)

    first_question = engine.start_consultation()

    sessions[request.session_id] = engine

    return {
        "session_id": request.session_id,
        "current_question": first_question,
        "rules_status": engine.get_rules_display_info(),
        "is_complete": first_question is None,
        "applied_initial_facts": [f.fact_name for f in request.initial_facts] if request.initial_facts else []
    }


@router.post("/answer")
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
        "rules_status": result["rules_status"],
        "derived_facts": result["derived_facts"],
        "is_complete": result["is_complete"]
    }

    if result["is_complete"]:
        response["diagnosis_result"] = result.get("diagnosis_result")

    return response


@router.post("/back")
async def go_back(request: GoBackRequest):
    """前の質問に戻る"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    engine = sessions[request.session_id]
    result = engine.go_back(request.steps)

    return {
        "session_id": request.session_id,
        "current_question": result["current_question"],
        "answered_questions": result["answered_questions"],
        "rules_status": result["rules_status"]
    }


@router.post("/restart")
async def restart_consultation(request: StartRequest):
    """最初からやり直し"""
    engine = InferenceEngine()
    first_question = engine.start_consultation()

    sessions[request.session_id] = engine

    return {
        "session_id": request.session_id,
        "current_question": first_question,
        "rules_status": engine.get_rules_display_info(),
        "is_complete": first_question is None
    }


@router.get("/state/{session_id}")
async def get_state(session_id: str):
    """現在の状態を取得"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    engine = sessions[session_id]
    state = engine.get_current_state()

    return {
        "session_id": session_id,
        **state
    }
