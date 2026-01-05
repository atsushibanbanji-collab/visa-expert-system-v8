import React from 'react';

// 条件を再帰的に表示するコンポーネント
function ConditionTree({ condition }) {
  if (!condition) return null;

  const hasSubConditions = condition.sub_conditions && condition.sub_conditions.length > 0;

  if (!hasSubConditions) {
    return (
      <li className="condition-leaf">
        {condition.text}
      </li>
    );
  }

  const operatorLabel = condition.operator === 'OR'
    ? '以下のいずれかを満たす必要があります'
    : '以下のすべてを満たす必要があります';
  const operatorClass = condition.operator === 'OR' ? 'operator-or' : 'operator-and';

  return (
    <li className="condition-branch">
      <div className={`condition-group ${operatorClass}`}>
        <span className={`operator-badge ${operatorClass}`}>{condition.operator}</span>
        <span className="operator-label">{operatorLabel}</span>
      </div>
      <ul className="sub-conditions">
        {condition.sub_conditions.map((sub, i) => (
          <ConditionTree key={i} condition={sub} />
        ))}
      </ul>
    </li>
  );
}

function DiagnosisResult({ result }) {
  if (!result) return null;

  return (
    <div className="diagnosis-result">
      <h2>診断結果</h2>
      {result.applicable_visas?.length > 0 && (
        <div className="result-section applicable">
          <h3>&#x2713; 申請可能なビザ</h3>
          <ul>
            {result.applicable_visas.map((visa, index) => (
              <li key={index} className="result-item applicable-visa">
                <span className={`visa-badge visa-${visa.type.replace('-', '')}`}>{visa.type}</span>
                <span className="visa-name">{visa.visa}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {result.conditional_visas?.length > 0 && (
        <div className="result-section conditional">
          <h3>&#x26A0; 条件付きで申請可能なビザ</h3>
          <p className="conditional-note">以下の条件を確認してください</p>
          <ul>
            {result.conditional_visas.map((visa, index) => (
              <li key={index} className="result-item conditional-visa">
                <span className={`visa-badge visa-${visa.type.replace('-', '')}`}>{visa.type}</span>
                <span className="visa-name">{visa.visa}</span>
                <div className="unknown-conditions">
                  <span className="unknown-conditions-title">確認が必要な条件:</span>
                  <ul className="condition-tree">
                    {visa.unknown_conditions.map((cond, i) => (
                      <ConditionTree key={i} condition={cond} />
                    ))}
                  </ul>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
      {(!result.applicable_visas || result.applicable_visas.length === 0) &&
       (!result.conditional_visas || result.conditional_visas.length === 0) && (
        <div className="result-section no-visa">
          <h3>該当するビザがありません</h3>
          <p>入力された条件では、申請可能なビザタイプが見つかりませんでした。</p>
        </div>
      )}
    </div>
  );
}

export default DiagnosisResult;
