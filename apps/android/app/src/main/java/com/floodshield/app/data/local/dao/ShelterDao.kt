package com.floodshield.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.floodshield.app.data.local.entity.CachedShelter

@Dao
interface ShelterDao {
    @Query("SELECT * FROM cached_shelters ORDER BY distanceM ASC")
    suspend fun getAllShelters(): List<CachedShelter>

    @Query("SELECT * FROM cached_shelters WHERE name LIKE '%' || :query || '%' OR address LIKE '%' || :query || '%'")
    suspend fun searchByName(query: String): List<CachedShelter>

    @Query("SELECT * FROM cached_shelters WHERE id = :id")
    suspend fun getShelterById(id: String): CachedShelter?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertShelters(shelters: List<CachedShelter>)

    @Query("DELETE FROM cached_shelters WHERE cachedAt < :threshold")
    suspend fun deleteExpired(threshold: Long)

    @Query("DELETE FROM cached_shelters")
    suspend fun clearAll()
}
