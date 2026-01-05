#!/bin/bash
echo "========================================"
echo " ビザ選定エキスパートシステム - バックエンド"
echo "========================================"

cd "$(dirname "$0")/backend"

echo ""
echo "Python仮想環境をチェック中..."
if [ ! -d "venv" ]; then
    echo "仮想環境を作成中..."
    python -m venv venv
fi

echo ""
echo "仮想環境をアクティベート中..."
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate

echo ""
echo "依存パッケージをインストール中..."
pip install -r requirements.txt -q

echo ""
echo "サーバーを起動中... (http://localhost:8000)"
echo "Ctrl+C で停止できます"
echo ""
uvicorn main:app --reload --host 0.0.0.0 --port 8000
