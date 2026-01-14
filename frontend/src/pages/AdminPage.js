import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';
import { useVisaTypes } from '../context/VisaTypeContext';
import AdminRuleCard from '../components/admin/AdminRuleCard';

function AdminPage() {
  const { visaTypes, visaTypeCodes, reloadVisaTypes } = useVisaTypes();
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterVisaType, setFilterVisaType] = useState('');
  const [message, setMessage] = useState(null);
  const [insertPosition, setInsertPosition] = useState(null);
  const [newRuleAtEnd, setNewRuleAtEnd] = useState(false);
  const pageRef = React.useRef(null);

  // ビザタイプ管理用state
  const [visaTypeExpanded, setVisaTypeExpanded] = useState(false);
  const [visaTypeEdits, setVisaTypeEdits] = useState({});
  const [newVisaType, setNewVisaType] = useState(null);

  // visaTypesが変更されたら編集状態を初期化
  useEffect(() => {
    const edits = {};
    visaTypes.forEach(vt => {
      edits[vt.code] = { code: vt.code };
    });
    setVisaTypeEdits(edits);
  }, [visaTypes]);

  const scrollToTop = () => {
    if (pageRef.current) {
      pageRef.current.scrollTop = 0;
    }
    window.scrollTo(0, 0);
  };

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
        setInsertPosition(null);
        setNewRuleAtEnd(false);
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
        let errorText = '保存に失敗しました';
        if (typeof error.detail === 'string') {
          errorText = error.detail;
        } else if (Array.isArray(error.detail)) {
          errorText = error.detail.map(e => e.msg || JSON.stringify(e)).join(', ');
        }
        setMessage({ type: 'error', text: errorText });
      }
    } catch (error) {
      console.error('Error saving rule:', error);
      setMessage({ type: 'error', text: '保存に失敗しました' });
    }
  };

  const handleDeleteRule = async (index) => {
    if (!window.confirm('このルールを削除しますか？')) return;

    try {
      const response = await fetch(`${API_BASE}/api/rules/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index })
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

  // ビザタイプ管理関数
  const handleAddVisaType = async (visaTypeData) => {
    try {
      const response = await fetch(`${API_BASE}/api/visa-types`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(visaTypeData)
      });
      if (response.ok) {
        reloadVisaTypes();
        setNewVisaType(null);
        setMessage({ type: 'success', text: 'ビザタイプを追加しました' });
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || '追加に失敗しました' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '追加に失敗しました' });
    }
  };

  const handleUpdateVisaType = async (originalCode) => {
    const editData = visaTypeEdits[originalCode];
    if (!editData || !editData.code.trim()) {
      setMessage({ type: 'error', text: 'コードは必須です' });
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/visa-types/${originalCode}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: editData.code })
      });
      if (response.ok) {
        reloadVisaTypes();
        setMessage({ type: 'success', text: 'ビザタイプを更新しました' });
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || '更新に失敗しました' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '更新に失敗しました' });
    }
  };

  const handleDeleteVisaType = async (code) => {
    if (!window.confirm(`ビザタイプ「${code}」を削除しますか？\n※このビザタイプを使用しているルールがある場合、問題が発生する可能性があります。`)) return;
    try {
      const response = await fetch(`${API_BASE}/api/visa-types/${code}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        reloadVisaTypes();
        setMessage({ type: 'success', text: 'ビザタイプを削除しました' });
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || '削除に失敗しました' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '削除に失敗しました' });
    }
  };

  const moveVisaType = async (index, direction) => {
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= visaTypes.length) return;

    // orderを入れ替えて更新
    const currentVt = visaTypes[index];
    const targetVt = visaTypes[newIndex];

    try {
      await Promise.all([
        fetch(`${API_BASE}/api/visa-types/${currentVt.code}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...currentVt, order: targetVt.order })
        }),
        fetch(`${API_BASE}/api/visa-types/${targetVt.code}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...targetVt, order: currentVt.order })
        })
      ]);
      reloadVisaTypes();
    } catch (error) {
      console.error('Error moving visa type:', error);
      setMessage({ type: 'error', text: '順序の変更に失敗しました' });
    }
  };

  const handleVisaTypeEditChange = (originalCode, field, value) => {
    setVisaTypeEdits(prev => ({
      ...prev,
      [originalCode]: { ...prev[originalCode], [field]: value }
    }));
  };

  return (
    <div className="admin-page" ref={pageRef}>
      <div className="admin-header">
        <h2>ルール管理</h2>
        <div className="admin-actions">
          <select value={filterVisaType} onChange={(e) => setFilterVisaType(e.target.value)}>
            <option value="">全てのビザタイプ</option>
            {visaTypeCodes.map(vt => (
              <option key={vt} value={vt}>{vt}ビザ</option>
            ))}
          </select>
          <button className="admin-button" onClick={() => {
            setNewRuleAtEnd(true);
            setInsertPosition(null);
            scrollToTop();
          }}>
            新規ルール（末尾）
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

      {/* ビザタイプ管理セクション */}
      <div className="visa-type-section">
        <div className="visa-type-header" onClick={() => setVisaTypeExpanded(!visaTypeExpanded)}>
          <span className="expand-icon">{visaTypeExpanded ? '▼' : '▶'}</span>
          <h3>ビザタイプ管理</h3>
          <span className="visa-type-count">{visaTypes.length}件</span>
        </div>
        {visaTypeExpanded && (
          <div className="visa-type-content">
            <div className="visa-type-list">
              {visaTypes.map((vt, index) => (
                <div key={vt.code} className="visa-type-item">
                  <div className="visa-type-move-buttons">
                    <button
                      className="move-btn"
                      onClick={() => moveVisaType(index, -1)}
                      disabled={index === 0}
                      title="上へ移動"
                    >↑</button>
                    <button
                      className="move-btn"
                      onClick={() => moveVisaType(index, 1)}
                      disabled={index === visaTypes.length - 1}
                      title="下へ移動"
                    >↓</button>
                  </div>
                  <div className="visa-type-fields">
                    <input
                      type="text"
                      className="visa-type-code-input"
                      value={visaTypeEdits[vt.code]?.code ?? vt.code}
                      onChange={(e) => handleVisaTypeEditChange(vt.code, 'code', e.target.value)}
                      onBlur={() => {
                        const edit = visaTypeEdits[vt.code];
                        if (edit && edit.code !== vt.code) {
                          handleUpdateVisaType(vt.code);
                        }
                      }}
                      onKeyDown={(e) => { if (e.key === 'Enter') e.target.blur(); }}
                      placeholder="コード"
                    />

                  </div>
                  <button className="delete-btn" onClick={() => handleDeleteVisaType(vt.code)}>削除</button>
                </div>
              ))}
            </div>
            {newVisaType ? (
              <VisaTypeForm
                initial={newVisaType}
                onSave={handleAddVisaType}
                onCancel={() => setNewVisaType(null)}
              />
            ) : (
              <button className="add-visa-type-btn" onClick={() => setNewVisaType({ code: '', name: '', order: visaTypes.length })}>
                + ビザタイプを追加
              </button>
            )}
          </div>
        )}
      </div>

      <div className="admin-rules-cards">
        {loading ? (
          <p className="loading-text">読み込み中...</p>
        ) : (
          <>
            {newRuleAtEnd && (
              <AdminRuleCard
                key="new-rule-end-top"
                rule={{ conditions: [''], action: '', is_or_rule: false, visa_type: visaTypeCodes[0] || 'E' }}
                index={-1}
                isNew={true}
                totalRules={rules.length}
                onSave={(data) => handleSaveRule({ ...data, insert_after: rules.length }, true)}
                onCancel={() => setNewRuleAtEnd(false)}
                onDelete={() => {}}
              />
            )}

            {!newRuleAtEnd && (insertPosition === 0 ? (
              <AdminRuleCard
                key="new-rule-0"
                rule={{ conditions: [''], action: '', is_or_rule: false, visa_type: visaTypeCodes[0] || 'E' }}
                index={-1}
                isNew={true}
                totalRules={rules.length}
                onSave={(data) => handleSaveRule({ ...data, insert_after: 0 }, true)}
                onCancel={() => setInsertPosition(null)}
                onDelete={() => {}}
              />
            ) : (
              <button className="insert-rule-btn" onClick={() => setInsertPosition(0)}>
                ＋ 先頭に挿入
              </button>
            ))}

            {rules.map((rule, index) => (
              <React.Fragment key={rule.action}>
                <AdminRuleCard
                  rule={rule}
                  index={index}
                  isNew={false}
                  totalRules={rules.length}
                  onSave={(data) => handleSaveRule(data, false)}
                  onDelete={() => handleDeleteRule(index)}
                  onMoveUp={() => moveRule(index, -1)}
                  onMoveDown={() => moveRule(index, 1)}
                />

                {index < rules.length - 1 && (
                  insertPosition === index + 1 ? (
                    <AdminRuleCard
                      key={`new-rule-${index + 1}`}
                      rule={{ conditions: [''], action: '', is_or_rule: false, visa_type: visaTypeCodes[0] || 'E' }}
                      index={-1}
                      isNew={true}
                      totalRules={rules.length}
                      onSave={(data) => handleSaveRule({ ...data, insert_after: index + 1 }, true)}
                      onCancel={() => setInsertPosition(null)}
                      onDelete={() => {}}
                    />
                  ) : (
                    <button className="insert-rule-btn" onClick={() => setInsertPosition(index + 1)}>
                      ＋
                    </button>
                  )
                )}
              </React.Fragment>
            ))}

            {insertPosition === rules.length ? (
              <AdminRuleCard
                key="new-rule-end"
                rule={{ conditions: [''], action: '', is_or_rule: false, visa_type: visaTypeCodes[0] || 'E' }}
                index={-1}
                isNew={true}
                totalRules={rules.length}
                onSave={(data) => handleSaveRule({ ...data, insert_after: rules.length }, true)}
                onCancel={() => setInsertPosition(null)}
                onDelete={() => {}}
              />
            ) : (
              <button className="insert-rule-btn" onClick={() => setInsertPosition(rules.length)}>
                ＋ 末尾に追加
              </button>
            )}
          </>
        )}
      </div>

      <button className="scroll-to-top-btn" onClick={scrollToTop} title="一番上に戻る">
        ↑
      </button>
    </div>
  );
}

// 新規ビザタイプ追加フォーム
function VisaTypeForm({ initial, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    code: initial.code || '',
    order: initial.order ?? 0
  });

  const handleSubmit = () => {
    if (!formData.code.trim()) {
      alert('コードは必須です');
      return;
    }
    onSave(formData);
  };

  return (
    <div className="visa-type-form">
      <input
        type="text"
        value={formData.code}
        onChange={(e) => setFormData({ ...formData, code: e.target.value })}
        placeholder="コード"
        className="visa-type-code-input"
      />

      <div className="form-actions">
        <button className="save-btn" onClick={handleSubmit}>追加</button>
        <button className="cancel-btn" onClick={onCancel}>キャンセル</button>
      </div>
    </div>
  );
}

export default AdminPage;
