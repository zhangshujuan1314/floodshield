'use client';

import { useState } from 'react';
import useSWR from 'swr';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import { fetchAuditLogs } from '@/lib/api';
import AuditEntry from '@/components/AuditEntry';
import type { AuditLog, PaginatedData } from '@/lib/types';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const ROLE_OPTIONS = [
  { value: '', label: '全部角色' },
  { value: 'admin', label: '管理员' },
  { value: 'community', label: '社区' },
  { value: 'emergency_station', label: '应急站' },
];

const RESOURCE_OPTIONS = [
  { value: '', label: '全部资源' },
  { value: 'report', label: '报告' },
  { value: 'task', label: '任务' },
  { value: 'shelter', label: '避险场所' },
  { value: 'notification', label: '通知' },
  { value: 'road_event', label: '道路事件' },
];

export default function AuditPage() {
  const [filters, setFilters] = useState({
    role: '',
    resourceType: '',
    requestId: '',
    from: '',
    to: '',
    page: 1,
  });
  const [detailEntry, setDetailEntry] = useState<AuditLog | null>(null);

  const { data, error, isLoading } = useSWR<PaginatedData<AuditLog>>(
    ['audit-logs', filters],
    () => fetchAuditLogs({
      role: filters.role || undefined,
      resourceType: filters.resourceType || undefined,
      requestId: filters.requestId || undefined,
      from: filters.from || undefined,
      to: filters.to || undefined,
      page: filters.page,
      pageSize: 10,
    })
  );

  const handleExport = () => {
    // Placeholder: in production, would call an export API or generate CSV client-side
    const rows = (data?.items || []).map(entry => ({
      时间: dayjs(entry.timestamp).format('YYYY-MM-DD HH:mm:ss'),
      操作者: entry.actor,
      角色: entry.actorRole,
      操作: entry.action,
      资源: `${entry.resource}/${entry.resourceId}`,
      详情: entry.detail || '',
      请求ID: entry.requestId,
      IP: entry.ip,
    }));
    const csv = [
      Object.keys(rows[0] || {}).join(','),
      ...rows.map(r => Object.values(r).map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')),
    ].join('\n');
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-logs-${dayjs().format('YYYYMMDD-HHmmss')}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderDiffView = (before?: Record<string, unknown>, after?: Record<string, unknown>) => {
    if (!before && !after) return null;
    const allKeys = new Set([
      ...Object.keys(before || {}),
      ...Object.keys(after || {}),
    ]);
    return (
      <div style={{ marginTop: 'var(--spacing-sm)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-sm)' }}>
          <div>
            <div className="form-label" style={{ fontSize: 'var(--font-size-xs)', marginBottom: 4 }}>变更前</div>
            <pre className="json-view" style={{ fontSize: 'var(--font-size-xs)', maxHeight: 200 }}>
              {before ? JSON.stringify(before, null, 2) : '(无)'}
            </pre>
          </div>
          <div>
            <div className="form-label" style={{ fontSize: 'var(--font-size-xs)', marginBottom: 4 }}>变更后</div>
            <pre className="json-view" style={{ fontSize: 'var(--font-size-xs)', maxHeight: 200 }}>
              {after ? JSON.stringify(after, null, 2) : '(无)'}
            </pre>
          </div>
        </div>
        {/* Field-level diff */}
        {before && after && (
          <div style={{ marginTop: 'var(--spacing-sm)' }}>
            <div className="form-label" style={{ fontSize: 'var(--font-size-xs)', marginBottom: 4 }}>字段差异</div>
            <div style={{ background: '#fafafa', borderRadius: 'var(--radius-sm)', padding: 'var(--spacing-sm)', fontSize: 'var(--font-size-xs)' }}>
              {Array.from(allKeys).map(key => {
                const bVal = before[key];
                const aVal = after[key];
                if (JSON.stringify(bVal) === JSON.stringify(aVal)) return null;
                return (
                  <div key={key} style={{ display: 'flex', gap: 'var(--spacing-sm)', padding: '2px 0', borderBottom: '1px solid var(--color-border-light)' }}>
                    <span style={{ fontFamily: 'monospace', minWidth: 100, color: 'var(--color-text-secondary)' }}>{key}</span>
                    <span style={{ color: 'var(--color-danger)', textDecoration: 'line-through', flex: 1 }}>
                      {bVal !== undefined ? JSON.stringify(bVal) : '(无)'}
                    </span>
                    <span style={{ color: 'var(--color-safe)', flex: 1 }}>
                      {aVal !== undefined ? JSON.stringify(aVal) : '(无)'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-lg">
        <h2 className="section-title" style={{ marginBottom: 0 }}>审计日志</h2>
        <button className="btn btn-secondary" onClick={handleExport}>
          📤 导出CSV
        </button>
      </div>

      {/* 筛选栏 */}
      <div className="card mb-md">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 'var(--spacing-md)' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">角色</label>
            <select
              className="form-select"
              value={filters.role}
              onChange={e => setFilters(prev => ({ ...prev, role: e.target.value, page: 1 }))}
            >
              {ROLE_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">资源类型</label>
            <select
              className="form-select"
              value={filters.resourceType}
              onChange={e => setFilters(prev => ({ ...prev, resourceType: e.target.value, page: 1 }))}
            >
              {RESOURCE_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">请求ID</label>
            <input
              type="text"
              className="form-input"
              placeholder="搜索请求ID"
              value={filters.requestId}
              onChange={e => setFilters(prev => ({ ...prev, requestId: e.target.value, page: 1 }))}
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">开始日期</label>
            <input
              type="datetime-local"
              className="form-input"
              value={filters.from}
              onChange={e => setFilters(prev => ({ ...prev, from: e.target.value, page: 1 }))}
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">结束日期</label>
            <input
              type="datetime-local"
              className="form-input"
              value={filters.to}
              onChange={e => setFilters(prev => ({ ...prev, to: e.target.value, page: 1 }))}
            />
          </div>
        </div>
      </div>

      {/* 日志列表 */}
      {isLoading ? (
        <div className="empty-state"><div className="empty-state-icon">⏳</div><div className="empty-state-text">加载中...</div></div>
      ) : error ? (
        <div className="empty-state"><div className="empty-state-icon">❌</div><div className="empty-state-text">加载失败</div></div>
      ) : (data?.items || []).length === 0 ? (
        <div className="empty-state"><div className="empty-state-icon">📝</div><div className="empty-state-text">暂无审计日志</div></div>
      ) : (
        <>
          {(data?.items || []).map(entry => (
            <AuditEntry key={entry.id} entry={entry} onViewDetail={setDetailEntry} />
          ))}

          {/* 分页 */}
          {data && data.totalPages > 1 && (
            <div className="flex items-center justify-between mt-md">
              <span className="text-hint" style={{ fontSize: 'var(--font-size-sm)' }}>
                共 {data.total} 条，第 {data.page}/{data.totalPages} 页
              </span>
              <div className="flex gap-sm">
                <button
                  className="pagination-btn"
                  disabled={filters.page <= 1}
                  onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
                >
                  上一页
                </button>
                <button
                  className="pagination-btn"
                  disabled={filters.page >= data.totalPages}
                  onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* 详情模态 */}
      {detailEntry && (
        <div className="dialog-overlay" onClick={() => setDetailEntry(null)}>
          <div className="dialog-box audit-detail-modal" onClick={e => e.stopPropagation()}>
            <div className="dialog-header">
              <span className="dialog-icon">📝</span>
              <h3 className="dialog-title">审计详情</h3>
            </div>

            <div style={{ fontSize: 'var(--font-size-sm)', marginBottom: 'var(--spacing-md)' }}>
              <div className="flex justify-between mb-sm">
                <span className="text-hint">操作</span>
                <span className="font-bold">{detailEntry.action}</span>
              </div>
              <div className="flex justify-between mb-sm">
                <span className="text-hint">操作人</span>
                <span>{detailEntry.actor} ({detailEntry.actorRole === 'admin' ? '管理员' : detailEntry.actorRole === 'community' ? '社区' : '应急站'})</span>
              </div>
              <div className="flex justify-between mb-sm">
                <span className="text-hint">资源</span>
                <span style={{ fontFamily: 'monospace' }}>{detailEntry.resource}/{detailEntry.resourceId}</span>
              </div>
              <div className="flex justify-between mb-sm">
                <span className="text-hint">请求ID</span>
                <span style={{ fontFamily: 'monospace' }}>{detailEntry.requestId}</span>
              </div>
              <div className="flex justify-between mb-sm">
                <span className="text-hint">IP</span>
                <span style={{ fontFamily: 'monospace' }}>{detailEntry.ip}</span>
              </div>
              <div className="flex justify-between mb-sm">
                <span className="text-hint">时间</span>
                <span>{dayjs(detailEntry.timestamp).format('YYYY-MM-DD HH:mm:ss')}</span>
              </div>
              {detailEntry.detail && (
                <div className="mb-sm">
                  <span className="text-hint">详情</span>
                  <div style={{ marginTop: 4, padding: 'var(--spacing-sm)', background: '#f5f5f5', borderRadius: 'var(--radius-sm)' }}>
                    {detailEntry.detail}
                  </div>
                </div>
              )}
            </div>

            {/* Diff 视图 */}
            {renderDiffView(detailEntry.before, detailEntry.after)}

            <div className="dialog-actions">
              <button className="btn btn-secondary" onClick={() => setDetailEntry(null)}>关闭</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
