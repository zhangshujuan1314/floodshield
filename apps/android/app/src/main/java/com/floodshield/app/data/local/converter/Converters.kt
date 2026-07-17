package com.floodshield.app.data.local.converter

import androidx.room.TypeConverter
import com.floodshield.app.data.api.AlertSummary
import com.floodshield.app.data.api.RiskSignal
import com.floodshield.app.data.api.RoadClosure
import com.floodshield.app.data.api.ShelterSummary
import com.squareup.moshi.Moshi
import com.squareup.moshi.Types
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory

/**
 * Room TypeConverters，用于在 JSON 字符串和复杂类型之间转换。
 */
class Converters {

    companion object {
        private val moshi = Moshi.Builder()
            .add(KotlinJsonAdapterFactory())
            .build()

        private val stringListAdapter = moshi.adapter<List<String>>(
            Types.newParameterizedType(List::class.java, String::class.java)
        )

        private val riskSignalListAdapter = moshi.adapter<List<RiskSignal>>(
            Types.newParameterizedType(List::class.java, RiskSignal::class.java)
        )

        private val alertSummaryListAdapter = moshi.adapter<List<AlertSummary>>(
            Types.newParameterizedType(List::class.java, AlertSummary::class.java)
        )

        private val shelterSummaryListAdapter = moshi.adapter<List<ShelterSummary>>(
            Types.newParameterizedType(List::class.java, ShelterSummary::class.java)
        )

        private val roadClosureListAdapter = moshi.adapter<List<RoadClosure>>(
            Types.newParameterizedType(List::class.java, RoadClosure::class.java)
        )
    }

    @TypeConverter
    fun fromStringList(value: List<String>): String = stringListAdapter.toJson(value)

    @TypeConverter
    fun toStringList(value: String): List<String> =
        stringListAdapter.fromJson(value) ?: emptyList()

    @TypeConverter
    fun fromRiskSignalList(value: List<RiskSignal>): String = riskSignalListAdapter.toJson(value)

    @TypeConverter
    fun toRiskSignalList(value: String): List<RiskSignal> =
        riskSignalListAdapter.fromJson(value) ?: emptyList()

    @TypeConverter
    fun fromAlertSummaryList(value: List<AlertSummary>): String = alertSummaryListAdapter.toJson(value)

    @TypeConverter
    fun toAlertSummaryList(value: String): List<AlertSummary> =
        alertSummaryListAdapter.fromJson(value) ?: emptyList()

    @TypeConverter
    fun fromShelterSummaryList(value: List<ShelterSummary>): String = shelterSummaryListAdapter.toJson(value)

    @TypeConverter
    fun toShelterSummaryList(value: String): List<ShelterSummary> =
        shelterSummaryListAdapter.fromJson(value) ?: emptyList()

    @TypeConverter
    fun fromRoadClosureList(value: List<RoadClosure>): String = roadClosureListAdapter.toJson(value)

    @TypeConverter
    fun toRoadClosureList(value: String): List<RoadClosure> =
        roadClosureListAdapter.fromJson(value) ?: emptyList()
}
