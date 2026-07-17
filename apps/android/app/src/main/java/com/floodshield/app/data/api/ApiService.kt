package com.floodshield.app.data.api

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface ApiService {
    // 风险概览
    @GET("v1/nearby/summary")
    suspend fun getNearbySummary(
        @Query("lat") lat: Double,
        @Query("lon") lon: Double,
        @Query("radiusM") radiusM: Int = 5000
    ): ApiResponse<RiskSummary>

    // 预警
    @GET("v1/alerts")
    suspend fun getAlerts(
        @Query("activeOnly") activeOnly: Boolean = true
    ): ApiResponse<List<Alert>>

    // 避难所
    @GET("v1/shelters/nearby")
    suspend fun getNearbyShelters(
        @Query("lat") lat: Double,
        @Query("lon") lon: Double,
        @Query("radiusM") radiusM: Int = 5000
    ): ApiResponse<List<Shelter>>

    // 险情上报
    @POST("v1/hazard-reports")
    suspend fun submitReport(@Body report: CreateReportRequest): ApiResponse<Report>

    @GET("v1/hazard-reports/{id}")
    suspend fun getReport(@Path("id") id: String): ApiResponse<Report>

    // 撤离路线
    @POST("v1/routes/evacuation")
    suspend fun requestRoute(@Body request: RouteRequest): ApiResponse<RouteResponse>

    // 认证
    @POST("v1/auth/login")
    suspend fun login(@Body request: LoginRequest): ApiResponse<LoginResponse>

    // 语音播报
    @POST("v1/voice/announcement")
    suspend fun getVoiceScript(@Body request: VoiceRequest): ApiResponse<VoiceResponse>
}
