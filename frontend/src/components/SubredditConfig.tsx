import React, { useState } from 'react';
import { Layers, Plus, X, Sparkles } from 'lucide-react';
import { SUBREDDIT_PRESETS } from '../presets';

const sameSubs = (a: string[], b: string[]) => {
  if (a.length !== b.length) return false;
  const set = new Set(a.map((s) => s.toLowerCase()));
  return b.every((s) => set.has(s.toLowerCase()));
};

interface SubredditConfigProps {
  subreddits: string[];
  onSubredditsChange: (subs: string[]) => void;
  selectedCategories: string[];
  onCategoriesChange: (cats: string[]) => void;
  categories: { id: string; name: string; description: string }[];
}

export const SubredditConfig: React.FC<SubredditConfigProps> = ({
  subreddits,
  onSubredditsChange,
  selectedCategories,
  onCategoriesChange,
  categories,
}) => {
  const [newSub, setNewSub] = useState('');

  const handleAdd = () => {
    const clean = newSub.trim().replace(/^r\//, '');
    if (clean && !subreddits.includes(clean)) {
      onSubredditsChange([...subreddits, clean]);
      setNewSub('');
    }
  };

  const handleRemove = (sub: string) => {
    onSubredditsChange(subreddits.filter((s) => s !== sub));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  };

  // Preset THAY THẾ danh sách hiện tại để mỗi lần cào chỉ tập trung 1 mảng
  const applyPreset = (presetSubs: string[]) => {
    onSubredditsChange([...presetSubs]);
  };

  const toggleCategory = (catId: string) => {
    if (selectedCategories.includes(catId)) {
      if (selectedCategories.length > 1) {
        onCategoriesChange(selectedCategories.filter((c) => c !== catId));
      }
    } else {
      onCategoriesChange([...selectedCategories, catId]);
    }
  };

  return (
    <div className="config-panel">
      <div className="panel-header">
        <div className="panel-title">
          <Layers size={18} color="#38bdf8" />
          <span>Danh sách Subreddit theo dõi bắt trend ({subreddits.length})</span>
        </div>

        <div className="preset-pills">
          <Sparkles size={14} color="#f59e0b" />
          <span>Chọn mảng:</span>
          {SUBREDDIT_PRESETS.map((preset) => {
            const isActive = sameSubs(subreddits, preset.subs);
            return (
              <button
                key={preset.id}
                className={`preset-btn ${isActive ? 'active' : ''}`}
                aria-pressed={isActive}
                title={`${preset.title}\n(Thay toàn bộ danh sách bằng: ${preset.subs.map((s) => 'r/' + s).join(', ')})`}
                onClick={() => applyPreset(preset.subs)}
              >
                {preset.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Subreddit Tags */}
      <div className="tags-wrapper">
        {subreddits.map((sub) => (
          <span key={sub} className="sub-tag">
            <span>r/{sub}</span>
            <button
              className="sub-tag-remove"
              onClick={() => handleRemove(sub)}
              title={`Xóa r/${sub}`}
            >
              <X size={13} />
            </button>
          </span>
        ))}

        <div className="add-sub-input-group">
          <input
            type="text"
            className="input-text"
            placeholder="+ Thêm sub (vd: AmazonWTF)"
            value={newSub}
            onChange={(e) => setNewSub(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button className="btn btn-secondary" style={{ padding: '6px 12px' }} onClick={handleAdd}>
            <Plus size={14} />
            <span>Thêm</span>
          </button>
        </div>
      </div>

      {/* Category Checkboxes */}
      <div className="feed-categories-row">
        <span style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>Nguồn dữ liệu cào:</span>
        {categories.map((cat) => (
          <label key={cat.id} className="checkbox-label">
            <input
              type="checkbox"
              checked={selectedCategories.includes(cat.id)}
              onChange={() => toggleCategory(cat.id)}
            />
            <span>{cat.name}</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({cat.description})</span>
          </label>
        ))}
      </div>
    </div>
  );
};
