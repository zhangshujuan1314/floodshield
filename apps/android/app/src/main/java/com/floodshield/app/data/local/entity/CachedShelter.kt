package com.floodshield.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "cached_shelters")
data class CachedShelter(
    @PrimaryKey val id: String,
    val name: String,
    val address: String,
    val distanceM: Int,
    val capacity: Int,
    val currentOccupancy: Int,
    val status: String,
    val facilitiesJson: String,
    val lat: Double,
    val lng: Double,
    val cachedAt: Long = System.currentTimeMillis()
)
