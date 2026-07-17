package com.floodshield.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.floodshield.app.data.local.entity.CachedAlert

@Dao
interface AlertDao {
    @Query("SELECT * FROM cached_alerts WHERE isActive = 1 ORDER BY effectiveAt DESC")
    suspend fun getActiveAlerts(): List<CachedAlert>

    @Query("SELECT * FROM cached_alerts ORDER BY effectiveAt DESC")
    suspend fun getAllAlerts(): List<CachedAlert>

    @Query("SELECT * FROM cached_alerts WHERE id = :id")
    suspend fun getAlertById(id: String): CachedAlert?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAlerts(alerts: List<CachedAlert>)

    @Query("DELETE FROM cached_alerts WHERE cachedAt < :threshold")
    suspend fun deleteExpired(threshold: Long)

    @Query("DELETE FROM cached_alerts")
    suspend fun clearAll()
}
