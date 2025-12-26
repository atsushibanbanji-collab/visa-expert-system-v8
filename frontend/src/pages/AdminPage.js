import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';
import AdminRuleCard from '../components/admin/AdminRuleCard';
import OrganizeModal from '../components/admin/OrganizeModal';

function AdminPage() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterVisaType, setFilterVisaType] = useState('');
  const [message, setMessage] = useState(null);
  const [showNewRuleForm, setShowNewRuleForm] = useState(false);
  const [showOrganizeModal, setShowOrganizeModal] = useState(false);

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
      const url = `${API_BASE}/api/rules`;
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ruleData)
      });

      if (response.ok) {
        setShowNewRuleForm(false);
        fetchRules();

        try {
          const validationResponse = await fetch(`${API_BASE}/api/validation/check`);
          const validationData = await validationResponse.json();
          if (validationData.status === 'ok') {
            setMessage({ type: 'success', text: isNew ? 'ルールを作成しました' : '保存しました' });
          } else {
            const issueTexts = validationData.issues.map(i => `・${i.message}`).join('\n');
            setMessage({
              type: 'warning',
              text: `${isNew ? '作成' : '保存'}しました（警告: ${validationData.issues.length}件）\n${issueTexts}`
            });
          }
        } catch (validationError) {
          setMessage({ type: 'success', text: isNew ? 'ルールを作成しました' : '保存しました' });
        }
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || '保存に失敗しました' });
      }
    } catch (error) {
      console.error('Error saving rule:', error);
      setMessage({ type: 'error', text: '保存に失敗しました' });
    }
  };

  const handleDeleteRule = async (action) => {
    if (!window.confirm(`このルールを削除しますか？`)) return;

    try {
      const response = await fetch(`${API_BASE}/api/rules/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });
      if (response.ok) {
        fetchRules();

        try {
          const validationResponse = await fetch(`${API_BASE}/api/validation/check`);
          const validationData = await validationResponse.json();
          if (validationData.status === 'ok') {
            setMessage({ type: 'success', text: 'ルールを削除しました' });
          } else {
            const issueTexts = validationData.issues.map(i => `・${i.message}`).join('\n');
            setMessage({
              type: 'warning',
              text: `削除しました（警告: ${validationData.issues.length}件）\n${issueTexts}`
            });
          }
        } catch (validationError) {
          setMessage({ type: 'success', text: 'ルールを削除しました' });
        }
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
        const issueTexts = data.issues.map(i => `・${i.message}`).join('\n');
        setMessage({
          type: 'warning',
          text: `整合性チェック: ${data.issues.length}件の問題\n${issueTexts}`
        });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '整合性チェックに失敗しました' });
    }
  };

  const handleAutoOrganize = async (mode) => {
    setShowOrganizeModal(false);

    try {
      const response = await fetch(`${API_BASE}/api/rules/auto-organize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });
      if (response.ok) {
        const modeText = mode === 'dependency' ? '依存関係順' : 'action名順';
        setMessage({ type: 'success', text: `ルールを${modeText}で整理しました` });
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
        body: JSON.stringify({ actions: newRules.map(r => r.action) })
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
          <button className="admin-button secondary" onClick={() => setShowOrganizeModal(true)}>
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

      {showOrganizeModal && (
        <OrganizeModal
          onSelect={handleAutoOrganize}
          onClose={() => setShowOrganizeModal(false)}
        />
      )}

      {showNewRuleForm && (
        <AdminRuleCard
          rule={{ conditions: [''], action: '', is_or_rule: false, visa_type: 'E' }}
          index={-1}
          isNew={true}
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
              key={rule.action}
              rule={rule}
              index={index}
              isNew={false}
              totalRules={rules.length}
              onSave={(data) => handleSaveRule(data, false)}
              onDelete={() => handleDeleteRule(rule.action)}
              onMoveUp={() => moveRule(index, -1)}
              onMoveDown={() => moveRule(index, 1)}
            />
          ))
        )}
      </div>
    </div>
  );
}

export default AdminPage;
