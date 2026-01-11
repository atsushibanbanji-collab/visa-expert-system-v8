import React from 'react';

function RuleCard({ rule, currentQuestion }) {
  const getStatusClass = (status) => {
    switch (status) {
      case 'fired': return 'rule-fired';
      case 'blocked': return 'rule-blocked';
      case 'uncertain': return 'rule-uncertain';
      case 'evaluating': return 'rule-evaluating';
      default: return 'rule-pending';
    }
  };

  const getConditionClass = (condition, isCurrent) => {
    let classes = 'condition-item';
    switch (condition.status) {
      case 'true': classes += ' condition-true'; break;
      case 'false': classes += ' condition-false'; break;
      case 'unknown': classes += ' condition-unknown'; break;
      default: classes += ' condition-unchecked';
    }
    if (condition.is_derived) classes += ' condition-derived';
    if (isCurrent) classes += ' condition-current';
    return classes;
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'fired': return '発火';
      case 'blocked': return '不可';
      case 'uncertain': return '不明';
      case 'evaluating': return '評価中';
      default: return '待機';
    }
  };

  return (
    <div className={`rule-card ${getStatusClass(rule.status)}`}>
      <div className="rule-card-header">
        <span className="rule-number">#{rule.index + 1}</span>
        <span className="rule-visa-badge">{rule.visa_type}</span>
        <span className="rule-operator-badge">{rule.operator}</span>
        <span className={`rule-status-badge ${rule.status}`}>
          {getStatusLabel(rule.status)}
        </span>
      </div>

      <div className="rule-card-body">
        <div className="rule-card-conclusion">
          <span className="label">THEN:</span>
          <span className={`conclusion-value ${rule.status === 'fired' ? 'conclusion-fired' : ''}`}>
            {rule.action}
          </span>
        </div>
        <div className="rule-card-conditions">
          <span className="label">IF:</span>
          <div className="conditions-list">
            {rule.conditions.map((cond, idx) => {
              const isCurrent = cond.text === currentQuestion;
              return (
                <React.Fragment key={idx}>
                  <span
                    className={getConditionClass(cond, isCurrent)}
                    data-current-condition={isCurrent ? 'true' : undefined}
                  >
                    {cond.is_derived && <span className="derived-marker">&#x25C6;</span>}
                    {cond.text}
                  </span>
                  {idx < rule.conditions.length - 1 && (
                    <span className="condition-operator">{rule.operator}</span>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default RuleCard;
