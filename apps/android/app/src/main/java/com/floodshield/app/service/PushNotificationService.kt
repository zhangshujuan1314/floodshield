package com.floodshield.app.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import com.floodshield.app.MainActivity
import com.floodshield.app.R
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Firebase Cloud Messaging 服务。
 * 处理推送通知的接收和 FCM Token 的管理。
 */
class PushNotificationService : FirebaseMessagingService() {

    /**
     * FCM Token 刷新时调用。
     * 需要将新 Token 发送到服务器。
     */
    override fun onNewToken(token: String) {
        super.onNewToken(token)
        CoroutineScope(Dispatchers.IO).launch {
            try {
                // TODO: 调用 API 注册新 Token
                // api.registerToken(token)
            } catch (_: Exception) {
                // Token 注册失败，下次启动时重试
            }
        }
    }

    /**
     * 收到推送消息时调用。
     * 支持通知消息和数据消息两种格式。
     */
    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)

        // 优先使用 notification payload，其次使用 data payload
        val title = message.notification?.title
            ?: message.data["title"]
            ?: "防洪预警"
        val body = message.notification?.body
            ?: message.data["body"]
            ?: ""
        val screen = message.data["screen"] ?: "home"
        val alertId = message.data["alertId"]

        showNotification(title, body, screen, alertId)
    }

    /**
     * 显示通知。
     * 点击通知后跳转到指定页面。
     */
    private fun showNotification(
        title: String,
        body: String,
        screen: String,
        alertId: String?
    ) {
        createNotificationChannels()

        // 构建深链接 Intent
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            putExtra("navigate_to", screen)
            alertId?.let { putExtra("alert_id", it) }
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            screen.hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // 根据类型选择通知渠道
        val channelId = if (screen == "alert") CHANNEL_ALERTS else CHANNEL_GENERAL
        val priority = if (screen == "alert") {
            NotificationCompat.PRIORITY_HIGH
        } else {
            NotificationCompat.PRIORITY_DEFAULT
        }

        val notification = NotificationCompat.Builder(this, channelId)
            .setContentTitle(title)
            .setContentText(body)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setPriority(priority)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .build()

        val manager = getSystemService(NotificationManager::class.java)
        manager.notify(System.currentTimeMillis().toInt(), notification)
    }

    /**
     * 创建通知渠道。
     * Android 8.0+ 需要通知渠道。
     */
    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val manager = getSystemService(NotificationManager::class.java)

            // 预警通知渠道（高优先级）
            val alertChannel = NotificationChannel(
                CHANNEL_ALERTS,
                "防洪预警",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "接收防洪预警通知"
                enableVibration(true)
            }

            // 通用通知渠道
            val generalChannel = NotificationChannel(
                CHANNEL_GENERAL,
                "通用通知",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "应用通用通知"
            }

            manager.createNotificationChannel(alertChannel)
            manager.createNotificationChannel(generalChannel)
        }
    }

    companion object {
        const val CHANNEL_ALERTS = "flood_alerts"
        const val CHANNEL_GENERAL = "general_notifications"
    }
}
