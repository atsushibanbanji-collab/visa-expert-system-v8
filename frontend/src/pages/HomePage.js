import React from 'react';

function HomePage({ onStartConsultation }) {
  return (
    <div className="welcome-screen">
      <button className="big-start-button" onClick={onStartConsultation}>
        診断を開始
      </button>
    </div>
  );
}

export default HomePage;
