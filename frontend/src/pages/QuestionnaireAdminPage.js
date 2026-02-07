import React, { useState, useEffect, useMemo } from 'react';
import { API_BASE } from '../config';

function TreeNode({ node, questionnaire, onEdit, onDelete, onSetStart }) {
  if (!node) return null;

  if (node.type === 'ref') {
    return <div className="tree-ref-card">&#8618; 参照</div>;
  }

  if (node.type === 'missing') {
    return <div className="tree-missing-card">未定義</div>;
  }

  const q = node.question;
  const isStart = q.id === questionnaire.start_question;

  return (
    <div className="tree-node">
      <div className={`tree-card${isStart ? ' tree-card-start' : ''}`} onClick={() => onEdit(q)}>
        {isStart && <span className="tree-start-badge">開始</span>}
        <div className="tree-card-text">{q.text}</div>
        <div className="tree-card-actions" onClick={e => e.stopPropagation()}>
          {!isStart && <button className="small-button" onClick={() => onSetStart(q.id)}>開始</button>}
          <button className="small-button" onClick={() => onEdit(q)}>編集</button>
          <button className="small-button danger" onClick={() => onDelete(q.id)}>削除</button>
        </div>
      </div>

      {node.children.length > 0 && (
        <>
          <div className="tree-connector" />
          <div className="tree-branches">
            {node.children.map((branch, i) => (
              <div className="tree-branch" key={i}>
                <div className="tree-branch-label">
                  {branch.answer.label}
                  {branch.answer.initial_facts?.length > 0 && (
                    <span className="branch-facts-badge">{branch.answer.initial_facts.length}</span>
                  )}
                </div>
                <div className="tree-connector" />
                {branch.childNode === null ? (
                  <div className="tree-terminal">診断開始</div>
                ) : (
                  <TreeNode node={branch.childNode} questionnaire={questionnaire} onEdit={onEdit} onDelete={onDelete} onSetStart={onSetStart} />
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function QuestionnaireAdminPage({ onBack }) {
  const [questionnaire, setQuestionnaire] = useState(null);
  const [availableFacts, setAvailableFacts] = useState([]);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);
  const [formData, setFormData] = useState({ id: '', text: '', answers: [] });
  const fileInputRef = React.useRef(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [qRes, cRes] = await Promise.all([
        fetch(`${API_BASE}/api/questionnaire`),
        fetch(`${API_BASE}/api/conditions`)
      ]);
      setQuestionnaire(await qRes.json());
      const cData = await cRes.json();
      setAvailableFacts(cData.conditions?.map(c => c.text) || []);
    } catch (error) {
      setMessage({ type: 'error', text: 'データの取得に失敗しました' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedQuestion(null);
    setIsEditing(true);
    setFormData({
      id: `q${Date.now()}`,
      text: '',
      answers: [
        { value: 'answer_0', label: 'はい', next_question: null, initial_facts: [] },
        { value: 'answer_1', label: 'いいえ', next_question: null, initial_facts: [] }
      ]
    });
  };

  const handleEdit = (question) => {
    setSelectedQuestion(question);
    setIsEditing(true);
    setFormData({
      id: question.id,
      text: question.text,
      answers: question.answers.map(a => ({ ...a, initial_facts: a.initial_facts || [] }))
    });
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const isNew = !selectedQuestion;
      const url = isNew
        ? `${API_BASE}/api/questionnaire/question`
        : `${API_BASE}/api/questionnaire/question/${selectedQuestion.id}`;
      const body = isNew ? formData : { text: formData.text, answers: formData.answers };

      const response = await fetch(url, {
        method: isNew ? 'POST' : 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (response.ok) {
        setIsEditing(false);
        setMessage({ type: 'success', text: '保存しました' });
        fetchData();
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || '保存に失敗しました' });
      }
    } catch {
      setMessage({ type: 'error', text: '保存に失敗しました' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (questionId) => {
    if (!window.confirm('この質問を削除しますか？')) return;
    try {
      const response = await fetch(`${API_BASE}/api/questionnaire/question/${questionId}`, { method: 'DELETE' });
      if (response.ok) {
        setMessage({ type: 'success', text: '削除しました' });
        fetchData();
      } else {
        setMessage({ type: 'error', text: '削除に失敗しました' });
      }
    } catch {
      setMessage({ type: 'error', text: '削除に失敗しました' });
    }
  };

  const handleSetStart = async (questionId) => {
    try {
      const response = await fetch(`${API_BASE}/api/questionnaire/start/${questionId}`, { method: 'PUT' });
      if (response.ok) {
        setMessage({ type: 'success', text: '開始質問を設定しました' });
        fetchData();
      }
    } catch {
      setMessage({ type: 'error', text: '設定に失敗しました' });
    }
  };

  const handleImport = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
      const response = await fetch(`${API_BASE}/api/questionnaire/import`, { method: 'POST', body: fd });
      const data = await response.json();
      if (data.status === 'imported') {
        setMessage({ type: 'success', text: `${data.count}件インポートしました` });
        fetchData();
      } else {
        setMessage({ type: 'error', text: data.errors?.join(', ') || 'インポートに失敗しました' });
      }
    } catch {
      setMessage({ type: 'error', text: 'インポートに失敗しました' });
    }
    event.target.value = '';
  };

  const updateFormAnswers = (newAnswers) => setFormData({ ...formData, answers: newAnswers });

  const addAnswer = () => {
    updateFormAnswers([...formData.answers, { value: `answer_${formData.answers.length}`, label: '', next_question: null, initial_facts: [] }]);
  };

  const removeAnswer = (index) => {
    updateFormAnswers(formData.answers.filter((_, i) => i !== index));
  };

  const updateAnswer = (index, field, value) => {
    const newAnswers = [...formData.answers];
    newAnswers[index] = { ...newAnswers[index], [field]: value };
    updateFormAnswers(newAnswers);
  };

  const addInitialFact = (answerIndex) => {
    const newAnswers = [...formData.answers];
    newAnswers[answerIndex].initial_facts = [...newAnswers[answerIndex].initial_facts, { fact_name: '', value: true }];
    updateFormAnswers(newAnswers);
  };

  const removeInitialFact = (answerIndex, factIndex) => {
    const newAnswers = [...formData.answers];
    newAnswers[answerIndex].initial_facts = newAnswers[answerIndex].initial_facts.filter((_, i) => i !== factIndex);
    updateFormAnswers(newAnswers);
  };

  const updateInitialFact = (answerIndex, factIndex, field, value) => {
    const newAnswers = [...formData.answers];
    newAnswers[answerIndex].initial_facts[factIndex] = { ...newAnswers[answerIndex].initial_facts[factIndex], [field]: value };
    updateFormAnswers(newAnswers);
  };

  const treeData = useMemo(() => {
    if (!questionnaire?.questions?.length) return null;

    const questionMap = new Map(questionnaire.questions.map(q => [q.id, q]));
    const visited = new Set();

    const buildNode = (questionId) => {
      if (!questionId) return null;
      if (visited.has(questionId)) return { type: 'ref', id: questionId };
      if (!questionMap.has(questionId)) return { type: 'missing', id: questionId };

      visited.add(questionId);
      const question = questionMap.get(questionId);
      return {
        type: 'node',
        question,
        children: question.answers.map(answer => ({ answer, childNode: buildNode(answer.next_question) }))
      };
    };

    return {
      root: buildNode(questionnaire.start_question),
      orphans: questionnaire.questions.filter(q => !visited.has(q.id))
    };
  }, [questionnaire]);

  if (loading && !questionnaire) {
    return <div className="admin-page"><p>読み込み中...</p></div>;
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h2>問診票管理</h2>
        <div className="admin-actions">
          <button className="action-button" onClick={onBack}>← 戻る</button>
          <button className="action-button" onClick={() => window.location.href = `${API_BASE}/api/questionnaire/export`}>エクスポート</button>
          <input type="file" ref={fileInputRef} accept=".csv" onChange={handleImport} style={{ display: 'none' }} />
          <button className="action-button" onClick={() => fileInputRef.current?.click()}>インポート</button>
          <button className="action-button primary" onClick={handleCreate}>+ 新規質問</button>
        </div>
      </div>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
          <button onClick={() => setMessage(null)}>×</button>
        </div>
      )}

      <div className="questionnaire-tree-container">
        {treeData ? (
          <>
            <div className="questionnaire-tree">
              {treeData.root ? (
                <TreeNode node={treeData.root} questionnaire={questionnaire} onEdit={handleEdit} onDelete={handleDelete} onSetStart={handleSetStart} />
              ) : (
                <p className="tree-empty-message">開始質問が設定されていません</p>
              )}
            </div>
            {treeData.orphans.length > 0 && (
              <div className="tree-orphans-section">
                <h4>未接続の質問（{treeData.orphans.length}件）</h4>
                <div className="tree-orphans-grid">
                  {treeData.orphans.map(q => (
                    <div key={q.id} className="tree-orphan-card" onClick={() => handleEdit(q)}>
                      <div className="tree-card-text">{q.text}</div>
                      <div className="tree-card-actions" onClick={e => e.stopPropagation()}>
                        <button className="small-button" onClick={() => handleSetStart(q.id)}>開始</button>
                        <button className="small-button" onClick={() => handleEdit(q)}>編集</button>
                        <button className="small-button danger" onClick={() => handleDelete(q.id)}>削除</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <p className="tree-empty-message">問診票がまだ設定されていません</p>
        )}
      </div>

      {isEditing && (
        <div className="question-editor-overlay" onClick={() => setIsEditing(false)}>
          <div className="question-editor-modal" onClick={e => e.stopPropagation()}>
            <h3>{selectedQuestion ? '質問編集' : '新規質問作成'}</h3>

            <div className="form-group">
              <label>質問文</label>
              <textarea value={formData.text} onChange={(e) => setFormData({ ...formData, text: e.target.value })} rows="2" />
            </div>

            <div className="form-group">
              <div className="form-group-header">
                <label>回答選択肢</label>
                <button className="small-button" onClick={addAnswer}>+ 追加</button>
              </div>

              {formData.answers.map((answer, ai) => (
                <div key={ai} className="answer-editor">
                  <div className="answer-row">
                    <input type="text" placeholder="ラベル" value={answer.label} onChange={(e) => updateAnswer(ai, 'label', e.target.value)} />
                    <select value={answer.next_question || ''} onChange={(e) => updateAnswer(ai, 'next_question', e.target.value || null)}>
                      <option value="">→ 診断開始</option>
                      {questionnaire?.questions.filter(q => q.id !== formData.id).map(q => (
                        <option key={q.id} value={q.id}>{q.text.length > 25 ? q.text.substring(0, 25) + '...' : q.text}</option>
                      ))}
                    </select>
                    {formData.answers.length > 2 && (
                      <button className="small-button danger" onClick={() => removeAnswer(ai)}>×</button>
                    )}
                  </div>

                  <div className="facts-section">
                    <div className="facts-header">
                      <span>初期ファクト</span>
                      <button className="small-button" onClick={() => addInitialFact(ai)}>+</button>
                    </div>
                    {answer.initial_facts.map((fact, fi) => (
                      <div key={fi} className="fact-row">
                        <select value={fact.fact_name} onChange={(e) => updateInitialFact(ai, fi, 'fact_name', e.target.value)}>
                          <option value="">選択...</option>
                          {availableFacts.map(f => <option key={f} value={f}>{f}</option>)}
                        </select>
                        <select value={fact.value.toString()} onChange={(e) => updateInitialFact(ai, fi, 'value', e.target.value === 'true')}>
                          <option value="true">TRUE</option>
                          <option value="false">FALSE</option>
                        </select>
                        <button className="small-button danger" onClick={() => removeInitialFact(ai, fi)}>×</button>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="form-actions">
              <button className="action-button primary" onClick={handleSave} disabled={loading}>{loading ? '保存中...' : '保存'}</button>
              <button className="action-button" onClick={() => setIsEditing(false)}>キャンセル</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default QuestionnaireAdminPage;
