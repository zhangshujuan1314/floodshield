package com.floodshield.app.ui.components

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.FloatingActionButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.floodshield.app.ui.theme.FloodShieldTheme

@Composable
fun VoiceButton(
    isPlaying: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        contentAlignment = Alignment.Center,
        modifier = modifier.size(96.dp)
    ) {
        // Ripple rings when playing
        if (isPlaying) {
            RippleRing(index = 0, color = MaterialTheme.colorScheme.primary)
            RippleRing(index = 1, color = MaterialTheme.colorScheme.primary)
        }

        FloatingActionButton(
            onClick = onClick,
            shape = CircleShape,
            containerColor = if (isPlaying)
                MaterialTheme.colorScheme.primary
            else
                MaterialTheme.colorScheme.primaryContainer,
            contentColor = if (isPlaying)
                MaterialTheme.colorScheme.onPrimary
            else
                MaterialTheme.colorScheme.onPrimaryContainer,
            elevation = FloatingActionButtonDefaults.elevation(
                defaultElevation = 6.dp,
                pressedElevation = 12.dp
            ),
            modifier = Modifier.size(72.dp)
        ) {
            Icon(
                imageVector = Icons.Default.Mic,
                contentDescription = if (isPlaying) "停止播报" else "语音播报",
                modifier = Modifier.size(32.dp)
            )
        }
    }

    if (isPlaying) {
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = "正在播报...",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.primary
        )
    }
}

@Composable
private fun RippleRing(index: Int, color: Color) {
    val transition = rememberInfiniteTransition(label = "ripple_$index")
    val alpha by transition.animateFloat(
        initialValue = 0.4f,
        targetValue = 0f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 1500, delayMillis = index * 500),
            repeatMode = RepeatMode.Restart
        ),
        label = "rippleAlpha_$index"
    )
    val scale by transition.animateFloat(
        initialValue = 0.8f,
        targetValue = 1.6f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 1500, delayMillis = index * 500),
            repeatMode = RepeatMode.Restart
        ),
        label = "rippleScale_$index"
    )

    Canvas(
        modifier = Modifier
            .size(96.dp)
            .alpha(alpha)
    ) {
        drawCircle(
            color = color,
            radius = size.minDimension / 2 * scale
        )
    }
}

// ── Previews ──

@Preview(name = "VoiceButton - Idle")
@Composable
private fun VoiceButtonIdlePreview() {
    FloodShieldTheme {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            VoiceButton(isPlaying = false, onClick = {})
        }
    }
}

@Preview(name = "VoiceButton - Playing")
@Composable
private fun VoiceButtonPlayingPreview() {
    FloodShieldTheme {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            VoiceButton(isPlaying = true, onClick = {})
        }
    }
}
