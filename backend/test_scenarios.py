#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ビザ選定エキスパートシステム テストスクリプト

使い方:
  python test_scenarios.py [テスト回数]

  例:
    python test_scenarios.py      # デフォルト10回
    python test_scenarios.py 5    # 5回テスト
    python test_scenarios.py 20   # 20回テスト

結果は test_results.txt に出力されます
"""

import requests
import uuid
import sys
import os
import random
from datetime import datetime

# ローカルまたはデプロイ先を切り替え
BASE_URL = "http://localhost:8000"
# BASE_URL = "https://visa-expert-backend.onrender.com"

# 結果出力ファイル（backendフォルダ内に保存）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "test_results.txt")

# 回答の選択肢と重み（yes:no:unknown = 3:3:4）
ANSWERS = ["yes", "no", "unknown"]
ANSWER_WEIGHTS = [3, 3, 4]  # 重み付き選択用


def run_random_test(test_number: int, answer_mode: str = "random", seed: int = None):
    """
    ランダムまたは固定回答でテストを実行

    Args:
        test_number: テスト番号
        answer_mode: "random", "yes", "no", "unknown" のいずれか
        seed: ランダムシード（再現性のため）

    Returns:
        tuple: (output_lines, questions_asked, answers_given, result)
    """
    if seed is not None:
        random.seed(seed)

    output = []
    output.append(f"\n{'='*60}")
    if answer_mode == "random":
        output.append(f"テスト {test_number}: ランダム回答 (seed={seed})")
    else:
        output.append(f"テスト {test_number}: 全部 {answer_mode.upper()}")
    output.append(f"{'='*60}")

    session_id = str(uuid.uuid4())

    # 診断開始
    try:
        resp = requests.post(
            f"{BASE_URL}/api/consultation/start",
            json={"session_id": session_id},
            timeout=10
        )
        data = resp.json()
    except Exception as e:
        output.append(f"[ERROR] 接続エラー: {e}")
        return output, [], [], {}

    questions_asked = []
    answers_given = []
    current_q = data.get("current_question")

    output.append(f"\n--- 質問と回答の流れ ---")

    question_count = 0
    max_questions = 50  # 無限ループ防止

    while current_q and question_count < max_questions:
        question_count += 1
        questions_asked.append(current_q)

        # 回答を決定
        if answer_mode == "random":
            answer = random.choices(ANSWERS, weights=ANSWER_WEIGHTS, k=1)[0]
        else:
            answer = answer_mode

        answers_given.append(answer)
        output.append(f"  Q{question_count}: {current_q}")
        output.append(f"  A{question_count}: {answer}")

        try:
            resp = requests.post(
                f"{BASE_URL}/api/consultation/answer",
                json={"session_id": session_id, "answer": answer},
                timeout=10
            )
            data = resp.json()
        except Exception as e:
            output.append(f"[ERROR] 回答送信エラー: {e}")
            return output, questions_asked, answers_given, {}

        current_q = data.get("current_question")

    if not current_q:
        output.append(f"  [終了] 全質問完了（{question_count}問）")
    else:
        output.append(f"  [警告] 質問数上限に達しました（{max_questions}問）")

    # 結果表示
    output.append(f"\n--- 診断結果 ---")

    result = data.get("diagnosis_result", {})
    applicable = result.get("applicable_visas", [])
    conditional = result.get("conditional_visas", [])

    if applicable:
        visa_list = ", ".join([v['visa'] for v in applicable])
        output.append(f"  取得可能ビザ: {visa_list}")
    else:
        output.append(f"  取得可能ビザ: なし")

    if conditional:
        visa_list = ", ".join([v['visa'] for v in conditional])
        output.append(f"  条件付き可能: {visa_list}")
    else:
        output.append(f"  条件付き可能: なし")

    # 統計情報
    output.append(f"\n--- 統計 ---")
    output.append(f"  質問数: {len(questions_asked)}")
    if answer_mode == "random":
        yes_count = answers_given.count("yes")
        no_count = answers_given.count("no")
        unknown_count = answers_given.count("unknown")
        output.append(f"  回答内訳: yes={yes_count}, no={no_count}, unknown={unknown_count}")

    return output, questions_asked, answers_given, result


def main():
    """メイン実行"""
    all_output = []

    # ヘッダー
    all_output.append("=" * 60)
    all_output.append("ビザ選定エキスパートシステム テスト結果")
    all_output.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    all_output.append(f"対象: {BASE_URL}")
    all_output.append("=" * 60)

    # コンソールにも表示
    for line in all_output:
        print(line)

    # テスト回数を取得
    if len(sys.argv) > 1:
        try:
            num_tests = int(sys.argv[1])
        except ValueError:
            num_tests = 10
    else:
        num_tests = 10

    # テスト結果を格納
    results_summary = []

    # テスト1: 全部UNKNOWN
    output, questions, answers, result = run_random_test(1, answer_mode="unknown")
    all_output.extend(output)
    for line in output:
        print(line)
    applicable = [v['visa'] for v in result.get("applicable_visas", [])]
    conditional = [v['visa'] for v in result.get("conditional_visas", [])]
    results_summary.append({
        "test": 1,
        "mode": "全部UNKNOWN",
        "questions": len(questions),
        "applicable": applicable,
        "conditional": conditional
    })

    # テスト2以降: ランダム
    for i in range(2, num_tests + 1):
        seed = i * 1000 + int(datetime.now().timestamp()) % 1000
        output, questions, answers, result = run_random_test(i, answer_mode="random", seed=seed)
        all_output.extend(output)
        for line in output:
            print(line)
        applicable = [v['visa'] for v in result.get("applicable_visas", [])]
        conditional = [v['visa'] for v in result.get("conditional_visas", [])]
        results_summary.append({
            "test": i,
            "mode": f"ランダム(seed={seed})",
            "questions": len(questions),
            "applicable": applicable,
            "conditional": conditional
        })

    # サマリー
    summary = []
    summary.append("\n" + "=" * 60)
    summary.append("テスト結果サマリー")
    summary.append("=" * 60)

    for r in results_summary:
        applicable_str = ", ".join(r["applicable"]) if r["applicable"] else "なし"
        conditional_str = ", ".join(r["conditional"]) if r["conditional"] else "なし"
        summary.append(f"  テスト{r['test']}: {r['mode']}")
        summary.append(f"    質問数: {r['questions']}, 取得可能: {applicable_str}, 条件付き: {conditional_str}")

    # 統計
    summary.append("\n--- 全体統計 ---")
    total_applicable = sum(1 for r in results_summary if r["applicable"])
    total_conditional = sum(1 for r in results_summary if r["conditional"])
    summary.append(f"  ビザ取得可能: {total_applicable}/{len(results_summary)} テスト")
    summary.append(f"  条件付き可能: {total_conditional}/{len(results_summary)} テスト")

    all_output.extend(summary)
    for line in summary:
        print(line)

    # ファイルに書き出し
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_output))

    print(f"\n結果を {OUTPUT_FILE} に保存しました")


if __name__ == "__main__":
    main()
