package com.floodshield.app.util

object Constants {
    // API 相关
    const val API_TIMEOUT = 30L // 秒

    // 位置相关
    const val LOCATION_UPDATE_INTERVAL = 10000L // 10秒
    const val LOCATION_FASTEST_INTERVAL = 5000L // 5秒
    const val DEFAULT_RADIUS_M = 5000           // 米

    // 风险等级
    const val RISK_BAND_LOW = "low"
    const val RISK_BAND_MODERATE = "moderate"
    const val RISK_BAND_HIGH = "high"
    const val RISK_BAND_CRITICAL = "critical"

    // 通知渠道
    const val CHANNEL_ALERTS = "flood_alerts"
    const val CHANNEL_LOCATION = "location_channel"
    const val CHANNEL_GEOFENCE = "geofence_alerts"
    const val CHANNEL_GENERAL = "general_notifications"

    // DataStore
    const val PREFERENCES_NAME = "floodshield_prefs"
    const val KEY_TOKEN = "auth_token"
    const val KEY_USER_ID = "user_id"
    const val KEY_LATITUDE = "last_latitude"
    const val KEY_LONGITUDE = "last_longitude"
}
