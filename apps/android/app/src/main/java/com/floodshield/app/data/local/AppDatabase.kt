package com.floodshield.app.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.floodshield.app.data.local.converter.Converters
import com.floodshield.app.data.local.dao.AlertDao
import com.floodshield.app.data.local.dao.RiskDao
import com.floodshield.app.data.local.dao.ShelterDao
import com.floodshield.app.data.local.entity.CachedAlert
import com.floodshield.app.data.local.entity.CachedRisk
import com.floodshield.app.data.local.entity.CachedShelter

@Database(
    entities = [
        CachedRisk::class,
        CachedShelter::class,
        CachedAlert::class
    ],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun riskDao(): RiskDao
    abstract fun shelterDao(): ShelterDao
    abstract fun alertDao(): AlertDao
}
