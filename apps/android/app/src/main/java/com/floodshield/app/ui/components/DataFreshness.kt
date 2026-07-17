package com.floodshield.app.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.floodshield.app.ui.theme.FloodShieldTheme

/**
 * 数据新鲜度指示器。
 *
 * @param minutesAgo 距上次更新的分钟数
 */
@Composable
fun DataFreshness(
    minutesAgo: Int,
    modifier: Modifier = Modifier
) {
    val color = freshnessColor(minutesAgo)
    val label = freshnessLabel(minutesAgo)

    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Canvas(modifier = Modifier.size(10.dp)) {
            drawCircle(color = color)
        }
        Spacer(modifier = Modifier.width(6.dp))
        Text(
            text = "数据更新于 $label",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

/**
 * Variant accepting a pre-formatted string (backward compatible).
 */
@Composable
fun DataFreshness(
    lastUpdated: String,
    minutesAgo: Int,
    modifier: Modifier = Modifier
) {
    val color = freshnessColor(minutesAgo)

    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Canvas(modifier = Modifier.size(10.dp)) {
            drawCircle(color = color)
        }
        Spacer(modifier = Modifier.width(6.dp))
        Text(
            text = "数据更新于 $lastUpdated",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

private fun freshnessColor(minutesAgo: Int): Color = when {
    minutesAgo < 5 -> Color(0xFF388E3C)   // 绿色 - 新鲜
    minutesAgo <= 30 -> Color(0xFFFF8F00) // 黄色 - 陈旧
    else -> Color(0xFFD32F2F)             // 红色 - 过期
}

private fun freshnessLabel(minutesAgo: Int): String = when {
    minutesAgo < 1 -> "刚刚"
    minutesAgo < 60 -> "${minutesAgo}分钟前"
    minutesAgo < 1440 -> "${minutesAgo / 60}小时前"
    else -> "${minutesAgo / 1440}天前"
}

// ── Previews ──

@Preview(name = "Fresh (< 5 min)")
@Composable
private fun DataFreshnessFreshPreview() {
    FloodShieldTheme { DataFreshness(minutesAgo = 2) }
}

@Preview(name = "Stale (15 min)")
@Composable
private fun DataFreshnessStalePreview() {
    FloodShieldTheme { DataFreshness(minutesAgo = 15) }
}

@Preview(name = "Outdated (> 30 min)")
@Composable
private fun DataFreshnessOutdatedPreview() {
    FloodShieldTheme { DataFreshness(minutesAgo = 45) }
}

@Preview(name = "Legacy string overload")
@Composable
private fun DataFreshnessLegacyPreview() {
    FloodShieldTheme { DataFreshness(lastUpdated = "3分钟前", minutesAgo = 3) }
}
