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
  const [filterVisaType, setFilterVisaType] = useState('');
  const [message, setMessage] = useState(null);
  const [showNewRuleForm, setShowNewRuleForm] = useState(false);

  const fetchRules = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/api/rules?sort=none`;
      if (filterVisaType) {
        url += `&visa_type=${filterVisaType}`;
      }
      const response = await fetch(url);
      const data = await response.json();
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

  const handleSaveRule = async (ruleData, isNew = false) => {
    try {
      const method = isNew ? 'POST' : 'PUT';
      const url = isNew ? `${API_BASE}/api/rules` : `${API_BASE}/api/rules/${ruleData.id}`;
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ruleData)
      });

      if (response.ok) {
        setMessage({ type: 'success', text: isNew ? 'ルールを作成しました' : '保存しました' });
        setShowNewRuleForm(false);
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
    if (!window.confirm(`このルールを削除しますか？`)) return;

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

  const handleAutoOrganize = async () => {
    if (!window.confirm('ルールを依存関係に基づいて自動整理しますか？\n\n整理ロジック:\n・ビザタイプ順（E→L→H-1B→B→J-1）\n・各ビザ内で依存深度順（ゴール→中間→初期）')) return;

    try {
      const response = await fetch(`${API_BASE}/api/rules/auto-organize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (response.ok) {
        setMessage({ type: 'success', text: 'ルールを整理しました' });
        fetchRules();
      } else {
        setMessage({ type: 'error', text: '整理に失敗しました' });
      }
    } catch (error) {
      console.error('Error organizing rules:', error);
      setMessage({ type: 'error', text: '整理に失敗しました' });
    }
  };

  const moveRule = async (index, direction) => {
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= rules.length) return;

    const newRules = [...rules];
    [newRules[index], newRules[newIndex]] = [newRules[newIndex], newRules[index]];
    setRules(newRules);

    try {
      await fetch(`${API_BASE}/api/rules/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rule_ids: newRules.map(r => r.id) })
      });
    } catch (error) {
      console.error('Error saving order:', error);
      setMessage({ type: 'error', text: '順序の保存に失敗しました' });
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
            <option value="H-1B">H-1Bビザ</option>
            <option value="B">Bビザ</option>
            <option value="J-1">J-1ビザ</option>
          </select>
          <button className="admin-button" onClick={() => setShowNewRuleForm(true)}>
            新規ルール
          </button>
          <button className="admin-button secondary" onClick={handleAutoOrganize}>
            自動整理
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

      {showNewRuleForm && (
        <AdminRuleCard
          rule={{ id: '', name: '', conditions: [''], action: '', is_or_rule: false, visa_type: 'E', rule_type: 'i' }}
          index={-1}
          isNew={true}
          allRules={rules}
          onSave={(data) => handleSaveRule(data, true)}
          onCancel={() => setShowNewRuleForm(false)}
          onDelete={() => {}}
        />
      )}

      <div className="admin-rules-cards">
        {loading ? (
          <p className="loading-text">読み込み中...</p>
        ) : (
          rules.map((rule, index) => (
            <AdminRuleCard
              key={rule.id}
              rule={rule}
              index={index}
              isNew={false}
              totalRules={rules.length}
              onSave={(data) => handleSaveRule(data, false)}
              onDelete={() => handleDeleteRule(rule.id)}
              onMoveUp={() => moveRule(index, -1)}
              onMoveDown={() => moveRule(index, 1)}
            />
          ))
        )}
      </div>
    </div>
  );
}

// 管理画面用ルールカード（常時編集可能・コンパクト）
function AdminRuleCard({ rule, index, isNew, totalRules, allRules, onSave, onCancel, onDelete, onMoveUp, onMoveDown }) {
  // 次の利用可能なIDを生成（一番若い空き番号を探す）
  const generateNextId = (visaType, rules) => {
    if (!rules) return '';
    const prefix = visaType.replace('-', '');
    const existingIds = new Set(
      rules
        .filter(r => r.visa_type === visaType)
        .map(r => {
          const match = r.id.match(new RegExp(`^${prefix}(\\d+)$`));
          return match ? parseInt(match[1], 10) : 0;
        })
        .filter(n => n > 0)
    );
    // 1から順に空き番号を探す
    let nextNum = 1;
    while (existingIds.has(nextNum)) {
      nextNum++;
    }
    return `${prefix}${String(nextNum).padStart(3, '0')}`;
  };

  const initialVisaType = rule.visa_type || 'E';
  const [formData, setFormData] = useState({
    id: isNew ? generateNextId(initialVisaType, allRules) : (rule.id || ''),
    name: rule.name || '',
    conditions: rule.conditions?.length ? rule.conditions : [''],
    action: rule.action || '',
    is_or_rule: rule.is_or_rule || false,
    visa_type: initialVisaType,
    rule_type: rule.rule_type || 'i'
  });
  const [hasChanges, setHasChanges] = useState(isNew);

  const updateField = (field, value) => {
    // ビザタイプ変更時はIDも自動更新（新規作成時のみ）
    if (field === 'visa_type' && isNew) {
      const newId = generateNextId(value, allRules);
      setFormData({ ...formData, [field]: value, id: newId });
    } else {
      setFormData({ ...formData, [field]: value });
    }
    setHasChanges(true);
  };

  const handleConditionChange = (idx, value) => {
    const newConds = [...formData.conditions];
    newConds[idx] = value;
    setFormData({ ...formData, conditions: newConds });
    setHasChanges(true);
  };

  const addCondition = () => {
    setFormData({ ...formData, conditions: [...formData.conditions, ''] });
    setHasChanges(true);
  };

  const removeCondition = (idx) => {
    if (formData.conditions.length > 1) {
      setFormData({ ...formData, conditions: formData.conditions.filter((_, i) => i !== idx) });
      setHasChanges(true);
    }
  };

  const moveCondition = (idx, direction) => {
    const newIdx = idx + direction;
    if (newIdx < 0 || newIdx >= formData.conditions.length) return;
    const newConds = [...formData.conditions];
    [newConds[idx], newConds[newIdx]] = [newConds[newIdx], newConds[idx]];
    setFormData({ ...formData, conditions: newConds });
    setHasChanges(true);
  };

  const handleSave = () => {
    const cleanedConditions = formData.conditions.filter(c => c.trim() !== '');
    if (!formData.id || !formData.name || cleanedConditions.length === 0 || !formData.action) {
      alert('ID、名前、条件、結論は必須です');
      return;
    }
    onSave({ ...formData, conditions: cleanedConditions });
    setHasChanges(false);
  };

  const handleCancel = () => {
    setFormData({
      id: rule.id || '',
      name: rule.name || '',
      conditions: rule.conditions?.length ? rule.conditions : [''],
      action: rule.action || '',
      is_or_rule: rule.is_or_rule || false,
      visa_type: rule.visa_type || 'E',
      rule_type: rule.rule_type || 'i'
    });
    setHasChanges(false);
    if (isNew) onCancel();
  };

  return (
    <div className={`admin-rule-card ${hasChanges ? 'has-changes' : ''}`}>
      <div className="rule-card-main">
        {/* 左側: 移動ボタン */}
        {!isNew && (
          <div className="rule-move-buttons">
            <button className="rule-move-btn" onClick={onMoveUp} disabled={index === 0}>↑</button>
            <button className="rule-move-btn" onClick={onMoveDown} disabled={index === totalRules - 1}>↓</button>
          </div>
        )}

        {/* 中央: ルール内容 */}
        <div className="rule-card-content">
          {/* ヘッダー行 */}
          <div className="rule-card-header">
            <span className="rule-number">#{isNew ? 'NEW' : index + 1}</span>
            <input type="text" className="rule-id-input" value={formData.id} onChange={(e) => updateField('id', e.target.value)} placeholder="ID" />
            <select className="rule-visa-select" value={formData.visa_type} onChange={(e) => updateField('visa_type', e.target.value)}>
              <option value="E">E</option>
              <option value="L">L</option>
              <option value="H-1B">H-1B</option>
              <option value="B">B</option>
              <option value="J-1">J-1</option>
            </select>
            <select className="rule-type-select" value={formData.is_or_rule ? 'or' : 'and'} onChange={(e) => updateField('is_or_rule', e.target.value === 'or')}>
              <option value="and">AND</option>
              <option value="or">OR</option>
            </select>
            <input type="text" className="rule-name-input" value={formData.name} onChange={(e) => updateField('name', e.target.value)} placeholder="ルール名" />
          </div>

          {/* THEN/IF 行 */}
          <div className="rule-card-body">
            <div className="rule-card-conclusion">
              <span className="label">THEN:</span>
              <input type="text" value={formData.action} onChange={(e) => updateField('action', e.target.value)} placeholder="結論" />
            </div>
            <div className="rule-card-conditions">
              <span className="label">IF:</span>
              <div className="conditions-edit-list">
                {formData.conditions.map((cond, idx) => (
                  <div key={idx} className="condition-edit-row">
                    <input type="text" value={cond} onChange={(e) => handleConditionChange(idx, e.target.value)} placeholder="条件" />
                    {formData.conditions.length > 1 && (
                      <>
                        <button type="button" className="cond-move-btn" onClick={() => moveCondition(idx, -1)} disabled={idx === 0}>↑</button>
                        <button type="button" className="cond-move-btn" onClick={() => moveCondition(idx, 1)} disabled={idx === formData.conditions.length - 1}>↓</button>
                        <button type="button" className="cond-remove-btn" onClick={() => removeCondition(idx)}>×</button>
                      </>
                    )}
                  </div>
                ))}
                <button type="button" className="cond-add-btn" onClick={addCondition}>+ 条件追加</button>
              </div>
            </div>
          </div>
        </div>

        {/* 右側: アクションボタン */}
        <div className="rule-action-buttons">
          <button className="delete-btn" onClick={isNew ? onCancel : onDelete}>{isNew ? '取消' : '削除'}</button>
        </div>
      </div>

      {/* 変更時の保存/キャンセル */}
      {hasChanges && (
        <div className="rule-card-actions">
          <button className="save-btn" onClick={handleSave}>保存</button>
          <button className="cancel-btn" onClick={handleCancel}>元に戻す</button>
        </div>
      )}
    </div>
  );
}

export default App;
