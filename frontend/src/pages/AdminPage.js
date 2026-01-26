import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';
import AdminRuleCard from '../components/admin/AdminRuleCard';

function AdminPage({ onGoToConditions, onGoToQuestionnaire }) {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);
  const [insertPosition, setInsertPosition] = useState(null);
  const [newRuleAtEnd, setNewRuleAtEnd] = useState(false);
  const [importPreview, setImportPreview] = useState(null);
  const pageRef = React.useRef(null);
  const fileInputRef = React.useRef(null);

  const scrollToTop = () => {
    if (pageRef.current) {
      pageRef.current.scrollTop = 0;
    }
    window.scrollTo(0, 0);
  };

  const fetchRules = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/rules`);
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
  }, []);

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

  const handleExport = () => {
    window.location.href = `${API_BASE}/api/rules/export`;
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
      const response = await fetch(`${API_BASE}/api/rules/import`, {
        method: 'POST',
        body: formData
      });
      const data = await response.json();

      if (data.status === 'error') {
        setMessage({
          type: 'error',
          text: `インポートエラー:\n${data.errors.join('\n')}`
        });
      } else if (data.status === 'preview') {
        setImportPreview(data.rules);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'ファイルの読み込みに失敗しました' });
    }

    e.target.value = '';
  };

  const handleApplyImport = async () => {
    if (!importPreview) return;

    if (!window.confirm(`${importPreview.length}件のルールをインポートします。現在のルールは全て置き換えられます。よろしいですか？`)) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/rules/import/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rules: importPreview })
      });
      const data = await response.json();

      if (data.status === 'applied') {
        setMessage({ type: 'success', text: `${data.count}件のルールをインポートしました` });
        setImportPreview(null);
        fetchRules();
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'インポートの適用に失敗しました' });
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
    <div className="admin-page" ref={pageRef}>
      <div className="admin-header">
        <h2>ルール管理</h2>
        <div className="admin-actions">
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
          <button className="admin-button secondary" onClick={handleExport}>
            CSVエクスポート
          </button>
          <button className="admin-button secondary" onClick={handleImportClick}>
            CSVインポート
          </button>
          <button className="admin-button" onClick={onGoToConditions}>
            質問管理
          </button>
          <button className="admin-button" onClick={onGoToQuestionnaire}>
            問診票管理
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

      {importPreview && (
        <div className="import-preview-overlay">
          <div className="import-preview-modal">
            <h3>インポートプレビュー（{importPreview.length}件）</h3>
            <div className="import-preview-list">
              {importPreview.map((rule, idx) => (
                <div key={idx} className="import-preview-item">
                  <span className="preview-number">#{idx + 1}</span>
                  <span className="preview-operator">{rule.is_or_rule ? 'OR' : 'AND'}</span>
                  <span className="preview-action">{rule.action}</span>
                  {rule.is_goal_action && <span className="preview-goal">GOAL</span>}
                </div>
              ))}
            </div>
            <div className="import-preview-actions">
              <button className="admin-button" onClick={handleApplyImport}>
                インポート実行
              </button>
              <button className="admin-button secondary" onClick={() => setImportPreview(null)}>
                キャンセル
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="admin-rules-cards">
        {loading ? (
          <p className="loading-text">読み込み中...</p>
        ) : (
          <>
            {newRuleAtEnd && (
              <AdminRuleCard
                key="new-rule-end-top"
                rule={{ conditions: [''], action: '', is_or_rule: false }}
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
                rule={{ conditions: [''], action: '', is_or_rule: false }}
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
                      rule={{ conditions: [''], action: '', is_or_rule: false }}
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
                rule={{ conditions: [''], action: '', is_or_rule: false }}
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

export default AdminPage;
