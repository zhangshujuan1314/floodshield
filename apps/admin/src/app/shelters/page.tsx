'use client';

import { useState } from 'react';
import useSWR from 'swr';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import { fetchShelters, updateShelter } from '@/lib/api';
import DataTable, { Column } from '@/components/DataTable';
import StatusBadge, { SHELTER_STATUS_MAP } from '@/components/StatusBadge';
import ConfirmDialog from '@/components/ConfirmDialog';
import type { Shelter, ShelterStatus } from '@/lib/types';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const VERIFICATION_MAP: Record<string, { label: string; icon: string; className: string }> = {
  verified: { label: '已核验', icon: '✅', className: 'status-verified' },
  unverified: { label: '未核验', icon: '❓', className: 'status-pending' },
  outdated: { label: '过期', icon: '⏰', className: 'status-expired' },
};

export default function SheltersPage() {
  const { data: shelters, error, isLoading, mutate } = useSWR<Shelter[]>(
    'shelters',
    fetchShelters
  );

  const [editingShelter, setEditingShelter] = useState<Shelter | null>(null);
  const [formData, setFormData] = useState<Partial<Shelter>>({});
  const [saving, setSaving] = useState(false);

  const handleEdit = (shelter: Shelter) => {
    setEditingShelter(shelter);
    setFormData({
      capacity: shelter.capacity,
      status: shelter.status,
      accessibility: shelter.accessibility,
      contactName: shelter.contactName,
      contactPhone: shelter.contactPhone,
    });
  };

  const handleSave = async () => {
    if (!editingShelter) return;
    setSaving(true);
    await updateShelter(editingShelter.id, formData);
    setSaving(false);
    setEditingShelter(null);
    mutate();
  };

  const columns: Column<Shelter>[] = [
    {
      key: 'name',
      title: '名称',
      sortable: true,
      render: (val, row) => (
        <div>
          <div className="font-bold">{String(val)}</div>
          <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>{row.address}</div>
        </div>
      ),
    },
    {
      key: 'status',
      title: '状态',
      width: '90px',
      render: (val) => <StatusBadge status={val as string} statusMap={SHELTER_STATUS_MAP} />,
    },
    {
      key: 'currentOccupancy',
      title: '入住',
      width: '100px',
      sortable: true,
      render: (val, row) => {
        const occupancy = val as number;
        const pct = Math.round((occupancy / row.capacity) * 100);
        const color = pct >= 90 ? 'var(--color-danger)' : pct >= 70 ? 'var(--color-warning)' : 'var(--color-safe)';
        return (
          <div>
            <span style={{ color, fontWeight: 600 }}>{occupancy}</span>
            <span className="text-hint">/{row.capacity}</span>
            <div style={{ background: '#f0f0f0', borderRadius: 4, height: 4, marginTop: 4 }}>
              <div style={{ background: color, borderRadius: 4, height: 4, width: `${Math.min(pct, 100)}%` }} />
            </div>
          </div>
        );
      },
    },
    {
      key: 'accessibility',
      title: '无障碍',
      width: '70px',
      render: (val) => (val ? '✅ 是' : '❌ 否'),
    },
    {
      key: 'verificationStatus',
      title: '核验',
      width: '80px',
      render: (val) => <StatusBadge status={val as string} statusMap={VERIFICATION_MAP} />,
    },
    {
      key: 'contactName',
      title: '联系人',
      width: '100px',
      render: (val, row) => (
        <div>
          <div>{String(val)}</div>
          <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>{row.contactPhone}</div>
        </div>
      ),
    },
    {
      key: 'updatedAt',
      title: '更新',
      width: '80px',
      render: (val) => (
        <span className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>
          {dayjs(val as string).fromNow()}
        </span>
      ),
    },
    {
      key: 'id',
      title: '操作',
      width: '60px',
      render: (_val, row) => (
        <button className="btn btn-secondary btn-sm" onClick={(e) => { e.stopPropagation(); handleEdit(row); }}>
          编辑
        </button>
      ),
    },
  ];

  return (
    <div>
      <h2 className="section-title">避险场所管理</h2>

      {isLoading ? (
        <div className="empty-state"><div className="empty-state-icon">⏳</div><div className="empty-state-text">加载中...</div></div>
      ) : error ? (
        <div className="empty-state"><div className="empty-state-icon">❌</div><div className="empty-state-text">加载失败</div></div>
      ) : (
        <DataTable
          columns={columns}
          data={shelters || []}
          rowKey="id"
          emptyText="暂无避险场所"
        />
      )}

      {/* 编辑表单 */}
      {editingShelter && (
        <div className="dialog-overlay" onClick={() => setEditingShelter(null)}>
          <div className="dialog-box" style={{ maxWidth: 480 }} onClick={e => e.stopPropagation()}>
            <div className="dialog-header">
              <span className="dialog-icon">🏠</span>
              <h3 className="dialog-title">编辑避险场所 - {editingShelter.name}</h3>
            </div>

            <div className="form-group">
              <label className="form-label">容纳人数</label>
              <input
                type="number"
                className="form-input"
                value={formData.capacity || 0}
                onChange={e => setFormData(prev => ({ ...prev, capacity: Number(e.target.value) }))}
              />
            </div>

            <div className="form-group">
              <label className="form-label">状态</label>
              <select
                className="form-select"
                value={formData.status || 'open'}
                onChange={e => setFormData(prev => ({ ...prev, status: e.target.value as ShelterStatus }))}
              >
                <option value="open">开放</option>
                <option value="full">满员</option>
                <option value="closed">关闭</option>
                <option value="maintenance">维护中</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">
                <input
                  type="checkbox"
                  checked={formData.accessibility || false}
                  onChange={e => setFormData(prev => ({ ...prev, accessibility: e.target.checked }))}
                  style={{ marginRight: 8 }}
                />
                无障碍设施
              </label>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">联系人</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.contactName || ''}
                  onChange={e => setFormData(prev => ({ ...prev, contactName: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">联系电话</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.contactPhone || ''}
                  onChange={e => setFormData(prev => ({ ...prev, contactPhone: e.target.value }))}
                />
              </div>
            </div>

            <div className="dialog-actions">
              <button className="btn btn-secondary" onClick={() => setEditingShelter(null)}>取消</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
