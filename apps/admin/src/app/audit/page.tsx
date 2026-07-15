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
];

export default function AuditPage() {
  const [filters, setFilters] = useState({
    role: '',
    resource: '',
    requestId: '',
    page: 1,
  });
  const [detailEntry, setDetailEntry] = useState<AuditLog | null>(null);

  const { data, error, isLoading } = useSWR<PaginatedData<AuditLog>>(
    ['audit-logs', filters],
    () => fetchAuditLogs({
      role: filters.role || undefined,
      resource: filters.resource || undefined,
      requestId: filters.requestId || undefined,
      page: filters.page,
      pageSize: 10,
    })
  );

  return (
    <div>
      <h2 className="section-title">审计日志</h2>

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
              value={filters.resource}
              onChange={e => setFilters(prev => ({ ...prev, resource: e.target.value, page: 1 }))}
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
                <span>{detailEntry.actor} ({detailEntry.actorRole})</span>
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

            {detailEntry.before && (
              <div className="mb-md">
                <div className="form-label">变更前 (Before)</div>
                <pre className="json-view">{JSON.stringify(detailEntry.before, null, 2)}</pre>
              </div>
            )}

            {detailEntry.after && (
              <div className="mb-md">
                <div className="form-label">变更后 (After)</div>
                <pre className="json-view">{JSON.stringify(detailEntry.after, null, 2)}</pre>
              </div>
            )}

            <div className="dialog-actions">
              <button className="btn btn-secondary" onClick={() => setDetailEntry(null)}>关闭</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
