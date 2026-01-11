import React, { useState, useEffect, useRef } from 'react';
import { API_BASE } from '../config';
import { VISA_TYPES } from '../constants';
import RuleCard from '../components/consultation/RuleCard';
import DiagnosisResult from '../components/consultation/DiagnosisResult';

function ConsultationPage({ onBack }) {
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [relatedVisaTypes, setRelatedVisaTypes] = useState([]);
  const [answeredQuestions, setAnsweredQuestions] = useState([]);
  const [rulesStatus, setRulesStatus] = useState([]);
  const [isComplete, setIsComplete] = useState(false);
  const [diagnosisResult, setDiagnosisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [validationError, setValidationError] = useState(null);
  const containerRef = useRef(null);

  const startConsultation = async () => {
    setLoading(true);
    setValidationError(null);
    try {
      const response = await fetch(`${API_BASE}/api/consultation/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      const data = await response.json();

      if (!response.ok) {
        setValidationError({
          message: data.detail?.error || '診断を開始できません',
          issues: data.detail?.issues || []
        });
        return;
      }

      setCurrentQuestion(data.current_question);
      setRelatedVisaTypes(data.related_visa_types || []);
      setRulesStatus(data.rules_status || []);
    } catch (error) {
      console.error('Error starting consultation:', error);
      setValidationError({ message: 'サーバーに接続できません', issues: [] });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    startConsultation();
  }, []);

  // 現在の質問の条件にスクロール（ルールカード単位で表示）
  useEffect(() => {
    if (containerRef.current && currentQuestion) {
      requestAnimationFrame(() => {
        const conditionEl = containerRef.current?.querySelector('[data-current-condition="true"]');
        if (conditionEl) {
          const ruleCard = conditionEl.closest('.rule-card');
          if (ruleCard) {
            ruleCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }
        }
      });
    }
  }, [currentQuestion, rulesStatus]);

  const answerQuestion = async (answer) => {
    if (loading) return;
    setLoading(true);
    try {
      setAnsweredQuestions(prev => [...prev, { question: currentQuestion, answer }]);
      const response = await fetch(`${API_BASE}/api/consultation/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, answer })
      });
      const data = await response.json();
      setCurrentQuestion(data.current_question);
      setRelatedVisaTypes(data.related_visa_types || []);
      setRulesStatus(data.rules_status || []);
      setIsComplete(data.is_complete);
      if (data.is_complete && data.diagnosis_result) {
        setDiagnosisResult(data.diagnosis_result);
      }
    } catch (error) {
      console.error('Error answering question:', error);
    }
    setLoading(false);
  };

  const goBack = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/consultation/back`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, steps: 1 })
      });
      const data = await response.json();
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

  return (
    <main className="main-content">
      <div className="consultation-panel">
        <div className="panel-header">
          <h2>診断</h2>
          <span className="question-count">質問 {answeredQuestions.length + 1}</span>
        </div>

        {validationError ? (
          <div className="validation-error">
            <h3>診断を開始できません</h3>
            <p>{validationError.message}</p>
            {validationError.issues.length > 0 && (
              <ul className="error-issues">
                {validationError.issues.map((issue, idx) => (
                  <li key={idx}>{issue}</li>
                ))}
              </ul>
            )}
            <button className="nav-button" onClick={onBack}>ホームに戻る</button>
          </div>
        ) : isComplete ? (
          <DiagnosisResult result={diagnosisResult} onGoBack={goBack} onRestart={onBack} />
        ) : (
          <>
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
                  <button className="answer-button yes" onClick={() => answerQuestion('yes')} disabled={loading}>はい</button>
                  <button className="answer-button no" onClick={() => answerQuestion('no')} disabled={loading}>いいえ</button>
                  <button className="answer-button unknown" onClick={() => answerQuestion('unknown')} disabled={loading}>わからない</button>
                </div>
                <div className="navigation-buttons">
                  <button className="nav-button" onClick={goBack} disabled={loading || answeredQuestions.length === 0}>
                    &#x2190; 前の質問に戻る
                  </button>
                  <button className="nav-button" onClick={onBack}>最初から</button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <div className="visualization-panel">
        <div className="panel-header">
          <h2>推論過程</h2>
        </div>
        <div className="rules-container" ref={containerRef}>
          {VISA_TYPES.map(visaType => {
            const visaRules = rulesStatus.filter(r => r.visa_type === visaType && r.status !== 'pending');
            if (visaRules.length === 0) return null;
            return (
              <div key={visaType} className={`visa-section visa-section-${visaType.replace('-', '')}`}>
                <h3 className="visa-section-title">{visaType}ビザ</h3>
                {visaRules.map(rule => (
                  <RuleCard key={rule.action} rule={rule} currentQuestion={currentQuestion} />
                ))}
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}

export default ConsultationPage;
