'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavItem {
  href: string;
  label: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/', label: '态势总览', icon: '📊' },
  { href: '/reports', label: '报告队列', icon: '📋' },
  { href: '/map', label: '地图管理', icon: '🗺️' },
  { href: '/shelters', label: '避险场所', icon: '🏠' },
  { href: '/tasks', label: '任务通知', icon: '📢' },
  { href: '/audit', label: '审计日志', icon: '📝' },
  { href: '/settings', label: '设置', icon: '⚙️' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span className="sidebar-logo-icon">🌊</span>
        <span className="sidebar-logo-text">汛安管理后台</span>
      </div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-nav-icon">{item.icon}</span>
              <span className="sidebar-nav-label">{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="sidebar-footer">
        <span className="sidebar-version">v0.1.0</span>
      </div>
    </aside>
  );
}
