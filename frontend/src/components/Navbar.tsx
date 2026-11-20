import React from 'react';
import { Radio, Key, Download, Play, Square, RefreshCw } from 'lucide-react';

interface NavbarProps {
  hasCookie: boolean;
  maskedCookie: string;
  onOpenCookieModal: () => void;
  onStartScrape: () => void;
  onCancelScrape: () => void;
  isRunning: boolean;
  onRefresh: () => void;
  exportUrl: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  hasCookie,
  maskedCookie,
  onOpenCookieModal,
  onStartScrape,
  onCancelScrape,
  isRunning,
  onRefresh,
  exportUrl,
}) => {
  return (
    <header className="navbar">
      <div className="brand-section">
        <div className="brand-logo-badge">
          <Radio size={22} />
        </div>
        <div>
          <h1 className="brand-title">Reddit Trend Radar</h1>
          <p className="brand-subtitle">Bộ công cụ bóc tách tín hiệu xu hướng & chấm điểm Velocity</p>
        </div>
      </div>

      <div className="navbar-actions">
        {/* Nút Cookie Status */}
        <button
          className="cookie-indicator"
          onClick={onOpenCookieModal}
          title={hasCookie ? `Đã cấu hình cookie (${maskedCookie})` : 'Chưa cấu hình cookie Reddit session'}
        >
          <span className={`status-dot ${hasCookie ? 'active' : 'inactive'}`} />
          <Key size={14} />
          <span>{hasCookie ? 'Phiên Reddit: Đã kết nối' : 'Cấu hình Cookie'}</span>
        </button>

        {/* Nút Làm mới danh sách */}
        <button
          className="btn btn-secondary"
          onClick={onRefresh}
          disabled={isRunning}
          title="Tải lại dữ liệu bài viết mới nhất"
        >
          <RefreshCw size={15} />
          <span>Làm mới</span>
        </button>

        {/* Nút Xuất JSON */}
        <a
          href={exportUrl}
          className="btn btn-secondary"
          download="test_output.json"
          title="Tải file test_output.json về máy tính"
        >
          <Download size={15} />
          <span>Xuất JSON</span>
        </a>

        {/* Nút Bắt đầu / Hủy cào */}
        {isRunning ? (
          <button className="btn btn-outline-danger" onClick={onCancelScrape}>
            <Square size={15} />
            <span>Dừng cào</span>
          </button>
        ) : (
          <button className="btn btn-primary" onClick={onStartScrape}>
            <Play size={15} />
            <span>Cào dữ liệu ngay</span>
          </button>
        )}
      </div>
    </header>
  );
};
