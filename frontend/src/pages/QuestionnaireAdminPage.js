import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';

function QuestionnaireAdminPage({ onBack }) {
  const [questionnaire, setQuestionnaire] = useState(null);
  const [availableFacts, setAvailableFacts] = useState([]);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);
  const fileInputRef = React.useRef(null);

  const [formData, setFormData] = useState({
    id: '',
    text: '',
    answers: []
  });

  useEffect(() => {
    fetchQuestionnaire();
    fetchAvailableFacts();
  }, []);

  const fetchQuestionnaire = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/questionnaire`);
      const data = await response.json();
      setQuestionnaire(data);
    } catch (error) {
      console.error('Error fetching questionnaire:', error);
      setMessage({ type: 'error', text: '問診票の取得に失敗しました' });
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableFacts = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/conditions`);
      const data = await response.json();
      setAvailableFacts(data.conditions?.map(c => c.text) || []);
    } catch (error) {
      console.error('Error fetching facts:', error);
    }
  };

  const handleCreate = () => {
    setSelectedQuestion(null);
    setIsEditing(true);
    setFormData({
      id: `q${Date.now()}`,
      text: '',
      answers: [
        { value: 'yes', label: 'はい', next_question: null, initial_facts: [] },
        { value: 'no', label: 'いいえ', next_question: null, initial_facts: [] }
      ]
    });
  };

  const handleEdit = (question) => {
    setSelectedQuestion(question);
    setIsEditing(true);
    setFormData({
      id: question.id,
      text: question.text,
      answers: question.answers.map(a => ({
        ...a,
        initial_facts: a.initial_facts || []
      }))
    });
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const method = selectedQuestion ? 'PUT' : 'POST';
      const url = selectedQuestion
        ? `${API_BASE}/api/questionnaire/question/${selectedQuestion.id}`
        : `${API_BASE}/api/questionnaire/question`;

      const body = selectedQuestion
        ? { text: formData.text, answers: formData.answers }
        : formData;

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (response.ok) {
        setIsEditing(false);
        setMessage({ type: 'success', text: '保存しました' });
        fetchQuestionnaire();
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || '保存に失敗しました' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '保存に失敗しました' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (questionId) => {
    if (!window.confirm('この質問を削除しますか？')) return;

    try {
      const response = await fetch(`${API_BASE}/api/questionnaire/question/${questionId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setMessage({ type: 'success', text: '削除しました' });
        fetchQuestionnaire();
      } else {
        setMessage({ type: 'error', text: '削除に失敗しました' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '削除に失敗しました' });
    }
  };

  const handleSetStart = async (questionId) => {
    try {
      const response = await fetch(`${API_BASE}/api/questionnaire/start/${questionId}`, {
        method: 'PUT'
      });

      if (response.ok) {
        setMessage({ type: 'success', text: '開始質問を設定しました' });
        fetchQuestionnaire();
      }
    } catch (error) {
      setMessage({ type: 'error', text: '設定に失敗しました' });
    }
  };

  const handleExport = async () => {
    window.location.href = `${API_BASE}/api/questionnaire/export`;
  };

  const handleImport = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/api/questionnaire/import`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      if (data.status === 'imported') {
        setMessage({ type: 'success', text: `${data.count}件インポートしました` });
        fetchQuestionnaire();
      } else {
        setMessage({ type: 'error', text: data.errors?.join(', ') || 'インポートに失敗しました' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'インポートに失敗しました' });
    }
    event.target.value = '';
  };

  // 回答管理
  const addAnswer = () => {
    setFormData({
      ...formData,
      answers: [...formData.answers, {
        value: `answer_${Date.now()}`,
        label: '',
        next_question: null,
        initial_facts: []
      }]
    });
  };

  const removeAnswer = (index) => {
    setFormData({
      ...formData,
      answers: formData.answers.filter((_, i) => i !== index)
    });
  };

  const updateAnswer = (index, field, value) => {
    const newAnswers = [...formData.answers];
    newAnswers[index] = { ...newAnswers[index], [field]: value };
    setFormData({ ...formData, answers: newAnswers });
  };

  const addInitialFact = (answerIndex) => {
    const newAnswers = [...formData.answers];
    newAnswers[answerIndex].initial_facts = [
      ...newAnswers[answerIndex].initial_facts,
      { fact_name: '', value: true }
    ];
    setFormData({ ...formData, answers: newAnswers });
  };

  const removeInitialFact = (answerIndex, factIndex) => {
    const newAnswers = [...formData.answers];
    newAnswers[answerIndex].initial_facts = newAnswers[answerIndex].initial_facts.filter((_, i) => i !== factIndex);
    setFormData({ ...formData, answers: newAnswers });
  };

  const updateInitialFact = (answerIndex, factIndex, field, value) => {
    const newAnswers = [...formData.answers];
    newAnswers[answerIndex].initial_facts[factIndex] = {
      ...newAnswers[answerIndex].initial_facts[factIndex],
      [field]: value
    };
    setFormData({ ...formData, answers: newAnswers });
  };

  if (loading && !questionnaire) {
    return <div className="admin-page"><p>読み込み中...</p></div>;
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h2>問診票管理</h2>
        <div className="admin-actions">
          <button className="action-button" onClick={onBack}>← 戻る</button>
          <button className="action-button" onClick={handleExport}>CSVエクスポート</button>
          <input
            type="file"
            ref={fileInputRef}
            accept=".csv"
            onChange={handleImport}
            style={{ display: 'none' }}
          />
          <button className="action-button" onClick={() => fileInputRef.current?.click()}>
            CSVインポート
          </button>
          <button className="action-button primary" onClick={handleCreate}>
            + 新規質問
          </button>
        </div>
      </div>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
          <button onClick={() => setMessage(null)}>×</button>
        </div>
      )}

      {!isEditing ? (
        <div className="questionnaire-list">
          {questionnaire && questionnaire.questions.length > 0 ? (
            <>
              <p className="start-question-info">
                開始質問: <strong>{questionnaire.start_question || '未設定'}</strong>
              </p>
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>質問文</th>
                    <th>回答数</th>
                    <th>初期ファクト</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {questionnaire.questions.map((q) => (
                    <tr key={q.id} className={q.id === questionnaire.start_question ? 'start-question' : ''}>
                      <td>
                        {q.id}
                        {q.id === questionnaire.start_question && <span className="badge">開始</span>}
                      </td>
                      <td>{q.text}</td>
                      <td>{q.answers.length}個</td>
                      <td>{q.answers.reduce((acc, a) => acc + (a.initial_facts?.length || 0), 0)}個</td>
                      <td>
                        {q.id !== questionnaire.start_question && (
                          <button className="small-button" onClick={() => handleSetStart(q.id)}>開始に設定</button>
                        )}
                        <button className="small-button" onClick={() => handleEdit(q)}>編集</button>
                        <button className="small-button danger" onClick={() => handleDelete(q.id)}>削除</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <p>問診票がまだ設定されていません</p>
          )}
        </div>
      ) : (
        <div className="question-editor">
          <h3>{selectedQuestion ? '質問編集' : '新規質問作成'}</h3>

          <div className="form-group">
            <label>質問ID</label>
            <input
              type="text"
              value={formData.id}
              onChange={(e) => setFormData({ ...formData, id: e.target.value })}
              disabled={selectedQuestion !== null}
            />
          </div>

          <div className="form-group">
            <label>質問文</label>
            <textarea
              value={formData.text}
              onChange={(e) => setFormData({ ...formData, text: e.target.value })}
              rows="2"
            />
          </div>

          <div className="form-group">
            <label>回答選択肢</label>
            <button className="small-button" onClick={addAnswer}>+ 選択肢追加</button>

            {formData.answers.map((answer, answerIndex) => (
              <div key={answerIndex} className="answer-editor">
                <div className="answer-header">
                  <span>選択肢 {answerIndex + 1}</span>
                  {formData.answers.length > 2 && (
                    <button className="small-button danger" onClick={() => removeAnswer(answerIndex)}>削除</button>
                  )}
                </div>

                <div className="answer-fields">
                  <input
                    type="text"
                    placeholder="値 (yes/no)"
                    value={answer.value}
                    onChange={(e) => updateAnswer(answerIndex, 'value', e.target.value)}
                  />
                  <input
                    type="text"
                    placeholder="ラベル"
                    value={answer.label}
                    onChange={(e) => updateAnswer(answerIndex, 'label', e.target.value)}
                  />
                  <select
                    value={answer.next_question || ''}
                    onChange={(e) => updateAnswer(answerIndex, 'next_question', e.target.value || null)}
                  >
                    <option value="">終了（診断開始）</option>
                    {questionnaire?.questions.filter(q => q.id !== formData.id).map(q => (
                      <option key={q.id} value={q.id}>{q.id}: {q.text.substring(0, 20)}...</option>
                    ))}
                  </select>
                </div>

                <div className="initial-facts-section">
                  <label>初期ファクト</label>
                  <button className="small-button" onClick={() => addInitialFact(answerIndex)}>+ ファクト追加</button>

                  {answer.initial_facts.map((fact, factIndex) => (
                    <div key={factIndex} className="fact-row">
                      <select
                        value={fact.fact_name}
                        onChange={(e) => updateInitialFact(answerIndex, factIndex, 'fact_name', e.target.value)}
                      >
                        <option value="">選択...</option>
                        {availableFacts.map(f => (
                          <option key={f} value={f}>{f}</option>
                        ))}
                      </select>
                      <span>=</span>
                      <select
                        value={fact.value.toString()}
                        onChange={(e) => updateInitialFact(answerIndex, factIndex, 'value', e.target.value === 'true')}
                      >
                        <option value="true">TRUE</option>
                        <option value="false">FALSE</option>
                      </select>
                      <button className="small-button danger" onClick={() => removeInitialFact(answerIndex, factIndex)}>×</button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="form-actions">
            <button className="action-button primary" onClick={handleSave} disabled={loading}>
              {loading ? '保存中...' : '保存'}
            </button>
            <button className="action-button" onClick={() => setIsEditing(false)}>キャンセル</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default QuestionnaireAdminPage;
