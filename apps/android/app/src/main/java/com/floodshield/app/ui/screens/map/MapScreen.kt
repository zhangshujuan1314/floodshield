package com.floodshield.app.ui.screens.map

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.MyLocation
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import com.floodshield.app.data.api.Shelter
import com.floodshield.app.ui.components.SmallRiskBadge
import com.google.android.gms.location.LocationServices
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.MapView
import com.google.android.gms.maps.model.BitmapDescriptorFactory
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.MarkerOptions

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MapScreen(
    viewModel: MapViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val context = LocalContext.current
    var googleMap by remember { mutableStateOf<GoogleMap?>(null) }
    val showBottomSheet = uiState.selectedShelter != null
    val sheetState = rememberModalBottomSheetState()

    val locationPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            val fusedClient = LocationServices.getFusedLocationProviderClient(context)
            try {
                fusedClient.lastLocation.addOnSuccessListener { location ->
                    if (location != null) {
                        viewModel.updateLocation(location.latitude, location.longitude)
                    }
                }
            } catch (_: SecurityException) {}
        } else {
            viewModel.loadData()
        }
    }

    LaunchedEffect(Unit) {
        val hasPermission = ContextCompat.checkSelfPermission(
            context, Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED

        if (hasPermission) {
            val fusedClient = LocationServices.getFusedLocationProviderClient(context)
            try {
                fusedClient.lastLocation.addOnSuccessListener { location ->
                    if (location != null) {
                        viewModel.updateLocation(location.latitude, location.longitude)
                    } else {
                        viewModel.loadData()
                    }
                }
            } catch (_: SecurityException) {
                viewModel.loadData()
            }
        } else {
            locationPermissionLauncher.launch(Manifest.permission.ACCESS_FINE_LOCATION)
        }
    }

    // Update map markers when data changes
    LaunchedEffect(uiState.shelters, uiState.activeLayers) {
        val map = googleMap ?: return@LaunchedEffect
        map.clear()

        if (uiState.activeLayers.contains(MapLayer.SHELTERS)) {
            uiState.shelters.forEach { shelter ->
                val pos = LatLng(shelter.location.lat, shelter.location.lng)
                map.addMarker(
                    MarkerOptions()
                        .position(pos)
                        .title(shelter.name)
                        .snippet(shelter.address)
                        .icon(BitmapDescriptorFactory.defaultMarker(BitmapDescriptorFactory.HUE_AZURE))
                )
            }
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        // Map
        AndroidView(
            factory = { ctx ->
                MapView(ctx).apply {
                    onCreate(null)
                    getMapAsync { map ->
                        googleMap = map
                        uiState.currentLocation?.let { loc ->
                            map.moveCamera(CameraUpdateFactory.newLatLngZoom(loc, 12f))
                        }
                        map.setOnMarkerClickListener { marker ->
                            val shelter = uiState.shelters.find {
                                it.location.lat == marker.position.latitude &&
                                    it.location.lng == marker.position.longitude
                            }
                            shelter?.let { viewModel.selectShelter(it) }
                            true
                        }
                        map.setOnMapClickListener {
                            viewModel.clearSelection()
                        }
                    }
                }
            },
            update = { mapView ->
                mapView.onResume()
            },
            modifier = Modifier.fillMaxSize()
        )

        // Layer toggles
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            MapLayer.entries.forEach { layer ->
                FilterChip(
                    selected = uiState.activeLayers.contains(layer),
                    onClick = { viewModel.toggleLayer(layer) },
                    label = { Text(layer.label, style = MaterialTheme.typography.labelSmall) }
                )
            }
        }

        // Risk summary overlay
        uiState.riskSummary?.let { risk ->
            Card(
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(start = 8.dp, top = 48.dp)
                    .width(180.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.9f)
                )
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "区域风险",
                            style = MaterialTheme.typography.labelMedium,
                            modifier = Modifier.weight(1f)
                        )
                        SmallRiskBadge(level = risk.platformRiskBand)
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "评分: ${String.format("%.1f", risk.riskScore)}",
                        style = MaterialTheme.typography.bodySmall
                    )
                    Text(
                        text = "置信度: ${String.format("%.0f%%", risk.confidence * 100)}",
                        style = MaterialTheme.typography.bodySmall
                    )
                    if (risk.roadClosures.isNotEmpty()) {
                        Text(
                            text = "道路封闭: ${risk.roadClosures.size}处",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.error
                        )
                    }
                }
            }
        }

        // My location FAB
        FloatingActionButton(
            onClick = {
                uiState.currentLocation?.let { loc ->
                    googleMap?.animateCamera(CameraUpdateFactory.newLatLngZoom(loc, 14f))
                }
            },
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(16.dp)
        ) {
            Icon(Icons.Default.MyLocation, contentDescription = "我的位置")
        }

        // Loading indicator
        if (uiState.isLoading) {
            CircularProgressIndicator(
                modifier = Modifier.align(Alignment.Center)
            )
        }

        // Error text
        uiState.error?.let { error ->
            Text(
                text = error,
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(bottom = 80.dp)
            )
        }
    }

    // Bottom sheet for selected shelter
    if (showBottomSheet) {
        ModalBottomSheet(
            onDismissRequest = { viewModel.clearSelection() },
            sheetState = sheetState
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp)
            ) {
                uiState.selectedShelter?.let { shelter ->
                    ShelterDetailSheet(shelter)
                }
                Spacer(modifier = Modifier.height(32.dp))
            }
        }
    }
}

@Composable
private fun ShelterDetailSheet(shelter: Shelter) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = shelter.name,
                style = MaterialTheme.typography.titleMedium
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = shelter.address,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row {
                Text(
                    text = "容量: ${shelter.currentOccupancy}/${shelter.capacity}",
                    style = MaterialTheme.typography.bodySmall
                )
                Spacer(modifier = Modifier.width(16.dp))
                Text(
                    text = "状态: ${shelter.status}",
                    style = MaterialTheme.typography.bodySmall
                )
            }
            if (shelter.facilities.isNotEmpty()) {
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "设施: ${shelter.facilities.joinToString("、")}",
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }
    }
}
