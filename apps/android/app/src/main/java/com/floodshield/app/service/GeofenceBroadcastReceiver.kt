package com.floodshield.app.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import com.floodshield.app.R
import com.google.android.gms.location.Geofence
import com.google.android.gms.location.GeofencingEvent

/**
 * 地理围栏事件接收器。
 * 当设备进入或离开指定区域时触发通知。
 */
class GeofenceBroadcastReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val event = GeofencingEvent.fromIntent(intent) ?: return
        if (event.hasError()) return

        val transition = event.geofenceTransition
        val message = when (transition) {
            Geofence.GEOFENCE_TRANSITION_ENTER -> "您已进入洪涝风险区域，请注意安全"
            Geofence.GEOFENCE_TRANSITION_EXIT -> "您已离开洪涝风险区域"
            else -> return
        }

        showNotification(context, message)
    }

    private fun showNotification(context: Context, message: String) {
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        val channel = NotificationChannel(
            CHANNEL_ID,
            "区域预警",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "进入/离开风险区域时的通知"
        }
        manager.createNotificationChannel(channel)

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setContentTitle("区域预警")
            .setContentText(message)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()

        manager.notify(System.currentTimeMillis().toInt(), notification)
    }

    companion object {
        private const val CHANNEL_ID = "geofence_alerts"
    }
}
