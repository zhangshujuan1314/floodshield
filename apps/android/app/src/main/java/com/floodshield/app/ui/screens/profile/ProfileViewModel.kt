package com.floodshield.app.ui.screens.profile

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

private val Context.profileDataStore by preferencesDataStore(name = "profile_prefs")

data class ProfileUiState(
    val notificationsEnabled: Boolean = true,
    val alertNotifications: Boolean = true,
    val reportUpdates: Boolean = true,
    val language: String = "中文",
    val subscribedAreas: List<String> = listOf("当前区域"),
    val username: String = "用户",
    val isLoggedIn: Boolean = false
)

@HiltViewModel
class ProfileViewModel @Inject constructor(
    @ApplicationContext private val context: Context
) : ViewModel() {

    private val _uiState = MutableStateFlow(ProfileUiState())
    val uiState: StateFlow<ProfileUiState> = _uiState.asStateFlow()

    companion object {
        val KEY_NOTIFICATIONS = booleanPreferencesKey("notifications_enabled")
        val KEY_ALERT_NOTIFICATIONS = booleanPreferencesKey("alert_notifications")
        val KEY_REPORT_UPDATES = booleanPreferencesKey("report_updates")
        val KEY_LANGUAGE = stringPreferencesKey("language")
        val KEY_USERNAME = stringPreferencesKey("username")
    }

    init {
        loadPreferences()
    }

    private fun loadPreferences() {
        viewModelScope.launch {
            context.profileDataStore.data.collect { prefs ->
                _uiState.value = _uiState.value.copy(
                    notificationsEnabled = prefs[KEY_NOTIFICATIONS] ?: true,
                    alertNotifications = prefs[KEY_ALERT_NOTIFICATIONS] ?: true,
                    reportUpdates = prefs[KEY_REPORT_UPDATES] ?: true,
                    language = prefs[KEY_LANGUAGE] ?: "中文",
                    username = prefs[KEY_USERNAME] ?: "用户",
                    isLoggedIn = prefs[KEY_USERNAME] != null
                )
            }
        }
    }

    fun toggleNotifications() {
        viewModelScope.launch {
            context.profileDataStore.edit { prefs ->
                val current = prefs[KEY_NOTIFICATIONS] ?: true
                prefs[KEY_NOTIFICATIONS] = !current
            }
        }
    }

    fun toggleAlertNotifications() {
        viewModelScope.launch {
            context.profileDataStore.edit { prefs ->
                val current = prefs[KEY_ALERT_NOTIFICATIONS] ?: true
                prefs[KEY_ALERT_NOTIFICATIONS] = !current
            }
        }
    }

    fun toggleReportUpdates() {
        viewModelScope.launch {
            context.profileDataStore.edit { prefs ->
                val current = prefs[KEY_REPORT_UPDATES] ?: true
                prefs[KEY_REPORT_UPDATES] = !current
            }
        }
    }

    fun setLanguage(language: String) {
        viewModelScope.launch {
            context.profileDataStore.edit { prefs ->
                prefs[KEY_LANGUAGE] = language
            }
        }
    }

    fun addSubscribedArea(area: String) {
        val current = _uiState.value.subscribedAreas.toMutableList()
        if (!current.contains(area)) {
            current.add(area)
            _uiState.value = _uiState.value.copy(subscribedAreas = current)
        }
    }

    fun removeSubscribedArea(area: String) {
        val current = _uiState.value.subscribedAreas.toMutableList()
        current.remove(area)
        _uiState.value = _uiState.value.copy(subscribedAreas = current)
    }

    fun login(username: String) {
        viewModelScope.launch {
            context.profileDataStore.edit { prefs ->
                prefs[KEY_USERNAME] = username
            }
        }
    }

    fun logout() {
        viewModelScope.launch {
            context.profileDataStore.edit { prefs ->
                prefs.remove(KEY_USERNAME)
            }
        }
    }
}
