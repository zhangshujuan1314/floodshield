package com.floodshield.app.data.repository

import com.floodshield.app.data.api.ApiService
import com.floodshield.app.data.api.Location
import com.floodshield.app.data.api.Resource
import com.floodshield.app.data.api.Shelter
import com.floodshield.app.data.cache.OfflineCache
import com.floodshield.app.data.local.dao.ShelterDao
import com.floodshield.app.data.local.entity.CachedShelter
import com.squareup.moshi.Moshi
import com.squareup.moshi.Types
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ShelterRepository @Inject constructor(
    private val api: ApiService,
    private val shelterDao: ShelterDao,
    private val moshi: Moshi
) {
    private val facilitiesAdapter = moshi.adapter<List<String>>(
        Types.newParameterizedType(List::class.java, String::class.java)
    )

    /**
     * 获取附近避难所。
     * 策略：API 优先，失败时回退到 Room 缓存。
     */
    fun getNearbyShelters(lat: Double, lon: Double): Flow<Resource<List<Shelter>>> = flow {
        emit(Resource.Loading)

        try {
            val response = api.getNearbyShelters(lat, lon)
            val data = response.data
            if (data != null) {
                shelterDao.clearAll()
                shelterDao.insertShelters(data.map { it.toCachedEntity() })
                emit(Resource.Success(data))
            } else {
                emitCachedOrError("避难所数据为空")
            }
        } catch (e: Exception) {
            emitCachedOrError(e.message ?: "网络错误", e)
        }
    }

    /**
     * 按名称搜索避难所（从缓存中搜索）。
     */
    suspend fun searchShelters(query: String): List<Shelter> {
        return shelterDao.searchByName(query).map { it.toDomain() }
    }

    /**
     * 获取缓存的避难所数据（离线模式）。
     */
    suspend fun getCachedShelters(): List<Shelter> {
        return shelterDao.getAllShelters()
            .filter { !OfflineCache.isExpired(it.cachedAt, OfflineCache.SHELTER_TTL_MS) }
            .map { it.toDomain() }
    }

    private suspend fun kotlinx.coroutines.flow.FlowCollector<Resource<List<Shelter>>>.emitCachedOrError(
        message: String,
        cause: Throwable? = null
    ) {
        val cached = shelterDao.getAllShelters()
            .filter { !OfflineCache.isExpired(it.cachedAt, OfflineCache.SHELTER_TTL_MS) }
        if (cached.isNotEmpty()) {
            emit(Resource.Success(cached.map { it.toDomain() }))
        } else {
            emit(Resource.Error(message, cause))
        }
    }

    // ── Entity <-> Domain 转换 ──

    private fun Shelter.toCachedEntity() = CachedShelter(
        id = id,
        name = name,
        address = address,
        distanceM = distanceM,
        capacity = capacity,
        currentOccupancy = currentOccupancy,
        status = status,
        facilitiesJson = facilitiesAdapter.toJson(facilities),
        lat = location.lat,
        lng = location.lng
    )

    private fun CachedShelter.toDomain() = Shelter(
        id = id,
        name = name,
        address = address,
        distanceM = distanceM,
        capacity = capacity,
        currentOccupancy = currentOccupancy,
        status = status,
        facilities = facilitiesAdapter.fromJson(facilitiesJson) ?: emptyList(),
        location = Location(lat = lat, lng = lng)
    )
}
