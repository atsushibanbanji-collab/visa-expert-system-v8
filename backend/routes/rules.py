"""
ルール管理関連のAPIエンドポイント
"""
from typing import Optional
from fastapi import APIRouter, HTTPException

from knowledge_base import (
    get_all_rules, VISA_RULES, save_rules, reload_rules,
    VISA_TYPE_ORDER, _load_goal_actions_from_json
)
from schemas import RuleRequest, DeleteRequest, ReorderRequest, AutoOrganizeRequest
from services.validation import check_rules_integrity
from services.rule_helpers import (
    rules_to_dict_list, build_rules_data, find_rule_by_action,
    rules_excluding_action, sort_rules_by_action, sort_rules_by_dependency,
    request_to_dict
)

router = APIRouter(prefix="/api", tags=["rules"])


@router.get("/rules")
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

    return {"rules": rules_to_dict_list(rules)}


@router.get("/visa-types")
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


@router.get("/validation/check")
async def validate_rules(visa_type: Optional[str] = None):
    """ルールの整合性チェック"""
    reload_rules()
    issues = check_rules_integrity(visa_type)
    return {"status": "ok", "message": "問題ありません"} if not issues else {"status": "issues_found", "issues": issues}


@router.post("/rules")
async def create_rule(rule: RuleRequest):
    """新しいルールを作成（actionが識別子）"""
    reload_rules()
    if find_rule_by_action(rule.action):
        raise HTTPException(status_code=400, detail=f"同じTHEN「{rule.action}」を持つルールが既に存在します")

    rules_data = build_rules_data(VISA_RULES)
    rules_data["rules"].append(request_to_dict(rule))

    if not save_rules(rules_data):
        raise HTTPException(status_code=500, detail="Failed to save rule")
    return {"status": "created", "action": rule.action}


@router.put("/rules")
async def update_rule(rule: RuleRequest):
    """既存ルールを更新（original_actionで対象を特定）"""
    reload_rules()
    target_action = rule.original_action or rule.action

    if not find_rule_by_action(target_action):
        raise HTTPException(status_code=404, detail="Rule not found")

    # actionを変更する場合、新しいactionが既に存在しないか確認
    if rule.original_action and rule.action != rule.original_action:
        if find_rule_by_action(rule.action):
            raise HTTPException(status_code=400, detail=f"同じTHEN「{rule.action}」を持つルールが既に存在します")

    rules_data = build_rules_data(rules_excluding_action(target_action))
    rules_data["rules"].append(request_to_dict(rule))

    if not save_rules(rules_data):
        raise HTTPException(status_code=500, detail="Failed to save rule")
    return {"status": "updated", "action": rule.action}


@router.post("/rules/delete")
async def delete_rule(request: DeleteRequest):
    """ルールを削除（actionで特定）"""
    reload_rules()
    if not find_rule_by_action(request.action):
        raise HTTPException(status_code=404, detail="Rule not found")

    if not save_rules(build_rules_data(rules_excluding_action(request.action))):
        raise HTTPException(status_code=500, detail="Failed to delete rule")
    return {"status": "deleted", "action": request.action}


@router.post("/rules/reorder")
async def reorder_rules(request: ReorderRequest):
    """ルールの順序を変更"""
    reload_rules()
    rules_map = {r.action: r for r in VISA_RULES}

    reordered = []
    for action in request.actions:
        if action in rules_map:
            reordered.append(rules_map.pop(action))
    reordered.extend(rules_map.values())

    if not save_rules(build_rules_data(reordered)):
        raise HTTPException(status_code=500, detail="Failed to save rule order")
    return {"status": "reordered", "count": len(reordered)}


@router.post("/rules/auto-organize")
async def auto_organize_rules(request: AutoOrganizeRequest = AutoOrganizeRequest()):
    """ルールを自動整理

    mode:
    - "dependency": 依存関係に基づいて整理（ビザタイプ順→深度順）
    - "action": action名順に整理（ビザタイプ順→action名順）
    """
    reload_rules()
    goal_actions = _load_goal_actions_from_json()

    if request.mode == "action":
        sorted_rules = sort_rules_by_action(VISA_RULES)
    else:
        sorted_rules = sort_rules_by_dependency(VISA_RULES, goal_actions)

    if not save_rules(build_rules_data(sorted_rules, goal_actions)):
        raise HTTPException(status_code=500, detail="Failed to save organized rules")
    return {"status": "organized", "count": len(sorted_rules)}


@router.post("/rules/reload")
async def reload_all_rules():
    """ルールをJSONファイルから再読み込み"""
    reload_rules()
    return {"status": "reloaded", "count": len(VISA_RULES)}
