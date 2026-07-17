package com.floodshield.app.data

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 持有当前设备位置的状态。
 * LocationService 更新此状态，ViewModels 观察此状态。
 */
@Singleton
class LocationStateHolder @Inject constructor() {

    private val _latitude = MutableStateFlow(39.9042)   // 默认北京
    private val _longitude = MutableStateFlow(116.4074)
    private val _hasRealLocation = MutableStateFlow(false)

    val latitude: StateFlow<Double> = _latitude.asStateFlow()
    val longitude: StateFlow<Double> = _longitude.asStateFlow()
    val hasRealLocation: StateFlow<Boolean> = _hasRealLocation.asStateFlow()

    fun updateLocation(lat: Double, lng: Double) {
        _latitude.value = lat
        _longitude.value = lng
        _hasRealLocation.value = true
    }
}
