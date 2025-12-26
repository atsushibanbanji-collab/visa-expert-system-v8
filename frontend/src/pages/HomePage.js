import React, { useState } from 'react';

function HomePage({ onStartConsultation }) {
  const [loading, setLoading] = useState(false);

  return (
    <div className="welcome-screen">
      <div className="welcome-content">
        <p className="subtitle">専門知識に基づくビザ選定支援</p>
        <div className="feature-list">
          <div className="feature-item">
            <span className="feature-icon">&#x2713;</span>
            <span>E・L・B・H-1B・J-1ビザを同時診断</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">&#x2713;</span>
            <span>バックワードチェイニングによる効率的な推論</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">&#x2713;</span>
            <span>推論過程のリアルタイム可視化</span>
          </div>
        </div>
        <button className="start-button" onClick={onStartConsultation} disabled={loading}>
          {loading ? '読み込み中...' : '診断を開始する'}
        </button>
      </div>
    </div>
  );
}

export default HomePage;
