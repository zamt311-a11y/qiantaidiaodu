package com.netopt.app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL


class NetoptFirebaseService : FirebaseMessagingService() {
  override fun onNewToken(token: String) {
    super.onNewToken(token)
    val prefs = getSharedPreferences("netopt", MODE_PRIVATE)
    prefs.edit().putString("fcm_token", token).apply()
    tryRegisterToken(this)
  }

  override fun onMessageReceived(message: RemoteMessage) {
    val title = message.notification?.title ?: "新消息"
    val body = message.notification?.body ?: "你有一条新通知"
    showNotification(this, title, body)
  }

  companion object {
    private const val CHANNEL_ID = "netopt_default"
    private const val CHANNEL_NAME = "Netopt 提醒"

    fun tryRegisterToken(context: Context) {
      val prefs = context.getSharedPreferences("netopt", MODE_PRIVATE)
      val token = (prefs.getString("fcm_token", "") ?: "").trim()
      val auth = (prefs.getString("token", "") ?: "").trim()
      val sent = (prefs.getString("fcm_token_sent", "") ?: "").trim()
      if (token.isBlank() || auth.isBlank() || token == sent) return

      Thread {
        try {
          val url = URL(BuildConfig.BASE_URL + "/api/messages/device_tokens")
          val conn = url.openConnection() as HttpURLConnection
          conn.requestMethod = "POST"
          conn.setRequestProperty("Content-Type", "application/json")
          conn.setRequestProperty("Authorization", "Bearer $auth")
          conn.doOutput = true
          val json = "{\"token\":\"$token\",\"platform\":\"android\"}"
          OutputStreamWriter(conn.outputStream, Charsets.UTF_8).use { it.write(json) }
          val code = conn.responseCode
          if (code in 200..299) {
            prefs.edit().putString("fcm_token_sent", token).apply()
          }
          conn.disconnect()
        } catch (_: Exception) {
        }
      }.start()
    }

    private fun showNotification(context: Context, title: String, body: String) {
      val mgr = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
      if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        val channel = NotificationChannel(CHANNEL_ID, CHANNEL_NAME, NotificationManager.IMPORTANCE_DEFAULT)
        mgr.createNotificationChannel(channel)
      }
      val notif = NotificationCompat.Builder(context, CHANNEL_ID)
        .setContentTitle(title)
        .setContentText(body)
        .setSmallIcon(android.R.drawable.ic_dialog_info)
        .setAutoCancel(true)
        .build()
      mgr.notify((System.currentTimeMillis() % 100000).toInt(), notif)
    }
  }
}
