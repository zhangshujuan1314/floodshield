package com.floodshield.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "cached_risks")
data class CachedRisk(
    @PrimaryKey val areaId: String,
    val platformRiskBand: String,
    val riskScore: Double,
    val confidence: Double,
    val signalsJson: String,
    val activeAlertsJson: String,
    val nearbySheltersJson: String,
    val roadClosuresJson: String,
    val actionsJson: String,
    val cachedAt: Long = System.currentTimeMillis()
)
