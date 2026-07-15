'use client';

import { useEffect, useState } from 'react';
import useSWR from 'swr';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import { fetchDashboard } from '@/lib/api';
import RiskBadge from '@/components/RiskBadge';
import DataFreshness from '@/components/DataFreshness';
import type { DashboardSummary } from '@/lib/types';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

export default function DashboardPage() {
  const { data, error, isLoading } = useSWR<DashboardSummary>(
    'dashboard',
    fetchDashboard,
    { refreshInterval: 30000 }
  );

  if (isLoading) {
    return <div className="empty-state"><div className="empty-state-icon">⏳</div><div className="empty-state-text">加载中...</div></div>;
  }

  if (error || !data) {
    return <div className="empty-state"><div className="empty-state-icon">❌</div><div className="empty-state-text">加载失败，请刷新重试</div></div>;
  }

  const criticalAreas = data.riskSnapshots.filter(r => r.riskLevel === 'critical').length;
  const highAreas = data.riskSnapshots.filter(r => r.riskLevel === 'high').length;

  return (
    <div>
      <h2 className="section-title">态势总览</h2>

      {/* 统计卡片 */}
      <div className="dashboard-grid">
        <div className="stat-card stat-critical">
          <div className="stat-card-icon">🔴</div>
          <div className="stat-card-info">
            <div className="stat-card-value">{criticalAreas}</div>
            <div className="stat-card-label">极高风险区域</div>
          </div>
        </div>
        <div className="stat-card stat-high">
          <div className="stat-card-icon">🔶</div>
          <div className="stat-card-info">
            <div className="stat-card-value">{highAreas}</div>
            <div className="stat-card-label">高危风险区域</div>
          </div>
        </div>
        <div className="stat-card stat-pending">
          <div className="stat-card-icon">📋</div>
          <div className="stat-card-info">
            <div className="stat-card-value">{data.pendingReportsCount}</div>
            <div className="stat-card-label">待核验报告</div>
          </div>
        </div>
        <div className="stat-card stat-task">
          <div className="stat-card-icon">📢</div>
          <div className="stat-card-info">
            <div className="stat-card-value">{data.activeTasksCount}</div>
            <div className="stat-card-label">进行中任务</div>
          </div>
        </div>
      </div>

      {/* 快速操作 */}
      <div className="quick-actions">
        <button className="quick-action-btn" onClick={() => window.location.href = '/reports'}>
          📋 处理报告队列
        </button>
        <button className="quick-action-btn" onClick={() => window.location.href = '/tasks'}>
          📢 创建新任务
        </button>
        <button className="quick-action-btn" onClick={() => window.location.href = '/map'}>
          🗺️ 查看地图
        </button>
        <button className="quick-action-btn" onClick={() => window.location.href = '/shelters'}>
          🏠 管理避险场所
        </button>
      </div>

      {/* 活跃预警 */}
      <div className="card mb-md">
        <div className="card-title">活跃预警</div>
        {data.activeAlerts.length === 0 ? (
          <div className="text-hint">暂无活跃预警</div>
        ) : (
          data.activeAlerts.map(alert => (
            <div key={alert.id} style={{
              padding: 'var(--spacing-sm) 0',
              borderBottom: '1px solid var(--color-border-light)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: 'var(--spacing-md)',
            }}>
              <RiskBadge level={alert.level} size="sm" />
              <div style={{ flex: 1 }}>
                <div className="font-bold">{alert.title}</div>
                <div className="text-secondary" style={{ fontSize: 'var(--font-size-sm)', marginTop: 4 }}>
                  {alert.content}
                </div>
                <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                  {alert.issuedBy} · {dayjs(alert.issuedAt).fromNow()}发布 · 有效至{dayjs(alert.expiresAt).format('HH:mm')}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 区域风险快照 */}
      <div className="card mb-md">
        <div className="card-title">区域风险快照</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 'var(--spacing-md)' }}>
          {data.riskSnapshots.map(snapshot => (
            <div key={snapshot.areaId} style={{
              border: '1px solid var(--color-border-light)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--spacing-md)',
            }}>
              <div className="flex items-center justify-between mb-sm">
                <span className="font-bold">{snapshot.areaName}</span>
                <RiskBadge level={snapshot.riskLevel} size="sm" />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, fontSize: 'var(--font-size-xs)' }}>
                <span className="text-hint">降雨: {snapshot.factors.rainfall}%</span>
                <span className="text-hint">水位: {snapshot.factors.waterLevel}%</span>
                <span className="text-hint">历史: {snapshot.factors.historicalFlood}%</span>
                <span className="text-hint">报告: {snapshot.factors.reportDensity}%</span>
              </div>
              <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)', marginTop: 8 }}>
                更新于 {dayjs(snapshot.updatedAt).fromNow()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 最近报告 */}
      <div className="card mb-md">
        <div className="card-title">最近报告</div>
        {data.recentReports.map(report => (
          <div key={report.id} style={{
            padding: 'var(--spacing-sm) 0',
            borderBottom: '1px solid var(--color-border-light)',
            cursor: 'pointer',
          }} onClick={() => window.location.href = `/reports/${report.id}`}>
            <div className="flex items-center justify-between">
              <span className="font-bold">{report.title}</span>
              <RiskBadge level={report.riskLevel} size="sm" />
            </div>
            <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
              {report.reporterName} · {report.location.address} · {dayjs(report.createdAt).fromNow()}
            </div>
          </div>
        ))}
      </div>

      {/* 数据新鲜度 */}
      <DataFreshness statuses={data.dataStatuses} />
    </div>
  );
}
