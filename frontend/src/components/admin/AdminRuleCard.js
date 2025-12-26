import React, { useState } from 'react';

function AdminRuleCard({ rule, index, isNew, totalRules, onSave, onCancel, onDelete, onMoveUp, onMoveDown }) {
  const initialVisaType = rule.visa_type || 'E';
  const [formData, setFormData] = useState({
    conditions: rule.conditions?.length ? rule.conditions : [''],
    action: rule.action || '',
    is_or_rule: rule.is_or_rule || false,
    visa_type: initialVisaType
  });
  const [hasChanges, setHasChanges] = useState(isNew);
  const originalAction = rule.action || '';

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
      rule_type: 'i'
    };
    if (!isNew && originalAction) {
      saveData.original_action = originalAction;
    }
    onSave(saveData);
    setHasChanges(false);
  };

  const handleCancel = () => {
    setFormData({
      conditions: rule.conditions?.length ? rule.conditions : [''],
      action: rule.action || '',
      is_or_rule: rule.is_or_rule || false,
      visa_type: rule.visa_type || 'E'
    });
    setHasChanges(false);
    if (isNew) onCancel();
  };

  return (
    <div className={`admin-rule-card ${hasChanges ? 'has-changes' : ''}`}>
      <div className="rule-card-main">
        {!isNew && (
          <div className="rule-move-buttons">
            <button className="rule-move-btn" onClick={onMoveUp} disabled={index === 0}>↑</button>
            <button className="rule-move-btn" onClick={onMoveDown} disabled={index === totalRules - 1}>↓</button>
          </div>
        )}

        <div className="rule-card-content">
          <div className="rule-card-header">
            <span className="rule-number">#{isNew ? 'NEW' : index + 1}</span>
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

        <div className="rule-action-buttons">
          <button className="delete-btn" onClick={isNew ? onCancel : onDelete}>{isNew ? '取消' : '削除'}</button>
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
