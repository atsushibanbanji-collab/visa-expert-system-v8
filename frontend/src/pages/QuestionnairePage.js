import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';

function QuestionnairePage({ onComplete, onSkip }) {
  const [questionnaire, setQuestionnaire] = useState(null);
  const [currentQuestionId, setCurrentQuestionId] = useState(null);
  const [answerHistory, setAnswerHistory] = useState([]);
  const [collectedFacts, setCollectedFacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchQuestionnaire();
  }, []);

  const fetchQuestionnaire = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/questionnaire`);
      if (!response.ok) {
        throw new Error('問診票の読み込みに失敗しました');
      }
      const data = await response.json();
      setQuestionnaire(data);
      setCurrentQuestionId(data.start_question);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching questionnaire:', err);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentQuestion = () => {
    if (!questionnaire || !currentQuestionId) return null;
    return questionnaire.questions.find(q => q.id === currentQuestionId);
  };

  const handleAnswer = (answer) => {
    const currentQuestion = getCurrentQuestion();
    if (!currentQuestion) return;

    // 回答履歴に追加
    const newHistory = [...answerHistory, {
      questionId: currentQuestionId,
      questionText: currentQuestion.text,
      answer: answer.label,
      answerValue: answer.value
    }];
    setAnswerHistory(newHistory);

    // initial_factsを収集
    const newFacts = [...collectedFacts];
    if (answer.initial_facts && answer.initial_facts.length > 0) {
      for (const fact of answer.initial_facts) {
        const existingIndex = newFacts.findIndex(f => f.fact_name === fact.fact_name);
        if (existingIndex >= 0) {
          newFacts.splice(existingIndex, 1);
        }
        newFacts.push(fact);
      }
    }
    setCollectedFacts(newFacts);

    // 次の質問へ、またはendComplete
    if (answer.next_question) {
      setCurrentQuestionId(answer.next_question);
    } else {
      onComplete(newFacts);
    }
  };

  const handleBack = () => {
    if (answerHistory.length === 0) return;

    const lastAnswer = answerHistory[answerHistory.length - 1];
    const newHistory = answerHistory.slice(0, -1);
    setAnswerHistory(newHistory);

    // この回答で追加したfactsを削除
    const currentQuestion = questionnaire.questions.find(q => q.id === lastAnswer.questionId);
    if (currentQuestion) {
      const selectedAnswer = currentQuestion.answers.find(a => a.value === lastAnswer.answerValue);
      if (selectedAnswer && selectedAnswer.initial_facts) {
        const factsToRemove = selectedAnswer.initial_facts.map(f => f.fact_name);
        const newFacts = collectedFacts.filter(f => !factsToRemove.includes(f.fact_name));
        setCollectedFacts(newFacts);
      }
    }

    setCurrentQuestionId(lastAnswer.questionId);
  };

  if (loading) {
    return (
      <div className="welcome-screen">
        <p>読み込み中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="welcome-screen">
        <p className="error-message">{error}</p>
        <button className="big-start-button" onClick={onSkip}>
          スキップして診断へ
        </button>
      </div>
    );
  }

  const currentQuestion = getCurrentQuestion();

  if (!currentQuestion) {
    return (
      <div className="welcome-screen">
        <p>問診票が設定されていません</p>
        <button className="big-start-button" onClick={onSkip}>
          診断を開始
        </button>
      </div>
    );
  }

  return (
    <main className="main-content">
      <div className="consultation-panel">
        <div className="panel-header">
          <h2>問診票</h2>
          <span className="question-count">質問 {answerHistory.length + 1}</span>
        </div>

        <div className="questionnaire-progress">
          <div
            className="progress-bar"
            style={{
              width: `${Math.min((answerHistory.length + 1) / questionnaire.questions.length * 100, 100)}%`
            }}
          />
        </div>

        <div className="question-section">
          <div className="current-question">
            <p className="question-text">{currentQuestion.text}</p>
          </div>

          <div className="questionnaire-answers">
            {currentQuestion.answers.map((answer) => (
              <button
                key={answer.value}
                className="questionnaire-answer-button"
                onClick={() => handleAnswer(answer)}
              >
                {answer.label}
              </button>
            ))}
          </div>

          <div className="navigation-buttons">
            {answerHistory.length > 0 && (
              <button className="nav-button" onClick={handleBack}>
                &#x2190; 前の質問に戻る
              </button>
            )}
            <button className="nav-button skip-button" onClick={onSkip}>
              スキップして診断へ
            </button>
          </div>
        </div>
      </div>

      <div className="visualization-panel">
        <div className="panel-header">
          <h2>回答状況</h2>
        </div>
        <div className="questionnaire-status">
          {answerHistory.length > 0 ? (
            <div className="answer-history">
              <h3>回答履歴</h3>
              <ul>
                {answerHistory.map((item, index) => (
                  <li key={index}>
                    <span className="history-number">{index + 1}.</span>
                    <span className="history-question">{item.questionText}</span>
                    <span className="history-arrow">→</span>
                    <span className="history-answer">{item.answer}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="no-history">まだ回答がありません</p>
          )}

          {collectedFacts.length > 0 && (
            <div className="collected-facts">
              <h3>収集された初期情報</h3>
              <ul>
                {collectedFacts.map((fact, index) => (
                  <li key={index} className={fact.value ? 'fact-true' : 'fact-false'}>
                    <span className="fact-status">{fact.value ? '✓' : '✗'}</span>
                    <span className="fact-name">{fact.fact_name}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

export default QuestionnairePage;
