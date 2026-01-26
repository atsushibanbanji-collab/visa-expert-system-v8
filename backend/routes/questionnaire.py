"""
問診票（プレスクリーニング）管理関連のAPIエンドポイント
"""
import csv
import io
import json
import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/questionnaire", tags=["questionnaire"])

# データファイルのパス
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
QUESTIONNAIRE_FILE = os.path.join(DATA_DIR, "questionnaire.json")


# Pydanticモデル
class InitialFact(BaseModel):
    fact_name: str
    value: bool


class Answer(BaseModel):
    value: str
    label: str
    next_question: Optional[str] = None
    initial_facts: List[InitialFact] = []


class Question(BaseModel):
    id: str
    text: str
    answers: List[Answer]


class Questionnaire(BaseModel):
    questions: List[Question]
    start_question: str


class QuestionCreate(BaseModel):
    id: str
    text: str
    answers: List[Answer]


class QuestionUpdate(BaseModel):
    id: Optional[str] = None
    text: Optional[str] = None
    answers: Optional[List[Answer]] = None


def load_questionnaire() -> dict:
    """問診票データを読み込む"""
    if not os.path.exists(QUESTIONNAIRE_FILE):
        return {"questions": [], "start_question": ""}
    with open(QUESTIONNAIRE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_questionnaire(data: dict):
    """問診票データを保存"""
    with open(QUESTIONNAIRE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("")
async def get_questionnaire():
    """問診票データを取得"""
    return load_questionnaire()


@router.put("")
async def update_questionnaire(questionnaire: Questionnaire):
    """問診票データを全体更新"""
    save_questionnaire(questionnaire.model_dump())
    return {"message": "問診票を更新しました"}


@router.post("/question")
async def add_question(question: QuestionCreate):
    """質問を追加"""
    data = load_questionnaire()

    # 既存IDチェック
    existing_ids = [q["id"] for q in data["questions"]]
    if question.id in existing_ids:
        raise HTTPException(status_code=400, detail=f"質問ID '{question.id}' は既に存在します")

    data["questions"].append(question.model_dump())
    save_questionnaire(data)
    return {"message": f"質問 '{question.id}' を追加しました"}


@router.put("/question/{question_id}")
async def update_question(question_id: str, question: QuestionUpdate):
    """質問を更新"""
    data = load_questionnaire()

    for i, q in enumerate(data["questions"]):
        if q["id"] == question_id:
            if question.id is not None:
                q["id"] = question.id
            if question.text is not None:
                q["text"] = question.text
            if question.answers is not None:
                q["answers"] = [a.model_dump() for a in question.answers]
            data["questions"][i] = q
            save_questionnaire(data)
            return {"message": f"質問 '{question_id}' を更新しました"}

    raise HTTPException(status_code=404, detail=f"質問 '{question_id}' が見つかりません")


@router.delete("/question/{question_id}")
async def delete_question(question_id: str):
    """質問を削除"""
    data = load_questionnaire()

    original_length = len(data["questions"])
    data["questions"] = [q for q in data["questions"] if q["id"] != question_id]

    if len(data["questions"]) == original_length:
        raise HTTPException(status_code=404, detail=f"質問 '{question_id}' が見つかりません")

    # 開始質問が削除された場合
    if data.get("start_question") == question_id:
        data["start_question"] = data["questions"][0]["id"] if data["questions"] else ""

    # 他の質問の遷移先を解除
    for q in data["questions"]:
        for answer in q["answers"]:
            if answer.get("next_question") == question_id:
                answer["next_question"] = None

    save_questionnaire(data)
    return {"message": f"質問 '{question_id}' を削除しました"}


@router.put("/start/{question_id}")
async def set_start_question(question_id: str):
    """開始質問を設定"""
    data = load_questionnaire()

    existing_ids = [q["id"] for q in data["questions"]]
    if question_id not in existing_ids:
        raise HTTPException(status_code=404, detail=f"質問 '{question_id}' が見つかりません")

    data["start_question"] = question_id
    save_questionnaire(data)
    return {"message": f"開始質問を '{question_id}' に設定しました"}


@router.get("/export")
async def export_csv():
    """問診票をCSV形式でエクスポート"""
    data = load_questionnaire()

    output = io.StringIO()
    output.write('\ufeff')  # BOM for Excel

    writer = csv.writer(output)
    writer.writerow([
        "question_id", "question_text", "answer_value", "answer_label",
        "next_question", "initial_facts"
    ])

    for q in data["questions"]:
        for answer in q["answers"]:
            initial_facts_str = json.dumps(answer.get("initial_facts", []), ensure_ascii=False)
            writer.writerow([
                q["id"],
                q["text"],
                answer["value"],
                answer["label"],
                answer.get("next_question") or "",
                initial_facts_str
            ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=questionnaire.csv"}
    )


@router.post("/import")
async def import_csv(file: UploadFile = File(...)):
    """CSVファイルから問診票をインポート"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルを選択してください")

    content = await file.read()

    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = content.decode('cp932')

    reader = csv.DictReader(io.StringIO(text))

    questions_dict = {}
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            question_id = row.get("question_id", "").strip()
            if not question_id:
                continue

            if question_id not in questions_dict:
                questions_dict[question_id] = {
                    "id": question_id,
                    "text": row.get("question_text", "").strip(),
                    "answers": []
                }

            initial_facts = json.loads(row.get("initial_facts", "[]"))

            questions_dict[question_id]["answers"].append({
                "value": row.get("answer_value", "").strip(),
                "label": row.get("answer_label", "").strip(),
                "next_question": row.get("next_question", "").strip() or None,
                "initial_facts": initial_facts
            })

        except Exception as e:
            errors.append(f"行{row_num}: {str(e)}")

    if errors:
        return {"status": "error", "errors": errors}

    questions = list(questions_dict.values())
    data = {
        "questions": questions,
        "start_question": questions[0]["id"] if questions else ""
    }

    save_questionnaire(data)
    return {"status": "imported", "count": len(questions)}
