package com.floodshield.app.ui.screens.map

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.floodshield.app.data.api.Resource
import com.floodshield.app.data.api.RiskSummary
import com.floodshield.app.data.api.Shelter
import com.floodshield.app.data.repository.RiskRepository
import com.floodshield.app.data.repository.ShelterRepository
import com.google.android.gms.maps.model.LatLng
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

enum class MapLayer(val label: String) {
    RISK_ZONES("风险区域"),
    REPORTS("险情上报"),
    SHELTERS("避险场所"),
    ROAD_CLOSURES("道路封闭")
}

data class MapUiState(
    val riskSummary: RiskSummary? = null,
    val shelters: List<Shelter> = emptyList(),
    val activeLayers: Set<MapLayer> = setOf(MapLayer.RISK_ZONES, MapLayer.SHELTERS),
    val selectedShelter: Shelter? = null,
    val isLoading: Boolean = false,
    val error: String? = null,
    val currentLocation: LatLng? = null
)

@HiltViewModel
class MapViewModel @Inject constructor(
    private val riskRepository: RiskRepository,
    private val shelterRepository: ShelterRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(MapUiState())
    val uiState: StateFlow<MapUiState> = _uiState.asStateFlow()

    private var currentLat = 39.9042
    private var currentLng = 116.4074

    fun loadData(lat: Double = currentLat, lng: Double = currentLng) {
        currentLat = lat
        currentLng = lng
        _uiState.value = _uiState.value.copy(
            isLoading = true,
            currentLocation = LatLng(lat, lng)
        )

        loadRiskSummary()
        loadShelters()
    }

    fun toggleLayer(layer: MapLayer) {
        val current = _uiState.value.activeLayers.toMutableSet()
        if (current.contains(layer)) current.remove(layer) else current.add(layer)
        _uiState.value = _uiState.value.copy(activeLayers = current)
    }

    fun selectShelter(shelter: Shelter?) {
        _uiState.value = _uiState.value.copy(selectedShelter = shelter)
    }

    fun clearSelection() {
        _uiState.value = _uiState.value.copy(selectedShelter = null)
    }

    fun updateLocation(lat: Double, lng: Double) {
        currentLat = lat
        currentLng = lng
        _uiState.value = _uiState.value.copy(currentLocation = LatLng(lat, lng))
        loadData(lat, lng)
    }

    private fun loadRiskSummary() {
        viewModelScope.launch {
            riskRepository.getNearbyRisk(currentLat, currentLng).collect { resource ->
                when (resource) {
                    is Resource.Success -> {
                        _uiState.value = _uiState.value.copy(
                            riskSummary = resource.data,
                            isLoading = false
                        )
                    }
                    is Resource.Error -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = resource.message
                        )
                    }
                    is Resource.Loading -> { /* 已在 loadData 中设置 */ }
                }
            }
        }
    }

    private fun loadShelters() {
        viewModelScope.launch {
            shelterRepository.getNearbyShelters(currentLat, currentLng).collect { resource ->
                when (resource) {
                    is Resource.Success -> {
                        _uiState.value = _uiState.value.copy(shelters = resource.data)
                    }
                    is Resource.Error -> {
                        _uiState.value = _uiState.value.copy(error = resource.message)
                    }
                    is Resource.Loading -> { /* no-op */ }
                }
            }
        }
    }
}
