'use client';

import { useState, useEffect } from 'react';
import useSWR from 'swr';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import { fetchRoadEvents, fetchShelters, fetchRiskSnapshots, createRoadEvent, updateShelter } from '@/lib/api';
import { hasPermission, getStoredUser } from '@/lib/auth';
import RiskBadge from '@/components/RiskBadge';
import StatusBadge, { ROAD_SEVERITY_MAP, SHELTER_STATUS_MAP } from '@/components/StatusBadge';
import ConfirmDialog from '@/components/ConfirmDialog';
import type { RoadEvent, Shelter, RiskSnapshot, User, RoadEventType, RoadEventSeverity, ShelterStatus } from '@/lib/types';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

interface MapLayers {
  roadEvents: boolean;
  riskPoints: boolean;
  shelters: boolean;
}

export default function MapPage() {
  const [layers, setLayers] = useState<MapLayers>({
    roadEvents: true,
    riskPoints: true,
    shelters: true,
  });
  const [activeTab, setActiveTab] = useState<'road' | 'risk' | 'shelter'>('road');
  const [user, setUser] = useState<User | null>(null);

  // Road event form
  const [showRoadForm, setShowRoadForm] = useState(false);
  const [roadForm, setRoadForm] = useState({
    roadSegmentRef: '',
    eventType: 'waterlogging' as RoadEventType,
    severity: 'difficult' as RoadEventSeverity,
    lng: '',
    lat: '',
    validFrom: '',
    validUntil: '',
  });
  const [creatingRoad, setCreatingRoad] = useState(false);

  // Shelter quick edit
  const [quickEditShelter, setQuickEditShelter] = useState<Shelter | null>(null);
  const [quickShelterStatus, setQuickShelterStatus] = useState<ShelterStatus>('open');

  const { data: roadEvents, mutate: mutateRoads } = useSWR<RoadEvent[]>('road-events', fetchRoadEvents);
  const { data: shelters, mutate: mutateShelters } = useSWR<Shelter[]>('shelters', fetchShelters);
  const { data: riskSnapshots } = useSWR<RiskSnapshot[]>('risk-snapshots', fetchRiskSnapshots);

  useEffect(() => {
    const stored = getStoredUser();
    if (stored) setUser(stored);
  }, []);

  const canEditMap = user ? hasPermission(user.role, 'map:edit') : false;
  const canEditShelter = user ? hasPermission(user.role, 'shelter:edit') : false;

  const toggleLayer = (key: keyof MapLayers) => {
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleCreateRoadEvent = async () => {
    if (!roadForm.roadSegmentRef.trim() || !roadForm.lng || !roadForm.lat) return;
    setCreatingRoad(true);
    await createRoadEvent({
      roadSegmentRef: roadForm.roadSegmentRef,
      eventType: roadForm.eventType,
      severity: roadForm.severity,
      geometry: { lng: Number(roadForm.lng), lat: Number(roadForm.lat) },
      validFrom: roadForm.validFrom || new Date().toISOString(),
      validUntil: roadForm.validUntil || new Date(Date.now() + 24 * 3600000).toISOString(),
    });
    setCreatingRoad(false);
    setShowRoadForm(false);
    setRoadForm({ roadSegmentRef: '', eventType: 'waterlogging', severity: 'difficult', lng: '', lat: '', validFrom: '', validUntil: '' });
    mutateRoads();
  };

  const handleQuickShelterUpdate = async () => {
    if (!quickEditShelter) return;
    await updateShelter(quickEditShelter.id, { status: quickShelterStatus });
    setQuickEditShelter(null);
    mutateShelters();
  };

  return (
    <div>
      <h2 className="section-title">地图管理</h2>

      <div className="map-container">
        {/* 地图视图（占位） */}
        <div className="map-view">
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🗺️</div>
            <div>地图视图</div>
            <div className="text-hint" style={{ fontSize: 'var(--font-size-sm)', marginTop: 8 }}>
              道路事件: {roadEvents?.filter(e => e.isActive).length || 0} |
              风险点: {riskSnapshots?.length || 0} |
              避险场所: {shelters?.length || 0}
            </div>
          </div>
        </div>

        {/* 侧边栏 */}
        <div className="map-sidebar">
          {/* 图层控制 */}
          <div className="map-layers">
            <div className="card-title">图层控制</div>
            <label className="layer-toggle">
              <input type="checkbox" checked={layers.roadEvents} onChange={() => toggleLayer('roadEvents')} />
              <span>🚧 道路事件 ({roadEvents?.filter(e => e.isActive).length || 0})</span>
            </label>
            <label className="layer-toggle">
              <input type="checkbox" checked={layers.riskPoints} onChange={() => toggleLayer('riskPoints')} />
              <span>⚠️ 风险点 ({riskSnapshots?.filter(r => r.riskLevel !== 'normal').length || 0})</span>
            </label>
            <label className="layer-toggle">
              <input type="checkbox" checked={layers.shelters} onChange={() => toggleLayer('shelters')} />
              <span>🏠 避险场所 ({shelters?.length || 0})</span>
            </label>
          </div>

          {/* Tab 切换 */}
          <div className="filter-bar">
            <button className={`filter-btn ${activeTab === 'road' ? 'active' : ''}`} onClick={() => setActiveTab('road')}>
              🚧 道路
            </button>
            <button className={`filter-btn ${activeTab === 'risk' ? 'active' : ''}`} onClick={() => setActiveTab('risk')}>
              ⚠️ 风险
            </button>
            <button className={`filter-btn ${activeTab === 'shelter' ? 'active' : ''}`} onClick={() => setActiveTab('shelter')}>
              🏠 场所
            </button>
          </div>

          {/* 道路事件列表 */}
          {activeTab === 'road' && (
            <div className="card" style={{ flex: 1, overflowY: 'auto' }}>
              <div className="flex items-center justify-between mb-md">
                <div className="card-title" style={{ marginBottom: 0 }}>道路事件 ({roadEvents?.length || 0})</div>
                {canEditMap && (
                  <button className="btn btn-primary btn-sm" onClick={() => setShowRoadForm(true)}>
                    + 新增
                  </button>
                )}
              </div>
              {!roadEvents || roadEvents.length === 0 ? (
                <div className="text-hint">暂无道路事件</div>
              ) : (
                roadEvents.map(event => (
                  <div key={event.id} style={{
                    padding: 'var(--spacing-sm) 0',
                    borderBottom: '1px solid var(--color-border-light)',
                  }}>
                    <div className="flex items-center justify-between mb-sm">
                      <span className="font-bold">{event.roadName}</span>
                      <StatusBadge status={event.severity} statusMap={ROAD_SEVERITY_MAP} />
                    </div>
                    <div className="text-secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                      {event.description}
                    </div>
                    <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                      {dayjs(event.reportedAt).fromNow()} · {event.isActive ? '进行中' : '已解决'}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* 风险点列表 */}
          {activeTab === 'risk' && (
            <div className="card" style={{ flex: 1, overflowY: 'auto' }}>
              <div className="card-title">风险点 ({riskSnapshots?.length || 0})</div>
              {!riskSnapshots || riskSnapshots.length === 0 ? (
                <div className="text-hint">暂无风险数据</div>
              ) : (
                riskSnapshots.map(snapshot => (
                  <div key={snapshot.areaId} style={{
                    padding: 'var(--spacing-sm) 0',
                    borderBottom: '1px solid var(--color-border-light)',
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
                    <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                      更新于 {dayjs(snapshot.updatedAt).fromNow()}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* 避险场所列表 */}
          {activeTab === 'shelter' && (
            <div className="card" style={{ flex: 1, overflowY: 'auto' }}>
              <div className="card-title">避险场所 ({shelters?.length || 0})</div>
              {!shelters || shelters.length === 0 ? (
                <div className="text-hint">暂无避险场所</div>
              ) : (
                shelters.map(shelter => {
                  const pct = Math.round((shelter.currentOccupancy / shelter.capacity) * 100);
                  const barColor = pct >= 90 ? 'var(--color-danger)' : pct >= 70 ? 'var(--color-warning)' : 'var(--color-safe)';
                  return (
                    <div key={shelter.id} style={{
                      padding: 'var(--spacing-sm) 0',
                      borderBottom: '1px solid var(--color-border-light)',
                    }}>
                      <div className="flex items-center justify-between mb-sm">
                        <span className="font-bold">{shelter.name}</span>
                        <StatusBadge status={shelter.status} statusMap={SHELTER_STATUS_MAP} />
                      </div>
                      <div className="text-secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                        {shelter.address}
                      </div>
                      <div style={{ marginTop: 4 }}>
                        <div className="flex items-center justify-between" style={{ fontSize: 'var(--font-size-xs)' }}>
                          <span className="text-hint">入住: {shelter.currentOccupancy}/{shelter.capacity}人</span>
                          <span className="text-hint">{pct}%</span>
                        </div>
                        <div style={{ background: '#f0f0f0', borderRadius: 4, height: 4, marginTop: 2 }}>
                          <div style={{ background: barColor, borderRadius: 4, height: 4, width: `${Math.min(pct, 100)}%` }} />
                        </div>
                      </div>
                      <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                        {shelter.accessibility ? '♿ 无障碍' : ''}
                        {canEditShelter && (
                          <button
                            className="btn-link"
                            style={{ marginLeft: 8 }}
                            onClick={() => { setQuickEditShelter(shelter); setQuickShelterStatus(shelter.status); }}
                          >
                            更新状态
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>
      </div>

      {/* 新增道路事件表单 */}
      {showRoadForm && (
        <div className="dialog-overlay" onClick={() => setShowRoadForm(false)}>
          <div className="dialog-box" style={{ maxWidth: 480 }} onClick={e => e.stopPropagation()}>
            <div className="dialog-header">
              <span className="dialog-icon">🚧</span>
              <h3 className="dialog-title">新增道路事件</h3>
            </div>

            <div className="form-group">
              <label className="form-label">路段名称</label>
              <input
                type="text"
                className="form-input"
                placeholder="如：望京西路"
                value={roadForm.roadSegmentRef}
                onChange={e => setRoadForm(prev => ({ ...prev, roadSegmentRef: e.target.value }))}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">事件类型</label>
                <select
                  className="form-select"
                  value={roadForm.eventType}
                  onChange={e => setRoadForm(prev => ({ ...prev, eventType: e.target.value as RoadEventType }))}
                >
                  <option value="waterlogging">积水</option>
                  <option value="blocked">阻断</option>
                  <option value="collapsed">塌陷</option>
                  <option value="debris">杂物</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">严重程度</label>
                <select
                  className="form-select"
                  value={roadForm.severity}
                  onChange={e => setRoadForm(prev => ({ ...prev, severity: e.target.value as RoadEventSeverity }))}
                >
                  <option value="passable">可通行</option>
                  <option value="difficult">通行困难</option>
                  <option value="blocked">断路</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">经度</label>
                <input
                  type="number"
                  step="0.001"
                  className="form-input"
                  placeholder="116.xxx"
                  value={roadForm.lng}
                  onChange={e => setRoadForm(prev => ({ ...prev, lng: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">纬度</label>
                <input
                  type="number"
                  step="0.001"
                  className="form-input"
                  placeholder="39.xxx"
                  value={roadForm.lat}
                  onChange={e => setRoadForm(prev => ({ ...prev, lat: e.target.value }))}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">生效时间</label>
                <input
                  type="datetime-local"
                  className="form-input"
                  value={roadForm.validFrom}
                  onChange={e => setRoadForm(prev => ({ ...prev, validFrom: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">失效时间</label>
                <input
                  type="datetime-local"
                  className="form-input"
                  value={roadForm.validUntil}
                  onChange={e => setRoadForm(prev => ({ ...prev, validUntil: e.target.value }))}
                />
              </div>
            </div>

            <div className="dialog-actions">
              <button className="btn btn-secondary" onClick={() => setShowRoadForm(false)}>取消</button>
              <button
                className="btn btn-primary"
                onClick={handleCreateRoadEvent}
                disabled={creatingRoad || !roadForm.roadSegmentRef.trim() || !roadForm.lng || !roadForm.lat}
              >
                {creatingRoad ? '创建中...' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 避险场所快速状态更新 */}
      <ConfirmDialog
        open={!!quickEditShelter}
        title={`更新状态 - ${quickEditShelter?.name || ''}`}
        message={`将「${quickEditShelter?.name}」的状态更改为：`}
        confirmText="确认更新"
        variant="warning"
        onConfirm={handleQuickShelterUpdate}
        onCancel={() => setQuickEditShelter(null)}
      />
      {quickEditShelter && (
        <div style={{ position: 'fixed', bottom: 80, left: '50%', transform: 'translateX(-50%)', zIndex: 1001, display: 'flex', gap: 8 }}>
          {(['open', 'full', 'closed', 'maintenance'] as ShelterStatus[]).map(s => {
            const labels: Record<string, string> = { open: '🟢 开放', full: '🟡 满员', closed: '⚪ 关闭', maintenance: '🔧 维护' };
            return (
              <button
                key={s}
                className={`btn btn-sm ${quickShelterStatus === s ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setQuickShelterStatus(s)}
              >
                {labels[s]}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
