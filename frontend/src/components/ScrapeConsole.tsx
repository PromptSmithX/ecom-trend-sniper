import React, { useState, useEffect, useRef } from 'react';
import type { ScrapeProgress } from '../types';
import { Terminal, ChevronUp, ChevronDown, CheckCircle2, AlertCircle } from 'lucide-react';

interface ScrapeConsoleProps {
  progress: ScrapeProgress;
}

export const ScrapeConsole: React.FC<ScrapeConsoleProps> = ({ progress }) => {
  const [isOpen, setIsOpen] = useState(true);
  const logsBoxRef = useRef<HTMLDivElement>(null);
  const logCount = progress.logs.length;

  // Tự động cuộn xuống dòng log mới nhất — CHỈ cuộn bên trong khung log,
  // không dùng scrollIntoView vì nó kéo cả trang web xuống cuối.
  useEffect(() => {
    const el = logsBoxRef.current;
    if (isOpen && el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [logCount, isOpen]);

  const percent = progress.total_requests > 0
    ? Math.round((progress.completed_requests / progress.total_requests) * 100)
    : 0;

  return (
    <div className="console-panel">
      <div className="console-header" onClick={() => setIsOpen(!isOpen)} style={{ cursor: 'pointer' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Terminal size={16} color="#38bdf8" />
          <span>Console Hoạt Động & Ghi Log Cào Dữ Liệu</span>

          {progress.is_running ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f59e0b', fontSize: '0.75rem' }}>
              <span className="status-dot active" />
              <span>{progress.current_step} ({progress.completed_requests}/{progress.total_requests})</span>
            </span>
          ) : (
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
              {progress.current_step || 'Đang chờ tác vụ...'}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {progress.total_requests > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '100px', height: '6px', background: 'var(--border-subtle)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${percent}%`, height: '100%', background: '#3b82f6', transition: 'width 0.3s' }} />
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }} className="tabular-nums">
                {percent}%
              </span>
            </div>
          )}

          <button style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            {isOpen ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="console-logs" ref={logsBoxRef}>
          {progress.logs.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', padding: '12px 0' }}>
              Chưa có nhật ký hoạt động nào. Hãy bấm "Cào dữ liệu ngay" để bắt đầu phiên mới.
            </div>
          ) : (
            progress.logs.map((log, index) => (
              <div key={index} className="log-line">
                <span className="log-ts">[{log.timestamp}]</span>
                <span className={`log-msg ${log.level}`}>
                  {log.level === 'error' && <AlertCircle size={12} style={{ display: 'inline', marginRight: '4px' }} />}
                  {log.level === 'success' && <CheckCircle2 size={12} style={{ display: 'inline', marginRight: '4px' }} />}
                  {log.message}
                </span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
