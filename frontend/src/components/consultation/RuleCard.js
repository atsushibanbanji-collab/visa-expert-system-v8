import React from 'react';

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
        <span className="rule-id">{rule.action}</span>
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

export default RuleCard;
