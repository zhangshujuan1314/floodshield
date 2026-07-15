import type { Metadata } from 'next';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import './globals.css';

export const metadata: Metadata = {
  title: '汛安管理后台',
  description: '汛安 - 社区与应急管理后台系统',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="app-layout">
          <Sidebar />
          <main className="app-main">
            <Header />
            <div className="app-content">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
