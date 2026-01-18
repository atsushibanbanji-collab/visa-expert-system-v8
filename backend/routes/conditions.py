"""
条件（質問）管理関連のAPIエンドポイント
"""
import csv
import io
import json
import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from knowledge import get_all_rules

router = APIRouter(prefix="/api/conditions", tags=["conditions"])

# データファイルのパス
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
NOTES_FILE = os.path.join(DATA_DIR, "condition_notes.json")


def load_notes() -> dict:
    """補足データを読み込む"""
    if not os.path.exists(NOTES_FILE):
        return {}
    with open(NOTES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_notes(notes: dict):
    """補足データを保存"""
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


def get_all_conditions() -> set:
    """全ルールから全条件を抽出"""
    conditions = set()
    for rule in get_all_rules():
        for cond in rule.conditions:
            conditions.add(cond)
    return conditions


@router.get("")
async def list_conditions():
    """全条件一覧を取得（補足付き）"""
    conditions = sorted(get_all_conditions())
    notes = load_notes()

    return {
        "conditions": [
            {
                "text": cond,
                "note": notes.get(cond, "")
            }
            for cond in conditions
        ]
    }


class UpdateNoteRequest(BaseModel):
    condition: str
    note: str


@router.put("/note")
async def update_note(request: UpdateNoteRequest):
    """条件の補足を更新"""
    notes = load_notes()

    if request.note.strip():
        notes[request.condition] = request.note.strip()
    else:
        # 空の場合は削除
        notes.pop(request.condition, None)

    save_notes(notes)
    return {"status": "updated", "condition": request.condition}


@router.get("/export")
async def export_conditions_csv():
    """条件と補足をCSV形式でエクスポート"""
    conditions = sorted(get_all_conditions())
    notes = load_notes()

    output = io.StringIO()
    output.write('\ufeff')  # BOM for Excel

    writer = csv.writer(output)
    writer.writerow(["condition", "note"])

    for cond in conditions:
        writer.writerow([cond, notes.get(cond, "")])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=condition_notes.csv"}
    )


@router.post("/import")
async def import_conditions_csv(file: UploadFile = File(...)):
    """CSVファイルから補足をインポート"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルを選択してください")

    content = await file.read()

    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = content.decode('cp932')

    reader = csv.DictReader(io.StringIO(text))

    updates = {}  # 更新する補足
    deletes = []  # 削除する条件
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            condition = row.get("condition", "").strip()
            note = row.get("note", "").strip()

            if not condition:
                continue

            if note:
                updates[condition] = note
            else:
                deletes.append(condition)

        except Exception as e:
            errors.append(f"行{row_num}: {str(e)}")

    if errors:
        return {"status": "error", "errors": errors}

    # 既存のノートを更新
    existing_notes = load_notes()
    existing_notes.update(updates)

    # 空になった条件を削除
    for condition in deletes:
        existing_notes.pop(condition, None)

    save_notes(existing_notes)

    return {"status": "imported", "count": len(updates)}


@router.get("/note/{condition:path}")
async def get_note(condition: str):
    """特定の条件の補足を取得"""
    notes = load_notes()
    return {"condition": condition, "note": notes.get(condition, "")}
