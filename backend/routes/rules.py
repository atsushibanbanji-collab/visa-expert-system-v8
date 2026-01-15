"""
ルール管理関連のAPIエンドポイント
"""
from fastapi import APIRouter, HTTPException

from knowledge import (
    get_all_rules, RULES, save_rules, reload_rules
)
from schemas import RuleRequest, DeleteRequest, ReorderRequest
from services.validation import check_rules_integrity
from services.rule_helpers import (
    rules_to_dict_list, build_rules_data, request_to_dict
)

router = APIRouter(prefix="/api", tags=["rules"])


@router.get("/rules")
async def get_rules():
    """ルール一覧を取得（rules.json順）"""
    reload_rules()
    rules = get_all_rules()
    return {"rules": rules_to_dict_list(rules)}


@router.get("/validation/check")
async def validate_rules():
    """ルールの整合性チェック"""
    reload_rules()
    issues = check_rules_integrity()
    return {"status": "ok", "message": "問題ありません"} if not issues else {"status": "issues_found", "issues": issues}


@router.post("/rules")
async def create_rule(rule: RuleRequest):
    """新しいルールを作成

    insert_after: 挿入位置（0=先頭、N=N番目の後、None=末尾）
    """
    reload_rules()
    rules_data = build_rules_data(RULES)
    new_rule = request_to_dict(rule)

    # 挿入位置を決定
    if rule.insert_after is not None:
        insert_index = rule.insert_after
        if insert_index < 0:
            insert_index = 0
        elif insert_index > len(rules_data["rules"]):
            insert_index = len(rules_data["rules"])
        rules_data["rules"].insert(insert_index, new_rule)
    else:
        insert_index = len(rules_data["rules"])
        rules_data["rules"].append(new_rule)

    if not save_rules(rules_data):
        raise HTTPException(status_code=500, detail="Failed to save rule")

    return {"status": "created", "action": rule.action, "position": insert_index}


@router.put("/rules")
async def update_rule(rule: RuleRequest):
    """既存ルールを更新（indexで対象を特定）"""
    reload_rules()

    if rule.index is None:
        raise HTTPException(status_code=400, detail="index is required for update")

    if rule.index < 0 or rule.index >= len(RULES):
        raise HTTPException(status_code=404, detail="Rule not found at specified index")

    # インデックス位置のルールだけを更新
    rules_data = build_rules_data(RULES)
    rules_data["rules"][rule.index] = request_to_dict(rule)

    if not save_rules(rules_data):
        raise HTTPException(status_code=500, detail="Failed to save rule")
    return {"status": "updated", "action": rule.action, "index": rule.index}


@router.post("/rules/delete")
async def delete_rule(request: DeleteRequest):
    """ルールを削除（indexで特定）"""
    reload_rules()

    if request.index < 0 or request.index >= len(RULES):
        raise HTTPException(status_code=404, detail="Rule not found at specified index")

    # インデックス位置のルールだけを削除
    rules_data = build_rules_data(RULES)
    deleted_action = rules_data["rules"][request.index]["action"]
    del rules_data["rules"][request.index]

    if not save_rules(rules_data):
        raise HTTPException(status_code=500, detail="Failed to delete rule")
    return {"status": "deleted", "index": request.index, "action": deleted_action}


@router.post("/rules/reorder")
async def reorder_rules(request: ReorderRequest):
    """ルールの順序を変更"""
    reload_rules()
    rules_map = {r.action: r for r in RULES}

    reordered = []
    for action in request.actions:
        if action in rules_map:
            reordered.append(rules_map.pop(action))
    reordered.extend(rules_map.values())

    if not save_rules(build_rules_data(reordered)):
        raise HTTPException(status_code=500, detail="Failed to save rule order")
    return {"status": "reordered", "count": len(reordered)}


@router.post("/rules/reload")
async def reload_all_rules():
    """ルールをJSONファイルから再読み込み"""
    reload_rules()
    return {"status": "reloaded", "count": len(RULES)}
