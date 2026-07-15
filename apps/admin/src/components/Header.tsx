'use client';

import { useEffect, useState } from 'react';
import { getStoredUser, getRoleLabel, logout } from '@/lib/auth';
import type { User } from '@/lib/types';

export default function Header() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const stored = getStoredUser();
    if (stored) {
      setUser(stored);
    } else {
      // Mock 模式下自动设置默认用户
      setUser({
        id: 'u-001',
        name: '张管理',
        role: 'admin',
        organizationId: 'org-gov',
        organizationName: '市防汛指挥部',
        lastLoginAt: new Date().toISOString(),
      });
    }
  }, []);

  const handleFontSizeToggle = () => {
    document.documentElement.classList.toggle('font-size-large');
  };

  return (
    <header className="header">
      <div className="header-left">
        <h1 className="header-title">社区与应急管理</h1>
      </div>
      <div className="header-right">
        <button
          className="header-btn font-size-btn"
          onClick={handleFontSizeToggle}
          title="切换大字号模式"
        >
          Aa
        </button>
        {user && (
          <div className="header-user">
            <span className="header-user-org">{user.organizationName}</span>
            <span className="header-user-name">{user.name}</span>
            <span className={`role-badge role-${user.role}`}>
              {getRoleLabel(user.role)}
            </span>
          </div>
        )}
        <button className="header-btn logout-btn" onClick={logout}>
          退出
        </button>
      </div>
    </header>
  );
}
