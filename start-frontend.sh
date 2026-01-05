#!/bin/bash
echo "========================================"
echo " ビザ選定エキスパートシステム - フロントエンド"
echo "========================================"

cd "$(dirname "$0")/frontend"

echo ""
echo "node_modulesをチェック中..."
if [ ! -d "node_modules" ]; then
    echo "依存パッケージをインストール中..."
    npm install
fi

echo ""
echo "開発サーバーを起動中... (http://localhost:3000)"
echo "Ctrl+C で停止できます"
echo ""
npm start
