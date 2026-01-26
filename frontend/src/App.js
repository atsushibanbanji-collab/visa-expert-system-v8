import React, { useState } from 'react';
import './App.css';
import './Admin.css';
import HomePage from './pages/HomePage';
import ConsultationPage from './pages/ConsultationPage';
import AdminPage from './pages/AdminPage';
import ConditionsPage from './pages/ConditionsPage';
import QuestionnairePage from './pages/QuestionnairePage';
import QuestionnaireAdminPage from './pages/QuestionnaireAdminPage';

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [initialFacts, setInitialFacts] = useState([]);

  const handleQuestionnaireComplete = (facts) => {
    setInitialFacts(facts);
    setCurrentPage('consultation');
  };

  const handleSkipQuestionnaire = () => {
    setInitialFacts([]);
    setCurrentPage('consultation');
  };

  const handleBackToHome = () => {
    setInitialFacts([]);
    setCurrentPage('home');
  };

  return (
    <div className="app">
      <header className="header">
        <h1>ビザ選定エキスパートシステム</h1>
        <div className="header-actions">
          <button
            className={`header-button ${currentPage === 'home' || currentPage === 'questionnaire' || currentPage === 'consultation' ? 'active' : ''}`}
            onClick={() => setCurrentPage('home')}
          >
            診断
          </button>
          <button
            className={`header-button ${currentPage === 'admin' || currentPage === 'conditions' || currentPage === 'questionnaireAdmin' ? 'active' : ''}`}
            onClick={() => setCurrentPage('admin')}
          >
            管理
          </button>
        </div>
      </header>

      {currentPage === 'home' && <HomePage onStartConsultation={() => setCurrentPage('questionnaire')} />}
      {currentPage === 'questionnaire' && (
        <QuestionnairePage
          onComplete={handleQuestionnaireComplete}
          onSkip={handleSkipQuestionnaire}
        />
      )}
      {currentPage === 'consultation' && (
        <ConsultationPage
          onBack={handleBackToHome}
          initialFacts={initialFacts}
        />
      )}
      {currentPage === 'admin' && (
        <AdminPage
          onGoToConditions={() => setCurrentPage('conditions')}
          onGoToQuestionnaire={() => setCurrentPage('questionnaireAdmin')}
        />
      )}
      {currentPage === 'conditions' && <ConditionsPage onBack={() => setCurrentPage('admin')} />}
      {currentPage === 'questionnaireAdmin' && <QuestionnaireAdminPage onBack={() => setCurrentPage('admin')} />}
    </div>
  );
}

export default App;
