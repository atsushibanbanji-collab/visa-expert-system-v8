import React from 'react';

function OrganizeModal({ onSelect, onClose }) {
  const options = [
    { mode: 'dependency', title: '依存関係順', desc: 'ビザタイプ順 → 依存深度順（ゴール→中間→初期）' },
    { mode: 'action', title: 'action名順', desc: 'ビザタイプ順 → action名順（アルファベット順）' }
  ];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content organize-modal" onClick={e => e.stopPropagation()}>
        <h3>自動整理モードを選択</h3>
        <div className="organize-options">
          {options.map(opt => (
            <button key={opt.mode} className="organize-option" onClick={() => onSelect(opt.mode)}>
              <span className="option-title">{opt.title}</span>
              <span className="option-desc">{opt.desc}</span>
            </button>
          ))}
        </div>
        <button className="modal-cancel" onClick={onClose}>キャンセル</button>
      </div>
    </div>
  );
}

export default OrganizeModal;
