package com.floodshield.app.ui.screens.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.floodshield.app.data.api.Alert
import com.floodshield.app.data.api.Resource
import com.floodshield.app.data.api.RiskSummary
import com.floodshield.app.data.repository.RiskRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import javax.inject.Inject

data class HomeUiState(
    val riskSummary: RiskSummary? = null,
    val alerts: List<Alert> = emptyList(),
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null,
    val lastUpdated: String? = null,
    val lastUpdatedMinutesAgo: Int = 0,
    val locationGranted: Boolean = false
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val riskRepository: RiskRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(HomeUiState())
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    private var currentLat = 39.9042
    private var currentLng = 116.4074
    private var lastFetchTimestamp = 0L

    init {
        loadData()
    }

    fun loadData() {
        loadRiskSummary()
        loadAlerts()
    }

    fun refresh() {
        _uiState.value = _uiState.value.copy(isRefreshing = true, error = null)
        loadRiskSummary()
        loadAlerts()
    }

    fun updateLocation(lat: Double, lng: Double) {
        currentLat = lat
        currentLng = lng
        _uiState.value = _uiState.value.copy(locationGranted = true)
        loadData()
    }

    fun onLocationPermissionDenied() {
        _uiState.value = _uiState.value.copy(locationGranted = false)
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    private fun loadRiskSummary() {
        viewModelScope.launch {
            riskRepository.getNearbyRisk(currentLat, currentLng).collect { resource ->
                when (resource) {
                    is Resource.Loading -> {
                        _uiState.value = _uiState.value.copy(isLoading = true, error = null)
                    }
                    is Resource.Success -> {
                        lastFetchTimestamp = System.currentTimeMillis()
                        _uiState.value = _uiState.value.copy(
                            riskSummary = resource.data,
                            isLoading = false,
                            isRefreshing = false,
                            lastUpdated = formatTime(lastFetchTimestamp),
                            lastUpdatedMinutesAgo = 0
                        )
                    }
                    is Resource.Error -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            isRefreshing = false,
                            error = resource.message
                        )
                    }
                }
            }
        }
    }

    private fun loadAlerts() {
        viewModelScope.launch {
            riskRepository.getAlerts().collect { resource ->
                when (resource) {
                    is Resource.Success -> {
                        _uiState.value = _uiState.value.copy(alerts = resource.data)
                    }
                    else -> { /* 预警加载失败不影响主界面 */ }
                }
            }
        }
    }

    private fun formatTime(timestamp: Long): String {
        val sdf = SimpleDateFormat("HH:mm:ss", Locale.CHINA)
        return sdf.format(Date(timestamp))
    }
}
