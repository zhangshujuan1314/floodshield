package com.floodshield.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.floodshield.app.data.local.entity.CachedRisk

@Dao
interface RiskDao {
    @Query("SELECT * FROM cached_risks ORDER BY cachedAt DESC LIMIT 1")
    suspend fun getLatestRisk(): CachedRisk?

    @Query("SELECT * FROM cached_risks WHERE areaId = :areaId")
    suspend fun getRiskByAreaId(areaId: String): CachedRisk?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertRisk(risk: CachedRisk)

    @Query("DELETE FROM cached_risks WHERE cachedAt < :threshold")
    suspend fun deleteExpired(threshold: Long)

    @Query("DELETE FROM cached_risks")
    suspend fun clearAll()
}
