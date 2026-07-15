'use client';

import { useState } from 'react';
import useSWR from 'swr';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import { fetchRoadEvents, fetchShelters, fetchRiskSnapshots } from '@/lib/api';
import RiskBadge from '@/components/RiskBadge';
import StatusBadge, { ROAD_SEVERITY_MAP, SHELTER_STATUS_MAP } from '@/components/StatusBadge';
import type { RoadEvent, Shelter, RiskSnapshot } from '@/lib/types';

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

  const { data: roadEvents } = useSWR<RoadEvent[]>('road-events', fetchRoadEvents);
  const { data: shelters } = useSWR<Shelter[]>('shelters', fetchShelters);
  const { data: riskSnapshots } = useSWR<RiskSnapshot[]>('risk-snapshots', fetchRiskSnapshots);

  const toggleLayer = (key: keyof MapLayers) => {
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));
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
              <span>🚧 道路事件</span>
            </label>
            <label className="layer-toggle">
              <input type="checkbox" checked={layers.riskPoints} onChange={() => toggleLayer('riskPoints')} />
              <span>⚠️ 风险点</span>
            </label>
            <label className="layer-toggle">
              <input type="checkbox" checked={layers.shelters} onChange={() => toggleLayer('shelters')} />
              <span>🏠 避险场所</span>
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
              <div className="card-title">道路事件 ({roadEvents?.length || 0})</div>
              {roadEvents?.map(event => (
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
              ))}
            </div>
          )}

          {/* 风险点列表 */}
          {activeTab === 'risk' && (
            <div className="card" style={{ flex: 1, overflowY: 'auto' }}>
              <div className="card-title">风险点 ({riskSnapshots?.length || 0})</div>
              {riskSnapshots?.map(snapshot => (
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
              ))}
            </div>
          )}

          {/* 避险场所列表 */}
          {activeTab === 'shelter' && (
            <div className="card" style={{ flex: 1, overflowY: 'auto' }}>
              <div className="card-title">避险场所 ({shelters?.length || 0})</div>
              {shelters?.map(shelter => (
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
                  <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                    容纳: {shelter.currentOccupancy}/{shelter.capacity}人
                    {shelter.accessibility ? ' · ♿无障碍' : ''}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
