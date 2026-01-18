import React, { useState, useEffect, useRef } from 'react';
import { API_BASE } from '../config';

function ConditionsPage({ onBack }) {
  const [conditions, setConditions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);
  const [editingCondition, setEditingCondition] = useState(null);
  const [editNote, setEditNote] = useState('');
  const fileInputRef = useRef(null);

  const fetchConditions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/conditions`);
      const data = await response.json();
      setConditions(data.conditions || []);
    } catch (error) {
      console.error('Error fetching conditions:', error);
      setMessage({ type: 'error', text: '条件の取得に失敗しました' });
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchConditions();
  }, []);

  const handleEdit = (condition) => {
    setEditingCondition(condition.text);
    setEditNote(condition.note || '');
  };

  const handleSave = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/conditions/note`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          condition: editingCondition,
          note: editNote
        })
      });

      if (response.ok) {
        setMessage({ type: 'success', text: '保存しました' });
        setEditingCondition(null);
        fetchConditions();
      } else {
        setMessage({ type: 'error', text: '保存に失敗しました' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '保存に失敗しました' });
    }
  };

  const handleCancel = () => {
    setEditingCondition(null);
    setEditNote('');
  };

  const handleExport = () => {
    window.location.href = `${API_BASE}/api/conditions/export`;
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/api/conditions/import`, {
        method: 'POST',
        body: formData
      });
      const data = await response.json();

      if (data.status === 'error') {
        setMessage({
          type: 'error',
          text: `インポートエラー:\n${data.errors.join('\n')}`
        });
      } else {
        setMessage({ type: 'success', text: `${data.count}件の補足をインポートしました` });
        fetchConditions();
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'インポートに失敗しました' });
    }

    e.target.value = '';
  };

  const notesCount = conditions.filter(c => c.note).length;

  return (
    <div className="admin-page conditions-page">
      <div className="admin-header">
        <div className="header-left">
          <button className="admin-button secondary" onClick={onBack}>
            ← ルール管理に戻る
          </button>
          <h2>質問管理</h2>
          <span className="conditions-count">
            {conditions.length}件中 {notesCount}件に補足あり
          </span>
        </div>
        <div className="admin-actions">
          <button className="admin-button secondary" onClick={handleExport}>
            CSVエクスポート
          </button>
          <button className="admin-button secondary" onClick={handleImportClick}>
            CSVインポート
          </button>
          <input
            type="file"
            ref={fileInputRef}
            accept=".csv"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
        </div>
      </div>

      {message && (
        <div className={`admin-message ${message.type}`}>
          {message.text}
          <button onClick={() => setMessage(null)}>&times;</button>
        </div>
      )}

      <div className="conditions-list">
        {loading ? (
          <p className="loading-text">読み込み中...</p>
        ) : (
          conditions.map((condition, idx) => (
            <div key={idx} className={`condition-card ${condition.note ? 'has-note' : ''}`}>
              <div className="condition-text">{condition.text}</div>
              {editingCondition === condition.text ? (
                <div className="condition-edit">
                  <textarea
                    value={editNote}
                    onChange={(e) => setEditNote(e.target.value)}
                    placeholder="補足説明を入力..."
                    rows={2}
                  />
                  <div className="condition-edit-actions">
                    <button className="admin-button" onClick={handleSave}>保存</button>
                    <button className="admin-button secondary" onClick={handleCancel}>キャンセル</button>
                  </div>
                </div>
              ) : (
                <div className="condition-note-display">
                  {condition.note ? (
                    <p className="note-text">{condition.note}</p>
                  ) : (
                    <p className="note-empty">補足なし</p>
                  )}
                  <button className="edit-note-btn" onClick={() => handleEdit(condition)}>
                    {condition.note ? '編集' : '補足を追加'}
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default ConditionsPage;
