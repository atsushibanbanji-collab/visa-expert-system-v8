import React, { useState } from 'react';
import './App.css';
import './Admin.css';
import HomePage from './pages/HomePage';
import ConsultationPage from './pages/ConsultationPage';
import AdminPage from './pages/AdminPage';
import { VisaTypeProvider } from './context/VisaTypeContext';

function App() {
  const [currentPage, setCurrentPage] = useState('home');

  return (
    <VisaTypeProvider>
    <div className="app">
      <header className="header">
        <h1>ビザ選定エキスパートシステム</h1>
        <div className="header-actions">
          <button
            className={`header-button ${currentPage === 'home' ? 'active' : ''}`}
            onClick={() => setCurrentPage('home')}
          >
            ホーム
          </button>
          <button
            className={`header-button ${currentPage === 'admin' ? 'active' : ''}`}
            onClick={() => setCurrentPage('admin')}
          >
            ルール管理
          </button>
        </div>
      </header>

      {currentPage === 'home' && <HomePage onStartConsultation={() => setCurrentPage('consultation')} />}
      {currentPage === 'consultation' && <ConsultationPage onBack={() => setCurrentPage('home')} />}
      {currentPage === 'admin' && <AdminPage />}
    </div>
    </VisaTypeProvider>
  );
}

export default App;
