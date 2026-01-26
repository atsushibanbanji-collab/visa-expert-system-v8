"""
ビザ選定エキスパートシステム - FastAPI メインアプリケーション
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.consultation import router as consultation_router
from routes.rules import router as rules_router
from routes.conditions import router as conditions_router
from routes.questionnaire import router as questionnaire_router

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

# ルーターを登録
app.include_router(consultation_router)
app.include_router(rules_router)
app.include_router(conditions_router)
app.include_router(questionnaire_router)


@app.get("/")
async def root():
    return {"message": "ビザ選定エキスパートシステム API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
