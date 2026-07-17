package com.floodshield.app.data.api

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

// ── API Response Wrapper ──

@JsonClass(generateAdapter = true)
data class ApiResponse<T>(
    @Json(name = "requestId") val requestId: String?,
    @Json(name = "dataStatus") val dataStatus: String,
    @Json(name = "timestamp") val timestamp: String?,
    @Json(name = "data") val data: T?
)

// ── Risk ──

@JsonClass(generateAdapter = true)
data class RiskSummary(
    @Json(name = "areaId") val areaId: String,
    @Json(name = "platformRiskBand") val platformRiskBand: String,
    @Json(name = "riskScore") val riskScore: Double,
    @Json(name = "confidence") val confidence: Double,
    @Json(name = "signals") val signals: List<RiskSignal>,
    @Json(name = "activeAlerts") val activeAlerts: List<AlertSummary>,
    @Json(name = "nearbyShelters") val nearbyShelters: List<ShelterSummary>,
    @Json(name = "roadClosures") val roadClosures: List<RoadClosure>,
    @Json(name = "actions") val actions: List<String>
)

@JsonClass(generateAdapter = true)
data class RiskSignal(
    @Json(name = "type") val type: String,
    @Json(name = "value") val value: Double,
    @Json(name = "unit") val unit: String?
)

@JsonClass(generateAdapter = true)
data class AlertSummary(
    @Json(name = "id") val id: String,
    @Json(name = "title") val title: String,
    @Json(name = "severity") val severity: String
)

@JsonClass(generateAdapter = true)
data class ShelterSummary(
    @Json(name = "id") val id: String,
    @Json(name = "name") val name: String,
    @Json(name = "distanceM") val distanceM: Int
)

@JsonClass(generateAdapter = true)
data class RoadClosure(
    @Json(name = "roadName") val roadName: String,
    @Json(name = "reason") val reason: String
)

// ── Alert ──

@JsonClass(generateAdapter = true)
data class Alert(
    @Json(name = "id") val id: String,
    @Json(name = "source") val source: String,
    @Json(name = "alertType") val alertType: String,
    @Json(name = "severity") val severity: String,
    @Json(name = "title") val title: String,
    @Json(name = "description") val description: String,
    @Json(name = "effectiveAt") val effectiveAt: String,
    @Json(name = "expiresAt") val expiresAt: String?,
    @Json(name = "isActive") val isActive: Boolean
)

// ── Shelter ──

@JsonClass(generateAdapter = true)
data class Shelter(
    @Json(name = "id") val id: String,
    @Json(name = "name") val name: String,
    @Json(name = "address") val address: String,
    @Json(name = "distanceM") val distanceM: Int,
    @Json(name = "capacity") val capacity: Int,
    @Json(name = "currentOccupancy") val currentOccupancy: Int,
    @Json(name = "status") val status: String,
    @Json(name = "facilities") val facilities: List<String>,
    @Json(name = "location") val location: Location
)

// ── Location ──

@JsonClass(generateAdapter = true)
data class Location(
    @Json(name = "lat") val lat: Double,
    @Json(name = "lng") val lng: Double
)

// ── Report ──

@JsonClass(generateAdapter = true)
data class CreateReportRequest(
    @Json(name = "reportType") val reportType: String,
    @Json(name = "severity") val severity: String,
    @Json(name = "description") val description: String,
    @Json(name = "location") val location: Location,
    @Json(name = "photoUrl") val photoUrl: String?
)

@JsonClass(generateAdapter = true)
data class Report(
    @Json(name = "id") val id: String,
    @Json(name = "reportType") val reportType: String,
    @Json(name = "severity") val severity: String,
    @Json(name = "description") val description: String,
    @Json(name = "location") val location: Location,
    @Json(name = "status") val status: String,
    @Json(name = "createdAt") val createdAt: String
)

// ── Route ──

@JsonClass(generateAdapter = true)
data class RouteRequest(
    @Json(name = "fromLat") val fromLat: Double,
    @Json(name = "fromLng") val fromLng: Double,
    @Json(name = "toLat") val toLat: Double,
    @Json(name = "toLng") val toLng: Double
)

@JsonClass(generateAdapter = true)
data class RouteResponse(
    @Json(name = "routeId") val routeId: String,
    @Json(name = "routeGeojson") val routeGeojson: String,
    @Json(name = "distanceM") val distanceM: Int,
    @Json(name = "durationS") val durationS: Int,
    @Json(name = "safetyScore") val safetyScore: Double,
    @Json(name = "warnings") val warnings: List<String>
)

// ── Auth ──

@JsonClass(generateAdapter = true)
data class LoginRequest(
    @Json(name = "username") val username: String,
    @Json(name = "password") val password: String
)

@JsonClass(generateAdapter = true)
data class LoginResponse(
    @Json(name = "token") val token: String,
    @Json(name = "user") val user: UserData
)

@JsonClass(generateAdapter = true)
data class UserData(
    @Json(name = "id") val id: String,
    @Json(name = "username") val username: String,
    @Json(name = "phone") val phone: String?
)

// ── Voice ──

@JsonClass(generateAdapter = true)
data class VoiceRequest(
    @Json(name = "text") val text: String,
    @Json(name = "language") val language: String = "zh-CN"
)

@JsonClass(generateAdapter = true)
data class VoiceResponse(
    @Json(name = "audioUrl") val audioUrl: String,
    @Json(name = "duration") val duration: Int?
)
