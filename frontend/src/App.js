import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [relatedVisaTypes, setRelatedVisaTypes] = useState([]);
  const [answeredQuestions, setAnsweredQuestions] = useState([]);
  const [rulesStatus, setRulesStatus] = useState([]);
  const [derivedFacts, setDerivedFacts] = useState([]);
  const [isComplete, setIsComplete] = useState(false);
  const [diagnosisResult, setDiagnosisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [started, setStarted] = useState(false);

  const startConsultation = async () => {
    setLoading(true);
    console.log('=== 診断開始 ===');
    console.log('Session ID:', sessionId);
    try {
      const response = await fetch(`${API_BASE}/api/consultation/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      const data = await response.json();
      console.log('開始レスポンス:', data);
      console.log('最初の質問:', data.current_question);
      console.log('関連ビザタイプ:', data.related_visa_types);
      console.log('ルール数:', data.rules_status?.length);
      setCurrentQuestion(data.current_question);
      setRelatedVisaTypes(data.related_visa_types || []);
      setRulesStatus(data.rules_status || []);
      setStarted(true);
    } catch (error) {
      console.error('Error starting consultation:', error);
    }
    setLoading(false);
  };

  const answerQuestion = async (answer) => {
    // ボタン連打対策：すでにローディング中なら何もしない
    if (loading) return;

    setLoading(true);
    console.log('=== 回答 ===');
    console.log('質問:', currentQuestion);
    console.log('回答:', answer);
    try {
      // 回答履歴に追加
      setAnsweredQuestions(prev => [...prev, { question: currentQuestion, answer }]);

      const response = await fetch(`${API_BASE}/api/consultation/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, answer })
      });
      const data = await response.json();
      console.log('回答レスポンス:', data);
      console.log('次の質問:', data.current_question);
      console.log('完了フラグ:', data.is_complete);
      console.log('導出された事実:', data.derived_facts);

      // ルールステータスの詳細
      const firedRules = data.rules_status?.filter(r => r.status === 'fired') || [];
      const blockedRules = data.rules_status?.filter(r => r.status === 'blocked') || [];
      const evaluatingRules = data.rules_status?.filter(r => r.status === 'evaluating') || [];
      console.log('発火ルール:', firedRules.map(r => r.id));
      console.log('ブロックルール:', blockedRules.map(r => r.id));
      console.log('評価中ルール:', evaluatingRules.map(r => r.id));

      setCurrentQuestion(data.current_question);
      setRelatedVisaTypes(data.related_visa_types || []);
      setRulesStatus(data.rules_status || []);
      setDerivedFacts(data.derived_facts || []);
      setIsComplete(data.is_complete);

      if (data.is_complete && data.diagnosis_result) {
        console.log('=== 診断結果 ===');
        console.log('結果:', data.diagnosis_result);
        setDiagnosisResult(data.diagnosis_result);
      }
    } catch (error) {
      console.error('Error answering question:', error);
    }
    setLoading(false);
  };

  const goBack = async () => {
    // ボタン連打対策：すでにローディング中なら何もしない
    if (loading) return;

    setLoading(true);
    console.log('=== 戻る ===');
    try {
      const response = await fetch(`${API_BASE}/api/consultation/back`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, steps: 1 })
      });
      const data = await response.json();
      console.log('戻るレスポンス:', data);
      console.log('現在の質問:', data.current_question);
      console.log('回答履歴:', data.answered_questions);

      setCurrentQuestion(data.current_question);
      setRelatedVisaTypes(data.related_visa_types || []);
      setRulesStatus(data.rules_status || []);
      setAnsweredQuestions(data.answered_questions?.map(q => ({
        question: q.condition,
        answer: q.answer
      })) || []);
      setIsComplete(false);
      setDiagnosisResult(null);
    } catch (error) {
      console.error('Error going back:', error);
    }
    setLoading(false);
  };

  const restart = () => {
    // トップページに戻る
    setStarted(false);
    setCurrentQuestion(null);
    setRelatedVisaTypes([]);
    setRulesStatus([]);
    setAnsweredQuestions([]);
    setDerivedFacts([]);
    setIsComplete(false);
    setDiagnosisResult(null);
  };

  if (!started) {
    return (
      <div className="app">
        <header className="header">
          <h1>ビザ選定エキスパートシステム</h1>
        </header>
        <div className="welcome-screen">
          <div className="welcome-content">
            <p className="subtitle">専門知識に基づくビザ選定支援</p>
            <div className="feature-list">
              <div className="feature-item">
                <span className="feature-icon">&#x2713;</span>
                <span>E・L・B・H-1B・J-1ビザを同時診断</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">&#x2713;</span>
                <span>バックワードチェイニングによる効率的な推論</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">&#x2713;</span>
                <span>推論過程のリアルタイム可視化</span>
              </div>
            </div>
            <button className="start-button" onClick={startConsultation} disabled={loading}>
              {loading ? '読み込み中...' : '診断を開始する'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <h1>ビザ選定エキスパートシステム</h1>
        <div className="header-actions">
          <button className="header-button" onClick={restart}>最初から</button>
        </div>
      </header>

      <main className="main-content">
        {/* 左側：診断画面 */}
        <div className="consultation-panel">
          <div className="panel-header">
            <h2>診断</h2>
            <span className="question-count">
              質問 {answeredQuestions.length + 1}
            </span>
          </div>

          {isComplete ? (
            <DiagnosisResult result={diagnosisResult} />
          ) : (
            <>
              {/* 現在の質問 */}
              {currentQuestion && (
                <div className="question-section">
                  <div className="current-question">
                    <div className="visa-tags">
                      {relatedVisaTypes.map(vt => (
                        <span key={vt} className={`visa-tag visa-${vt.replace('-', '')}`}>{vt}</span>
                      ))}
                    </div>
                    <p className="question-text">{currentQuestion}</p>
                  </div>

                  <div className="answer-buttons">
                    <button
                      className="answer-button yes"
                      onClick={() => answerQuestion('yes')}
                      disabled={loading}
                    >
                      はい
                    </button>
                    <button
                      className="answer-button no"
                      onClick={() => answerQuestion('no')}
                      disabled={loading}
                    >
                      いいえ
                    </button>
                    <button
                      className="answer-button unknown"
                      onClick={() => answerQuestion('unknown')}
                      disabled={loading}
                    >
                      わからない
                    </button>
                  </div>

                  <div className="navigation-buttons">
                    <button
                      className="nav-button"
                      onClick={goBack}
                      disabled={loading || answeredQuestions.length === 0}
                    >
                      &#x2190; 前の質問に戻る
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* 右側：推論過程可視化 */}
        <div className="visualization-panel">
          <div className="panel-header">
            <h2>推論過程</h2>
          </div>

          <div className="rules-container">
            {/* ビザタイプ別にグループ化（評価中・評価済みのルールのみ表示） */}
            {['E', 'L', 'B', 'H-1B', 'J-1'].map(visaType => {
              // pending以外（evaluating, fired, blocked, uncertain）のルールのみ表示
              const visaRules = rulesStatus.filter(r =>
                r.visa_type === visaType && r.status !== 'pending'
              );
              if (visaRules.length === 0) return null;

              return (
                <div key={visaType} className={`visa-section visa-section-${visaType.replace('-', '')}`}>
                  <h3 className="visa-section-title">{visaType}ビザ</h3>
                  {visaRules.map(rule => (
                    <RuleCard key={rule.id} rule={rule} />
                  ))}
                </div>
              );
            })}
          </div>

        </div>
      </main>
    </div>
  );
}

function RuleCard({ rule }) {
  const getStatusClass = (status) => {
    switch (status) {
      case 'fired': return 'rule-fired';
      case 'blocked': return 'rule-blocked';
      case 'uncertain': return 'rule-uncertain';
      case 'evaluating': return 'rule-evaluating';
      default: return 'rule-pending';
    }
  };

  const getConditionClass = (condition) => {
    let classes = 'condition-item';
    switch (condition.status) {
      case 'true': classes += ' condition-true'; break;
      case 'false': classes += ' condition-false'; break;
      case 'unknown': classes += ' condition-unknown'; break;
      default: classes += ' condition-unchecked';
    }
    if (condition.is_derived) classes += ' condition-derived';
    return classes;
  };

  return (
    <div className={`rule-card ${getStatusClass(rule.status)}`}>
      <div className="rule-header">
        <span className="rule-id">{rule.id}</span>
        <span className="rule-name">{rule.name}</span>
        <span className={`rule-status-badge ${rule.status}`}>
          {rule.status === 'fired' ? '発火' : rule.status === 'blocked' ? '不可' : rule.status === 'uncertain' ? '不明' : '評価中'}
        </span>
      </div>

      <div className="rule-conditions">
        <span className="conditions-label">IF</span>
        <div className="conditions-list">
          {rule.conditions.map((cond, index) => (
            <React.Fragment key={index}>
              <div className={getConditionClass(cond)}>
                {cond.is_derived && <span className="derived-marker">&#x25C6;</span>}
                {cond.text}
              </div>
              {index < rule.conditions.length - 1 && (
                <span className="operator">{rule.operator}</span>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      <div className="rule-conclusion">
        <span className="conclusion-label">THEN</span>
        <span className={`conclusion-text ${rule.status === 'fired' ? 'conclusion-derived' : ''}`}>
          {rule.conclusion}
        </span>
      </div>
    </div>
  );
}

function DiagnosisResult({ result }) {
  if (!result) return null;

  return (
    <div className="diagnosis-result">
      <h2>診断結果</h2>

      {result.applicable_visas?.length > 0 && (
        <div className="result-section applicable">
          <h3>&#x2713; 申請可能なビザ</h3>
          <ul>
            {result.applicable_visas.map((visa, index) => (
              <li key={index} className="result-item applicable-visa">
                <span className={`visa-badge visa-${visa.type.replace('-', '')}`}>{visa.type}</span>
                <span className="visa-name">{visa.visa}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.conditional_visas?.length > 0 && (
        <div className="result-section conditional">
          <h3>&#x26A0; 条件付きで申請可能なビザ</h3>
          <p className="conditional-note">以下の条件を確認してください</p>
          <ul>
            {result.conditional_visas.map((visa, index) => (
              <li key={index} className="result-item conditional-visa">
                <span className={`visa-badge visa-${visa.type.replace('-', '')}`}>{visa.type}</span>
                <span className="visa-name">{visa.visa}</span>
                <div className="unknown-conditions">
                  <span>確認が必要な条件:</span>
                  <ul>
                    {visa.unknown_conditions.map((cond, i) => (
                      <li key={i}>{cond}</li>
                    ))}
                  </ul>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {(!result.applicable_visas || result.applicable_visas.length === 0) &&
       (!result.conditional_visas || result.conditional_visas.length === 0) && (
        <div className="result-section no-visa">
          <h3>該当するビザがありません</h3>
          <p>入力された条件では、申請可能なビザタイプが見つかりませんでした。</p>
        </div>
      )}
    </div>
  );
}

export default App;
