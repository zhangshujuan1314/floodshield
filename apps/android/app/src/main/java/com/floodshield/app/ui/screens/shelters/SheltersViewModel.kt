package com.floodshield.app.ui.screens.shelters

import android.location.Location
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.floodshield.app.data.api.Resource
import com.floodshield.app.data.api.Shelter
import com.floodshield.app.data.repository.ShelterRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ShelterWithDistance(
    val shelter: Shelter,
    val distanceMeters: Float
)

data class SheltersUiState(
    val shelters: List<ShelterWithDistance> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val filterAccessible: Boolean = false,
    val currentLat: Double = 39.9042,
    val currentLng: Double = 116.4074
)

@HiltViewModel
class SheltersViewModel @Inject constructor(
    private val shelterRepository: ShelterRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(SheltersUiState())
    val uiState: StateFlow<SheltersUiState> = _uiState.asStateFlow()

    init {
        loadShelters()
    }

    fun loadShelters() {
        val lat = _uiState.value.currentLat
        val lng = _uiState.value.currentLng

        viewModelScope.launch {
            shelterRepository.getNearbyShelters(lat, lng).collect { resource ->
                when (resource) {
                    is Resource.Loading -> {
                        _uiState.value = _uiState.value.copy(isLoading = true, error = null)
                    }
                    is Resource.Success -> {
                        val withDistance = resource.data.map { shelter ->
                            val results = FloatArray(1)
                            Location.distanceBetween(
                                lat, lng,
                                shelter.location.lat, shelter.location.lng,
                                results
                            )
                            ShelterWithDistance(shelter, results[0])
                        }.sortedBy { it.distanceMeters }

                        _uiState.value = _uiState.value.copy(
                            shelters = withDistance,
                            isLoading = false
                        )
                    }
                    is Resource.Error -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = resource.message
                        )
                    }
                }
            }
        }
    }

    fun updateLocation(lat: Double, lng: Double) {
        _uiState.value = _uiState.value.copy(currentLat = lat, currentLng = lng)
        loadShelters()
    }

    fun toggleAccessibleFilter() {
        _uiState.value = _uiState.value.copy(
            filterAccessible = !_uiState.value.filterAccessible
        )
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    fun getFilteredShelters(): List<ShelterWithDistance> {
        val state = _uiState.value
        return if (state.filterAccessible) {
            state.shelters.filter {
                it.shelter.name.contains("无障碍") ||
                    it.shelter.name.contains("轮椅") ||
                    it.shelter.address.contains("无障碍") ||
                    it.shelter.address.contains("轮椅") ||
                    it.shelter.facilities.any { f -> f.contains("无障碍") }
            }
        } else {
            state.shelters
        }
    }

    fun formatDistance(meters: Float): String {
        return if (meters < 1000) {
            "${meters.toInt()}米"
        } else {
            String.format(java.util.Locale.CHINA, "%.1f公里", meters / 1000)
        }
    }
}
