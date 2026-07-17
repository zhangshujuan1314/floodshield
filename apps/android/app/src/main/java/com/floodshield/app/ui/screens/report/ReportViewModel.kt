package com.floodshield.app.ui.screens.report

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.floodshield.app.data.api.CreateReportRequest
import com.floodshield.app.data.api.Location
import com.floodshield.app.data.api.Report
import com.floodshield.app.data.api.Resource
import com.floodshield.app.data.repository.ReportRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

enum class ReportType(val label: String, val apiValue: String) {
    WATERLOGGING("积水", "waterlogging"),
    ROAD_BLOCK("道路中断", "road_block"),
    MANHOLE_DAMAGED("井盖破损", "manhole_damaged"),
    PEOPLE_TRAPPED("人员受困", "people_trapped")
}

enum class Severity(val label: String, val apiValue: String) {
    LOW("轻微", "low"),
    MEDIUM("中等", "medium"),
    HIGH("严重", "high")
}

data class ReportUiState(
    val selectedType: ReportType? = null,
    val selectedSeverity: Severity = Severity.MEDIUM,
    val description: String = "",
    val photoUri: Uri? = null,
    val latitude: Double = 39.9042,
    val longitude: Double = 116.4074,
    val isSubmitting: Boolean = false,
    val submitSuccess: Boolean = false,
    val reportId: String? = null,
    val error: String? = null
)

@HiltViewModel
class ReportViewModel @Inject constructor(
    private val reportRepository: ReportRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ReportUiState())
    val uiState: StateFlow<ReportUiState> = _uiState.asStateFlow()

    fun selectType(type: ReportType) {
        _uiState.value = _uiState.value.copy(selectedType = type)
    }

    fun selectSeverity(severity: Severity) {
        _uiState.value = _uiState.value.copy(selectedSeverity = severity)
    }

    fun updateDescription(text: String) {
        _uiState.value = _uiState.value.copy(description = text)
    }

    fun setPhotoUri(uri: Uri?) {
        _uiState.value = _uiState.value.copy(photoUri = uri)
    }

    fun updateLocation(lat: Double, lng: Double) {
        _uiState.value = _uiState.value.copy(latitude = lat, longitude = lng)
    }

    fun submitReport() {
        val state = _uiState.value
        if (state.selectedType == null) {
            _uiState.value = state.copy(error = "请选择险情类型")
            return
        }
        if (state.description.isBlank()) {
            _uiState.value = state.copy(error = "请填写险情描述")
            return
        }

        val request = CreateReportRequest(
            reportType = state.selectedType.apiValue,
            severity = state.selectedSeverity.apiValue,
            description = state.description,
            location = Location(lat = state.latitude, lng = state.longitude),
            photoUrl = state.photoUri?.toString()
        )

        viewModelScope.launch {
            reportRepository.submitReport(request).collect { resource ->
                when (resource) {
                    is Resource.Loading -> {
                        _uiState.value = _uiState.value.copy(isSubmitting = true, error = null)
                    }
                    is Resource.Success -> {
                        _uiState.value = _uiState.value.copy(
                            isSubmitting = false,
                            submitSuccess = true,
                            reportId = resource.data.id
                        )
                    }
                    is Resource.Error -> {
                        _uiState.value = _uiState.value.copy(
                            isSubmitting = false,
                            error = resource.message
                        )
                    }
                }
            }
        }
    }

    fun resetForm() {
        _uiState.value = ReportUiState()
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    fun dismissSuccess() {
        _uiState.value = _uiState.value.copy(submitSuccess = false, reportId = null)
    }
}
