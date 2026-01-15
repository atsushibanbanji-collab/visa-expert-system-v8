import React from 'react';

function DiagnosisResult({ result, onGoBack, onRestart }) {
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
                <span className="visa-name">{visa.visa}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {result.conditional_visas?.length > 0 && (
        <div className="result-section conditional">
          <h3>&#x26A0; 条件付きで申請可能なビザ</h3>
          <ul>
            {result.conditional_visas.map((visa, index) => (
              <li key={index} className="result-item conditional-visa">
                <p className="conditional-description">
                  以下の条件が満たされれば申請ができます:
                </p>
                <p className="visa-name-conditional">{visa.visa}</p>
                <ul className="unknown-conditions-list">
                  {visa.unknown_conditions.map((cond, i) => (
                    <li key={i}>「{cond}」</li>
                  ))}
                </ul>
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
      <div className="result-actions">
        <button className="action-button go-back" onClick={onGoBack}>
          前の質問に戻る
        </button>
        <button className="action-button restart" onClick={onRestart}>
          最初から
        </button>
      </div>
    </div>
  );
}

export default DiagnosisResult;
