'use client';

import { useState, useEffect } from 'react';
import useSWR from 'swr';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import { fetchReport, verifyReport, rejectReport } from '@/lib/api';
import { hasPermission, getStoredUser } from '@/lib/auth';
import RiskBadge from '@/components/RiskBadge';
import StatusBadge, { REPORT_STATUS_MAP, REPORT_TYPE_MAP } from '@/components/StatusBadge';
import ConfirmDialog from '@/components/ConfirmDialog';
import type { Report, User } from '@/lib/types';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

export default function ReportDetailPage({ params }: { params: { id: string } }) {
  const { data: report, error, isLoading, mutate } = useSWR<Report>(
    ['report', params.id],
    () => fetchReport(params.id)
  );
  const [confirmAction, setConfirmAction] = useState<'verify' | 'reject' | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const stored = getStoredUser();
    if (stored) setUser(stored);
  }, []);

  const canViewPreciseLocation = user ? hasPermission(user.role, 'user:precise_location') : false;
  const canVerify = user ? hasPermission(user.role, 'report:verify') : false;
  const canReject = user ? hasPermission(user.role, 'report:reject') : false;

  const handleVerify = async () => {
    await verifyReport(params.id);
    setConfirmAction(null);
    mutate();
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) return;
    await rejectReport(params.id, rejectReason);
    setConfirmAction(null);
    setRejectReason('');
    mutate();
  };

  if (isLoading) {
    return <div className="empty-state"><div className="empty-state-icon">⏳</div><div className="empty-state-text">加载中...</div></div>;
  }

  if (error || !report) {
    return <div className="empty-state"><div className="empty-state-icon">❌</div><div className="empty-state-text">报告不存在或加载失败</div></div>;
  }

  const typeConfig = REPORT_TYPE_MAP[report.type] || { label: report.type, icon: '📌' };

  return (
    <div>
      <div className="flex items-center gap-md mb-lg">
        <a href="/reports" className="btn btn-secondary btn-sm">← 返回列表</a>
        <h2 className="section-title" style={{ marginBottom: 0 }}>报告详情</h2>
      </div>

      <div className="report-detail">
        <div className="report-detail-main">
          {/* 基本信息 */}
          <div className="card">
            <div className="flex items-center justify-between mb-md">
              <div className="flex items-center gap-sm">
                <span style={{ fontSize: 24 }}>{typeConfig.icon}</span>
                <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600 }}>{report.title}</h3>
              </div>
              <StatusBadge status={report.status} statusMap={REPORT_STATUS_MAP} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-md)' }}>
              <div>
                <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>报告人</div>
                <div>{report.reporterName} {report.reporterPhone && `(${report.reporterPhone})`}</div>
              </div>
              <div>
                <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>报告类型</div>
                <div>{typeConfig.icon} {typeConfig.label}</div>
              </div>
              <div>
                <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>风险等级</div>
                <div><RiskBadge level={report.riskLevel} /></div>
              </div>
              <div>
                <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>可信度</div>
                <div style={{
                  color: report.credibilityScore >= 0.8 ? 'var(--color-safe)' : report.credibilityScore >= 0.5 ? 'var(--color-warning)' : 'var(--color-danger)',
                  fontWeight: 600,
                  fontSize: 'var(--font-size-lg)',
                }}>
                  {Math.round(report.credibilityScore * 100)}%
                </div>
              </div>
              <div>
                <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>优先级</div>
                <div style={{ fontWeight: 600 }}>{report.priority}/5</div>
              </div>
              <div>
                <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>创建时间</div>
                <div>{dayjs(report.createdAt).format('YYYY-MM-DD HH:mm:ss')}</div>
              </div>
            </div>
          </div>

          {/* 描述 */}
          <div className="card">
            <div className="card-title">描述</div>
            <p style={{ lineHeight: 1.8 }}>{report.description}</p>
          </div>

          {/* 照片证据 */}
          <div className="card">
            <div className="card-title">照片证据 ({report.photos.length})</div>
            {report.photos.length === 0 ? (
              <div className="text-hint">暂无照片</div>
            ) : (
              <div className="report-photos">
                {report.photos.map((photo, i) => (
                  <div key={i} className="report-photo">
                    📷 照片 {i + 1}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 位置信息 */}
          <div className="card">
            <div className="card-title">位置信息</div>
            <div style={{ marginBottom: 'var(--spacing-sm)' }}>
              <span className="text-hint">公开地址：</span>
              <span>{report.location.address}</span>
            </div>
            {report.location.preciseAddress && canViewPreciseLocation && (
              <div style={{ marginBottom: 'var(--spacing-sm)' }}>
                <span className="text-hint">精确地址：</span>
                <span className="font-bold">{report.location.preciseAddress}</span>
                <span className="text-hint" style={{ fontSize: 'var(--font-size-xs)', marginLeft: 8 }}>(仅授权角色可见)</span>
              </div>
            )}
            {canViewPreciseLocation ? (
              <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>
                经度: {report.location.lng} / 纬度: {report.location.lat}
              </div>
            ) : (
              <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>
                位置精度已模糊化（需授权角色查看精确坐标）
              </div>
            )}
            {/* 地图预览占位 */}
            <div className="map-view" style={{ height: 200, marginTop: 'var(--spacing-sm)' }}>
              📍 地图预览 ({report.location.address})
            </div>
          </div>

          {/* 核验历史 */}
          <div className="card">
            <div className="card-title">操作历史</div>
            {report.auditTrail.map((action, i) => (
              <div key={i} style={{
                padding: 'var(--spacing-sm) 0',
                borderBottom: i < report.auditTrail.length - 1 ? '1px solid var(--color-border-light)' : 'none',
              }}>
                <div className="flex items-center justify-between">
                  <span className="font-bold">{action.action}</span>
                  <span className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>
                    {dayjs(action.timestamp).format('MM-DD HH:mm:ss')}
                  </span>
                </div>
                <div className="text-secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                  {action.actor} ({action.actorRole})
                  {action.detail && ` - ${action.detail}`}
                </div>
              </div>
            ))}
          </div>

          {/* 驳回原因 */}
          {report.rejectReason && (
            <div className="card" style={{ borderColor: 'var(--color-danger)' }}>
              <div className="card-title text-danger">驳回原因</div>
              <p>{report.rejectReason}</p>
            </div>
          )}
        </div>

        {/* 侧边操作栏 */}
        <div className="report-detail-sidebar">
          <div className="card">
            <div className="card-title">操作</div>
            {report.status === 'pending_review' ? (
              <div className="report-actions">
                {canVerify && (
                  <button className="btn btn-success" onClick={() => setConfirmAction('verify')}>
                    ✅ 核验通过
                  </button>
                )}
                {canReject && (
                  <button className="btn btn-danger" onClick={() => setConfirmAction('reject')}>
                    ❌ 驳回报告
                  </button>
                )}
                {!canVerify && !canReject && (
                  <div className="text-hint">您没有核验或驳回报告的权限</div>
                )}
              </div>
            ) : (
              <div className="text-hint">
                该报告已{report.status === 'verified' ? '核验通过' : report.status === 'rejected' ? '被驳回' : '过期'}
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-title">报告信息</div>
            <div style={{ fontSize: 'var(--font-size-sm)' }}>
              <div className="flex justify-between mb-sm">
                <span className="text-hint">报告ID</span>
                <span style={{ fontFamily: 'monospace' }}>{report.id}</span>
              </div>
              <div className="flex justify-between mb-sm">
                <span className="text-hint">创建时间</span>
                <span>{dayjs(report.createdAt).format('MM-DD HH:mm')}</span>
              </div>
              <div className="flex justify-between mb-sm">
                <span className="text-hint">更新时间</span>
                <span>{dayjs(report.updatedAt).format('MM-DD HH:mm')}</span>
              </div>
              {report.verifiedBy && (
                <div className="flex justify-between mb-sm">
                  <span className="text-hint">核验人</span>
                  <span>{report.verifiedBy}</span>
                </div>
              )}
              {report.verifiedAt && (
                <div className="flex justify-between">
                  <span className="text-hint">核验时间</span>
                  <span>{dayjs(report.verifiedAt).format('MM-DD HH:mm')}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 核验确认 */}
      <ConfirmDialog
        open={confirmAction === 'verify'}
        title="确认核验报告"
        message={`确定要核验通过报告「${report.title}」吗？核验后该报告将标记为已确认。`}
        confirmText="确认核验"
        onConfirm={handleVerify}
        onCancel={() => setConfirmAction(null)}
      />

      {/* 驳回对话框 */}
      {confirmAction === 'reject' && (
        <div className="dialog-overlay" onClick={() => setConfirmAction(null)}>
          <div className="dialog-box dialog-danger" onClick={e => e.stopPropagation()}>
            <div className="dialog-header">
              <span className="dialog-icon">⚠️</span>
              <h3 className="dialog-title">驳回报告</h3>
            </div>
            <p className="dialog-message">确定要驳回报告「{report.title}」吗？请填写驳回原因。</p>
            <div className="form-group">
              <textarea
                className="form-textarea"
                placeholder="请输入驳回原因（必填）"
                value={rejectReason}
                onChange={e => setRejectReason(e.target.value)}
                rows={3}
              />
            </div>
            <div className="dialog-actions">
              <button className="btn btn-secondary" onClick={() => { setConfirmAction(null); setRejectReason(''); }}>取消</button>
              <button className="btn btn-danger" disabled={!rejectReason.trim()} onClick={handleReject}>确认驳回</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
