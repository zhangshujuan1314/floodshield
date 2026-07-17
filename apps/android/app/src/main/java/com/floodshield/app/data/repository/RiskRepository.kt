package com.floodshield.app.data.repository

import com.floodshield.app.data.api.Alert
import com.floodshield.app.data.api.AlertSummary
import com.floodshield.app.data.api.ApiService
import com.floodshield.app.data.api.Resource
import com.floodshield.app.data.api.RiskSignal
import com.floodshield.app.data.api.RiskSummary
import com.floodshield.app.data.api.RoadClosure
import com.floodshield.app.data.api.ShelterSummary
import com.floodshield.app.data.cache.OfflineCache
import com.floodshield.app.data.local.dao.AlertDao
import com.floodshield.app.data.local.dao.RiskDao
import com.floodshield.app.data.local.entity.CachedAlert
import com.floodshield.app.data.local.entity.CachedRisk
import com.squareup.moshi.Moshi
import com.squareup.moshi.Types
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RiskRepository @Inject constructor(
    private val api: ApiService,
    private val riskDao: RiskDao,
    private val alertDao: AlertDao,
    private val moshi: Moshi
) {
    private val stringListType = Types.newParameterizedType(List::class.java, String::class.java)
    private val signalListType = Types.newParameterizedType(List::class.java, RiskSignal::class.java)
    private val alertSummaryListType = Types.newParameterizedType(List::class.java, AlertSummary::class.java)
    private val shelterSummaryListType = Types.newParameterizedType(List::class.java, ShelterSummary::class.java)
    private val roadClosureListType = Types.newParameterizedType(List::class.java, RoadClosure::class.java)

    private val stringListAdapter = moshi.adapter<List<String>>(stringListType)
    private val signalListAdapter = moshi.adapter<List<RiskSignal>>(signalListType)
    private val alertSummaryAdapter = moshi.adapter<List<AlertSummary>>(alertSummaryListType)
    private val shelterSummaryAdapter = moshi.adapter<List<ShelterSummary>>(shelterSummaryListType)
    private val roadClosureAdapter = moshi.adapter<List<RoadClosure>>(roadClosureListType)
    private val alertListAdapter = moshi.adapter<List<Alert>>(
        Types.newParameterizedType(List::class.java, Alert::class.java)
    )

    /**
     * 获取附近风险概览。
     * 策略：API 优先，失败时回退到 Room 缓存。
     */
    fun getNearbyRisk(lat: Double, lon: Double): Flow<Resource<RiskSummary>> = flow {
        emit(Resource.Loading)

        try {
            val response = api.getNearbySummary(lat, lon)
            val data = response.data
            if (data != null) {
                riskDao.insertRisk(data.toCachedEntity())
                emit(Resource.Success(data))
            } else {
                emitCachedOrError("数据为空")
            }
        } catch (e: Exception) {
            emitCachedOrError(e.message ?: "网络错误", e)
        }
    }

    /**
     * 获取活跃预警列表。
     */
    fun getAlerts(): Flow<Resource<List<Alert>>> = flow {
        emit(Resource.Loading)

        try {
            val response = api.getAlerts(activeOnly = true)
            val data = response.data
            if (data != null) {
                alertDao.insertAlerts(data.map { it.toCachedEntity() })
                emit(Resource.Success(data))
            } else {
                emitCachedAlertsOrError("预警数据为空")
            }
        } catch (e: Exception) {
            emitCachedAlertsOrError(e.message ?: "网络错误", e)
        }
    }

    /**
     * 获取缓存的风险数据（离线模式）。
     */
    suspend fun getCachedRisk(): RiskSummary? {
        val cached = riskDao.getLatestRisk()
        return if (cached != null && !OfflineCache.isExpired(cached.cachedAt, OfflineCache.RISK_TTL_MS)) {
            cached.toDomain()
        } else {
            null
        }
    }

    /**
     * 获取缓存的预警数据（离线模式）。
     */
    suspend fun getCachedAlerts(): List<Alert> {
        return alertDao.getActiveAlerts()
            .filter { !OfflineCache.isExpired(it.cachedAt, OfflineCache.ALERT_TTL_MS) }
            .map { it.toDomain() }
    }

    private suspend fun kotlinx.coroutines.flow.FlowCollector<Resource<RiskSummary>>.emitCachedOrError(
        message: String,
        cause: Throwable? = null
    ) {
        val cached = riskDao.getLatestRisk()
        if (cached != null && !OfflineCache.isExpired(cached.cachedAt, OfflineCache.RISK_TTL_MS)) {
            emit(Resource.Success(cached.toDomain()))
        } else {
            emit(Resource.Error(message, cause))
        }
    }

    private suspend fun kotlinx.coroutines.flow.FlowCollector<Resource<List<Alert>>>.emitCachedAlertsOrError(
        message: String,
        cause: Throwable? = null
    ) {
        val cached = alertDao.getActiveAlerts()
            .filter { !OfflineCache.isExpired(it.cachedAt, OfflineCache.ALERT_TTL_MS) }
        if (cached.isNotEmpty()) {
            emit(Resource.Success(cached.map { it.toDomain() }))
        } else {
            emit(Resource.Error(message, cause))
        }
    }

    // ── Entity <-> Domain 转换 ──

    private fun RiskSummary.toCachedEntity() = CachedRisk(
        areaId = areaId,
        platformRiskBand = platformRiskBand,
        riskScore = riskScore,
        confidence = confidence,
        signalsJson = signalListAdapter.toJson(signals),
        activeAlertsJson = alertSummaryAdapter.toJson(activeAlerts),
        nearbySheltersJson = shelterSummaryAdapter.toJson(nearbyShelters),
        roadClosuresJson = roadClosureAdapter.toJson(roadClosures),
        actionsJson = stringListAdapter.toJson(actions)
    )

    private fun CachedRisk.toDomain() = RiskSummary(
        areaId = areaId,
        platformRiskBand = platformRiskBand,
        riskScore = riskScore,
        confidence = confidence,
        signals = signalListAdapter.fromJson(signalsJson) ?: emptyList(),
        activeAlerts = alertSummaryAdapter.fromJson(activeAlertsJson) ?: emptyList(),
        nearbyShelters = shelterSummaryAdapter.fromJson(nearbySheltersJson) ?: emptyList(),
        roadClosures = roadClosureAdapter.fromJson(roadClosuresJson) ?: emptyList(),
        actions = stringListAdapter.fromJson(actionsJson) ?: emptyList()
    )

    private fun Alert.toCachedEntity() = CachedAlert(
        id = id,
        source = source,
        alertType = alertType,
        severity = severity,
        title = title,
        description = description,
        effectiveAt = effectiveAt,
        expiresAt = expiresAt,
        isActive = isActive
    )

    private fun CachedAlert.toDomain() = Alert(
        id = id,
        source = source,
        alertType = alertType,
        severity = severity,
        title = title,
        description = description,
        effectiveAt = effectiveAt,
        expiresAt = expiresAt,
        isActive = isActive
    )
}
