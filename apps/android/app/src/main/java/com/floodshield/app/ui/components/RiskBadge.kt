package com.floodshield.app.ui.components

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CrisisAlert
import androidx.compose.material.icons.filled.HelpOutline
import androidx.compose.material.icons.filled.PriorityHigh
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import com.floodshield.app.ui.theme.RiskAttention
import com.floodshield.app.ui.theme.RiskCritical
import com.floodshield.app.ui.theme.RiskHigh
import com.floodshield.app.ui.theme.RiskNormal
import com.floodshield.app.ui.theme.RiskUnknown

enum class RiskLevel(val apiValue: String, val label: String, val color: Color) {
    NORMAL("normal", "当前正常", RiskNormal),
    ATTENTION("attention", "需要关注", RiskAttention),
    HIGH("high", "高风险", RiskHigh),
    CRITICAL("critical", "立即避险", RiskCritical),
    UNKNOWN("unknown", "数据不足", RiskUnknown);

    companion object {
        fun fromApi(value: String): RiskLevel =
            entries.find { it.apiValue == value } ?: UNKNOWN
    }
}

@Composable
fun RiskBadge(
    level: String,
    modifier: Modifier = Modifier
) {
    val riskLevel = RiskLevel.fromApi(level)
    val config = riskConfigForLevel(riskLevel)

    Box(
        contentAlignment = Alignment.Center,
        modifier = modifier.size(120.dp)
    ) {
        if (riskLevel == RiskLevel.CRITICAL) {
            PulseRing(color = config.color)
        }

        Canvas(modifier = Modifier.size(110.dp)) {
            drawCircle(color = config.color)
        }

        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = config.icon,
                contentDescription = riskLevel.label,
                tint = Color.White,
                modifier = Modifier.size(40.dp)
            )
            Text(
                text = riskLevel.label,
                color = Color.White,
                style = MaterialTheme.typography.labelLarge
            )
        }
    }
}

@Composable
fun SmallRiskBadge(
    level: String,
    modifier: Modifier = Modifier
) {
    val riskLevel = RiskLevel.fromApi(level)
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(4.dp))
            .background(riskLevel.color)
            .padding(horizontal = 8.dp, vertical = 4.dp)
    ) {
        Text(
            text = riskLevel.label,
            color = Color.White,
            style = MaterialTheme.typography.labelSmall
        )
    }
}

@Composable
private fun PulseRing(color: Color) {
    val transition = rememberInfiniteTransition(label = "pulse")
    val alpha by transition.animateFloat(
        initialValue = 0.6f,
        targetValue = 0f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 1000),
            repeatMode = RepeatMode.Restart
        ),
        label = "pulseAlpha"
    )
    val scale by transition.animateFloat(
        initialValue = 0.9f,
        targetValue = 1.3f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 1000),
            repeatMode = RepeatMode.Restart
        ),
        label = "pulseScale"
    )

    Canvas(
        modifier = Modifier
            .size(120.dp)
            .alpha(alpha)
    ) {
        drawCircle(
            color = color,
            radius = size.minDimension / 2 * scale
        )
    }
}

private data class RiskConfig(
    val color: Color,
    val icon: ImageVector
)

private fun riskConfigForLevel(level: RiskLevel): RiskConfig = when (level) {
    RiskLevel.NORMAL -> RiskConfig(RiskNormal, Icons.Filled.CheckCircle)
    RiskLevel.ATTENTION -> RiskConfig(RiskAttention, Icons.Filled.Warning)
    RiskLevel.HIGH -> RiskConfig(RiskHigh, Icons.Filled.PriorityHigh)
    RiskLevel.CRITICAL -> RiskConfig(RiskCritical, Icons.Filled.CrisisAlert)
    RiskLevel.UNKNOWN -> RiskConfig(RiskUnknown, Icons.Filled.HelpOutline)
}
