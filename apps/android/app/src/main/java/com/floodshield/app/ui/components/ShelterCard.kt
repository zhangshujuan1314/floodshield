package com.floodshield.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Accessible
import androidx.compose.material.icons.filled.ChildCare
import androidx.compose.material.icons.filled.DirectionsWalk
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Navigation
import androidx.compose.material.icons.filled.Pets
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.floodshield.app.ui.theme.FloodShieldTheme

data class ShelterData(
    val id: String,
    val name: String,
    val address: String,
    val capacity: Int,
    val currentOccupancy: Int,
    val distance: String,
    val status: String = "开放",           // 开放/关闭/即将满员
    val accessible: Boolean = false,
    val childFriendly: Boolean = false,
    val petFriendly: Boolean = false
)

@Composable
fun ShelterCard(
    shelter: ShelterData,
    modifier: Modifier = Modifier,
    onNavigate: (() -> Unit)? = null
) {
    val occupancyRatio = if (shelter.capacity > 0) {
        shelter.currentOccupancy.toFloat() / shelter.capacity
    } else 0f

    Card(
        modifier = modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Name + status badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = shelter.name,
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.weight(1f)
                )
                StatusBadge(status = shelter.status)
            }

            Spacer(modifier = Modifier.height(4.dp))

            // Address + distance
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Default.LocationOn,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(16.dp)
                )
                Spacer(modifier = Modifier.width(4.dp))
                Text(
                    text = shelter.address,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.weight(1f)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = shelter.distance,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.primary
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Capacity bar
            Text(
                text = "容纳人数: ${shelter.currentOccupancy} / ${shelter.capacity}",
                style = MaterialTheme.typography.bodySmall
            )
            Spacer(modifier = Modifier.height(4.dp))
            LinearProgressIndicator(
                progress = { occupancyRatio.coerceIn(0f, 1f) },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(8.dp)
                    .clip(RoundedCornerShape(4.dp)),
                color = when {
                    occupancyRatio >= 0.9f -> Color(0xFFD32F2F)
                    occupancyRatio >= 0.7f -> Color(0xFFFF8F00)
                    else -> Color(0xFF388E3C)
                },
                trackColor = MaterialTheme.colorScheme.surfaceVariant,
            )

            // Accessibility icons
            if (shelter.accessible || shelter.childFriendly || shelter.petFriendly) {
                Spacer(modifier = Modifier.height(12.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    if (shelter.accessible) {
                        AccessibilityIcon(
                            icon = Icons.Default.Accessible,
                            label = "无障碍"
                        )
                    }
                    if (shelter.childFriendly) {
                        AccessibilityIcon(
                            icon = Icons.Default.ChildCare,
                            label = "儿童友好"
                        )
                    }
                    if (shelter.petFriendly) {
                        AccessibilityIcon(
                            icon = Icons.Default.Pets,
                            label = "允许宠物"
                        )
                    }
                }
            }

            // Navigate button
            if (onNavigate != null) {
                Spacer(modifier = Modifier.height(12.dp))
                Button(
                    onClick = onNavigate,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(
                        imageVector = Icons.Default.Navigation,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("导航")
                }
            }
        }
    }
}

@Composable
private fun StatusBadge(status: String) {
    val (bgColor, textColor) = when (status) {
        "开放" -> Color(0xFF388E3C) to Color.White
        "即将满员" -> Color(0xFFFF8F00) to Color.White
        "关闭" -> Color(0xFF757575) to Color.White
        else -> MaterialTheme.colorScheme.surfaceVariant to MaterialTheme.colorScheme.onSurfaceVariant
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(12.dp))
            .background(bgColor)
            .padding(horizontal = 10.dp, vertical = 4.dp)
    ) {
        Text(
            text = status,
            color = textColor,
            style = MaterialTheme.typography.labelSmall
        )
    }
}

@Composable
private fun AccessibilityIcon(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Icon(
            imageVector = icon,
            contentDescription = label,
            tint = MaterialTheme.colorScheme.primary,
            modifier = Modifier.size(20.dp)
        )
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

// ── Previews ──

@Preview(name = "ShelterCard - Open")
@Composable
private fun ShelterCardOpenPreview() {
    FloodShieldTheme {
        ShelterCard(
            shelter = ShelterData(
                id = "1",
                name = "市第一中学避难所",
                address = "和平路100号",
                capacity = 500,
                currentOccupancy = 320,
                distance = "1.2km",
                status = "开放",
                accessible = true,
                childFriendly = true,
                petFriendly = false
            ),
            onNavigate = {}
        )
    }
}

@Preview(name = "ShelterCard - Almost Full")
@Composable
private fun ShelterCardAlmostFullPreview() {
    FloodShieldTheme {
        ShelterCard(
            shelter = ShelterData(
                id = "2",
                name = "体育馆临时安置点",
                address = "体育路88号",
                capacity = 200,
                currentOccupancy = 185,
                distance = "2.5km",
                status = "即将满员",
                accessible = true,
                childFriendly = false,
                petFriendly = true
            ),
            onNavigate = {}
        )
    }
}

@Preview(name = "ShelterCard - Closed")
@Composable
private fun ShelterCardClosedPreview() {
    FloodShieldTheme {
        ShelterCard(
            shelter = ShelterData(
                id = "3",
                name = "社区活动中心",
                address = "中心街12号",
                capacity = 100,
                currentOccupancy = 0,
                distance = "0.8km",
                status = "关闭"
            )
        )
    }
}
