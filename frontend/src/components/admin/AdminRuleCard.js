import React, { useState } from 'react';

function AdminRuleCard({ rule, index, isNew, totalRules, onSave, onCancel, onDelete, onMoveUp, onMoveDown }) {
  const [formData, setFormData] = useState({
    conditions: rule.conditions?.length ? rule.conditions : [''],
    action: rule.action || '',
    is_or_rule: rule.is_or_rule || false,
    is_goal_action: rule.is_goal_action || false
  });
  const [hasChanges, setHasChanges] = useState(isNew);

  const updateField = (field, value) => {
    setFormData({ ...formData, [field]: value });
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
    if (cleanedConditions.length === 0 || !formData.action) {
      alert('条件と結論は必須です');
      return;
    }
    const saveData = {
      ...formData,
      conditions: cleanedConditions,
      rule_type: 'i',
      is_goal_action: formData.is_goal_action
    };
    if (!isNew) {
      saveData.index = index;
    }
    onSave(saveData);
    setHasChanges(false);
  };

  const handleCancel = () => {
    setFormData({
      conditions: rule.conditions?.length ? rule.conditions : [''],
      action: rule.action || '',
      is_or_rule: rule.is_or_rule || false,
      is_goal_action: rule.is_goal_action || false
    });
    setHasChanges(false);
    if (isNew) onCancel();
  };

  return (
    <div className={`admin-rule-card ${hasChanges ? 'has-changes' : ''}`}>
      <div className="rule-card-main">
        <div className="rule-card-content">
          <div className="rule-card-header">
            {!isNew && (
              <>
                <button className="rule-move-btn" onClick={onMoveUp} disabled={index === 0}>↑</button>
                <button className="rule-move-btn" onClick={onMoveDown} disabled={index === totalRules - 1}>↓</button>
              </>
            )}
            <span className="rule-number">#{isNew ? 'NEW' : index + 1}</span>
            <select className="rule-type-select" value={formData.is_or_rule ? 'or' : 'and'} onChange={(e) => updateField('is_or_rule', e.target.value === 'or')}>
              <option value="and">AND</option>
              <option value="or">OR</option>
            </select>
            <label className="goal-action-checkbox">
              <input
                type="checkbox"
                checked={formData.is_goal_action}
                onChange={(e) => updateField('is_goal_action', e.target.checked)}
              />
              ゴール
            </label>
            <button className="delete-btn" onClick={isNew ? onCancel : onDelete}>{isNew ? '取消' : '削除'}</button>
          </div>

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
      </div>

      {hasChanges && (
        <div className="rule-card-actions">
          <button className="save-btn" onClick={handleSave}>保存</button>
          <button className="cancel-btn" onClick={handleCancel}>元に戻す</button>
        </div>
      )}
    </div>
  );
}

export default AdminRuleCard;
