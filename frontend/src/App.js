import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import './Admin.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [currentPage, setCurrentPage] = useState('home'); // 'home', 'consultation', 'admin'

  return (
    <div className="app">
      <header className="header">
        <h1>ビザ選定エキスパートシステム</h1>
        <div className="header-actions">
          <button
            className={`header-button ${currentPage === 'home' ? 'active' : ''}`}
            onClick={() => setCurrentPage('home')}
          >
            ホーム
          </button>
          <button
            className={`header-button ${currentPage === 'admin' ? 'active' : ''}`}
            onClick={() => setCurrentPage('admin')}
          >
            ルール管理
          </button>
        </div>
      </header>

      {currentPage === 'home' && <HomePage onStartConsultation={() => setCurrentPage('consultation')} />}
      {currentPage === 'consultation' && <ConsultationPage onBack={() => setCurrentPage('home')} />}
      {currentPage === 'admin' && <AdminPage />}
    </div>
  );
}

// ホームページ
function HomePage({ onStartConsultation }) {
  const [loading, setLoading] = useState(false);

  return (
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
        <button className="start-button" onClick={onStartConsultation} disabled={loading}>
          {loading ? '読み込み中...' : '診断を開始する'}
        </button>
      </div>
    </div>
  );
}

// 診断ページ
function ConsultationPage({ onBack }) {
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
    try {
      const response = await fetch(`${API_BASE}/api/consultation/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      const data = await response.json();
      console.log('[START]', data);
      setCurrentQuestion(data.current_question);
      setRelatedVisaTypes(data.related_visa_types || []);
      setRulesStatus(data.rules_status || []);
      setStarted(true);
    } catch (error) {
      console.error('Error starting consultation:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    startConsultation();
  }, []);

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
      console.log('[ANSWER]', answer, data);
      setCurrentQuestion(data.current_question);
      setRelatedVisaTypes(data.related_visa_types || []);
      setRulesStatus(data.rules_status || []);
      setDerivedFacts(data.derived_facts || []);
      setIsComplete(data.is_complete);
      if (data.is_complete && data.diagnosis_result) {
        console.log('[RESULT]', data.diagnosis_result);
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
      console.log('[BACK]', data);
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

        {isComplete ? (
          <DiagnosisResult result={diagnosisResult} />
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
        <div className="rules-container">
          {['E', 'L', 'H-1B', 'B', 'J-1'].map(visaType => {
            const visaRules = rulesStatus.filter(r => r.visa_type === visaType && r.status !== 'pending');
            if (visaRules.length === 0) return null;
            return (
              <div key={visaType} className={`visa-section visa-section-${visaType.replace('-', '')}`}>
                <h3 className="visa-section-title">{visaType}ビザ</h3>
                {visaRules.map(rule => <RuleCard key={rule.id} rule={rule} />)}
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}

// ルールカード
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
              {index < rule.conditions.length - 1 && <span className="operator">{rule.operator}</span>}
            </React.Fragment>
          ))}
        </div>
      </div>
      <div className="rule-conclusion">
        <span className="conclusion-label">THEN</span>
        <span className={`conclusion-text ${rule.status === 'fired' ? 'conclusion-derived' : ''}`}>{rule.conclusion}</span>
      </div>
    </div>
  );
}

// 診断結果
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
                    {visa.unknown_conditions.map((cond, i) => <li key={i}>{cond}</li>)}
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

// 管理ページ
function AdminPage() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRule, setSelectedRule] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [filterVisaType, setFilterVisaType] = useState('');
  const [message, setMessage] = useState(null);

  const fetchRules = async () => {
    setLoading(true);
    try {
      const url = filterVisaType
        ? `${API_BASE}/api/rules?visa_type=${filterVisaType}`
        : `${API_BASE}/api/rules`;
      const response = await fetch(url);
      const data = await response.json();
      console.log('[ADMIN] fetchRules', data);
      setRules(data.rules || []);
    } catch (error) {
      console.error('Error fetching rules:', error);
      setMessage({ type: 'error', text: 'ルールの取得に失敗しました' });
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchRules();
  }, [filterVisaType]);

  const handleSaveRule = async (ruleData) => {
    try {
      const method = editMode ? 'PUT' : 'POST';
      const url = editMode ? `${API_BASE}/api/rules/${ruleData.id}` : `${API_BASE}/api/rules`;
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ruleData)
      });

      if (response.ok) {
        setMessage({ type: 'success', text: editMode ? 'ルールを更新しました' : 'ルールを作成しました' });
        setSelectedRule(null);
        setEditMode(false);
        fetchRules();
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || '保存に失敗しました' });
      }
    } catch (error) {
      console.error('Error saving rule:', error);
      setMessage({ type: 'error', text: '保存に失敗しました' });
    }
  };

  const handleDeleteRule = async (ruleId) => {
    if (!window.confirm(`ルール ${ruleId} を削除しますか？`)) return;

    try {
      const response = await fetch(`${API_BASE}/api/rules/${ruleId}`, { method: 'DELETE' });
      if (response.ok) {
        setMessage({ type: 'success', text: 'ルールを削除しました' });
        fetchRules();
      } else {
        setMessage({ type: 'error', text: '削除に失敗しました' });
      }
    } catch (error) {
      console.error('Error deleting rule:', error);
      setMessage({ type: 'error', text: '削除に失敗しました' });
    }
  };

  const handleValidate = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/validation/check`);
      const data = await response.json();
      if (data.status === 'ok') {
        setMessage({ type: 'success', text: '整合性チェック: 問題ありません' });
      } else {
        setMessage({ type: 'warning', text: `整合性チェック: ${data.issues.length}件の問題が見つかりました` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '整合性チェックに失敗しました' });
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h2>ルール管理</h2>
        <div className="admin-actions">
          <select value={filterVisaType} onChange={(e) => setFilterVisaType(e.target.value)}>
            <option value="">全てのビザタイプ</option>
            <option value="E">Eビザ</option>
            <option value="L">Lビザ</option>
            <option value="B">Bビザ</option>
            <option value="H-1B">H-1Bビザ</option>
            <option value="J-1">J-1ビザ</option>
          </select>
          <button className="admin-button" onClick={() => { setSelectedRule({}); setEditMode(false); }}>
            新規ルール
          </button>
          <button className="admin-button secondary" onClick={handleValidate}>
            整合性チェック
          </button>
        </div>
      </div>

      {message && (
        <div className={`admin-message ${message.type}`}>
          {message.text}
          <button onClick={() => setMessage(null)}>&times;</button>
        </div>
      )}

      <div className={`admin-content ${selectedRule ? 'with-editor' : ''}`}>
        <div className="rules-list">
          {loading ? (
            <p>読み込み中...</p>
          ) : (
            <table className="rules-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>名前</th>
                  <th>ビザ</th>
                  <th>条件数</th>
                  <th>タイプ</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {rules.map(rule => (
                  <tr key={rule.id} className={selectedRule?.id === rule.id ? 'selected' : ''}>
                    <td>{rule.id}</td>
                    <td>{rule.name}</td>
                    <td><span className={`visa-badge visa-${rule.visa_type.replace('-', '')}`}>{rule.visa_type}</span></td>
                    <td>{rule.conditions.length}</td>
                    <td>{rule.is_or_rule ? 'OR' : 'AND'}</td>
                    <td>
                      <button className="table-button" onClick={() => { setSelectedRule(rule); setEditMode(true); }}>編集</button>
                      <button className="table-button danger" onClick={() => handleDeleteRule(rule.id)}>削除</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {selectedRule && (
          <RuleEditor
            rule={selectedRule}
            isEdit={editMode}
            onSave={handleSaveRule}
            onCancel={() => { setSelectedRule(null); setEditMode(false); }}
          />
        )}
      </div>
    </div>
  );
}

// ルール編集フォーム
function RuleEditor({ rule, isEdit, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    id: rule.id || '',
    name: rule.name || '',
    conditions: rule.conditions || [''],
    action: rule.action || '',
    is_or_rule: rule.is_or_rule || false,
    visa_type: rule.visa_type || 'E',
    rule_type: rule.rule_type || 'i'
  });

  const handleConditionChange = (index, value) => {
    const newConditions = [...formData.conditions];
    newConditions[index] = value;
    setFormData({ ...formData, conditions: newConditions });
  };

  const addCondition = () => {
    setFormData({ ...formData, conditions: [...formData.conditions, ''] });
  };

  const removeCondition = (index) => {
    const newConditions = formData.conditions.filter((_, i) => i !== index);
    setFormData({ ...formData, conditions: newConditions });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const cleanedConditions = formData.conditions.filter(c => c.trim() !== '');
    onSave({ ...formData, conditions: cleanedConditions });
  };

  return (
    <div className="rule-editor">
      <h3>{isEdit ? 'ルール編集' : '新規ルール作成'}</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>ID</label>
          <input
            type="text"
            value={formData.id}
            onChange={(e) => setFormData({ ...formData, id: e.target.value })}
            disabled={isEdit}
            required
            placeholder="例: E012"
          />
        </div>

        <div className="form-group">
          <label>ルール名</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            placeholder="例: 新規条件"
          />
        </div>

        <div className="form-group">
          <label>ビザタイプ</label>
          <select value={formData.visa_type} onChange={(e) => setFormData({ ...formData, visa_type: e.target.value })}>
            <option value="E">Eビザ</option>
            <option value="L">Lビザ</option>
            <option value="B">Bビザ</option>
            <option value="H-1B">H-1Bビザ</option>
            <option value="J-1">J-1ビザ</option>
          </select>
        </div>

        <div className="form-group">
          <label>条件タイプ</label>
          <div className="radio-group">
            <label>
              <input
                type="radio"
                checked={!formData.is_or_rule}
                onChange={() => setFormData({ ...formData, is_or_rule: false })}
              /> AND（全て満たす）
            </label>
            <label>
              <input
                type="radio"
                checked={formData.is_or_rule}
                onChange={() => setFormData({ ...formData, is_or_rule: true })}
              /> OR（いずれか満たす）
            </label>
          </div>
        </div>

        <div className="form-group">
          <label>ルールタイプ</label>
          <select value={formData.rule_type} onChange={(e) => setFormData({ ...formData, rule_type: e.target.value })}>
            <option value="i">開始ルール（直接質問）</option>
            <option value="m">中間ルール（導出条件）</option>
          </select>
        </div>

        <div className="form-group">
          <label>条件 (IF)</label>
          {formData.conditions.map((cond, index) => (
            <div key={index} className="condition-input">
              <input
                type="text"
                value={cond}
                onChange={(e) => handleConditionChange(index, e.target.value)}
                placeholder="条件を入力"
              />
              {formData.conditions.length > 1 && (
                <button type="button" className="remove-btn" onClick={() => removeCondition(index)}>-</button>
              )}
            </div>
          ))}
          <button type="button" className="add-btn" onClick={addCondition}>+ 条件追加</button>
        </div>

        <div className="form-group">
          <label>結論 (THEN)</label>
          <input
            type="text"
            value={formData.action}
            onChange={(e) => setFormData({ ...formData, action: e.target.value })}
            required
            placeholder="結論を入力"
          />
        </div>

        <div className="form-actions">
          <button type="submit" className="save-btn">保存</button>
          <button type="button" className="cancel-btn" onClick={onCancel}>キャンセル</button>
        </div>
      </form>
    </div>
  );
}

export default App;
