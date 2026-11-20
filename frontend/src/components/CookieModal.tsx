import React, { useState } from 'react';
import { X, Key, Info, Trash2, Check } from 'lucide-react';

interface CookieModalProps {
  isOpen: boolean;
  onClose: () => void;
  hasCookie: boolean;
  maskedCookie: string;
  onSaveCookie: (cookie: string) => Promise<void>;
  onDeleteCookie: () => Promise<void>;
}

export const CookieModal: React.FC<CookieModalProps> = ({
  isOpen,
  onClose,
  hasCookie,
  maskedCookie,
  onSaveCookie,
  onDeleteCookie,
}) => {
  const [cookieInput, setCookieInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  if (!isOpen) return null;

  const handleSave = async () => {
    if (!cookieInput.trim()) return;
    setSaving(true);
    try {
      await onSaveCookie(cookieInput.trim());
      setCookieInput('');
      setMsg('Đã lưu cookie thành công!');
      setTimeout(() => setMsg(''), 2500);
    } catch {
      setMsg('Lỗi khi lưu cookie');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Bạn có chắc chắn muốn xóa cookie đã lưu?')) return;
    setSaving(true);
    try {
      await onDeleteCookie();
      setMsg('Đã xóa cookie thành công!');
      setTimeout(() => setMsg(''), 2500);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Key size={18} color="#f59e0b" />
            <h2 className="modal-title">Cấu hình Cookie phiên Reddit (reddit_session)</h2>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <div className="hint-box">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, marginBottom: '4px', color: 'var(--text-primary)' }}>
              <Info size={15} color="#38bdf8" />
              <span>Tại sao cần cookie `reddit_session`?</span>
            </div>
            Reddit gần đây đã bật cơ chế Login Wall trên <code>old.reddit.com</code> (chuyển hướng khách ẩn danh sang <code>login/?reason=lor2</code>). Cung cấp cookie phiên giúp script cào trực tiếp như một trình duyệt đã đăng nhập.
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Trạng thái hiện tại:
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span className={`status-dot ${hasCookie ? 'active' : 'inactive'}`} />
              <span style={{ fontWeight: 600 }}>
                {hasCookie ? `Đã cấu hình: ${maskedCookie}` : 'Chưa có cookie'}
              </span>
              {hasCookie && (
                <button
                  className="btn btn-outline-danger"
                  style={{ padding: '4px 10px', fontSize: '0.75rem', marginLeft: 'auto' }}
                  onClick={handleDelete}
                  disabled={saving}
                >
                  <Trash2 size={13} />
                  <span>Xóa cookie</span>
                </button>
              )}
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Dán giá trị cookie `reddit_session` mới:
            </label>
            <textarea
              rows={3}
              className="input-text"
              style={{ width: '100%', resize: 'vertical' }}
              placeholder="Nhập giá trị cookie reddit_session..."
              value={cookieInput}
              onChange={(e) => setCookieInput(e.target.value)}
            />
          </div>

          <div style={{ fontSize: '0.775rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
            <strong>Cách lấy cookie từ trình duyệt:</strong>
            <br />
            1. Mở Reddit trên Chrome / Edge, đăng nhập tài khoản.
            <br />
            2. Bấm <code>F12</code> -&gt; Vào tab <strong>Application</strong> (hoặc Storage) -&gt; <strong>Cookies</strong> -&gt; chọn <code>https://www.reddit.com</code>.
            <br />
            3. Tìm dòng có tên <code>reddit_session</code>, nhấp đúp và sao chép cột <strong>Value</strong> rồi dán vào đây.
          </div>

          {msg && (
            <div style={{ color: msg.includes('Lỗi') ? '#f87171' : '#34d399', fontSize: '0.85rem' }}>
              {msg}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
            <button className="btn btn-secondary" onClick={onClose}>
              Đóng
            </button>
            <button
              className="btn btn-primary"
              onClick={handleSave}
              disabled={saving || !cookieInput.trim()}
            >
              <Check size={15} />
              <span>{saving ? 'Đang lưu...' : 'Lưu cookie'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
