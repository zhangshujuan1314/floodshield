package com.floodshield.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "cached_alerts")
data class CachedAlert(
    @PrimaryKey val id: String,
    val source: String,
    val alertType: String,
    val severity: String,
    val title: String,
    val description: String,
    val effectiveAt: String,
    val expiresAt: String?,
    val isActive: Boolean,
    val cachedAt: Long = System.currentTimeMillis()
)
