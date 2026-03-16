package com.netopt.app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class NetoptFirebaseService : FirebaseMessagingService() {
  override fun onNewToken(token: String) {
    super.onNewToken(token)
    val prefs = getSharedPreferences("netopt", MODE_PRIVATE)
    prefs.edit().putString("fcm_token", token).apply()
    PushTokenReporter.tryRegisterFcm(this)
  }

  override fun onMessageReceived(message: RemoteMessage) {
    val title = message.notification?.title ?: "New message"
    val body = message.notification?.body ?: "You have a new notification"
    showNotification(this, title, body)
  }

  companion object {
    private const val CHANNEL_ID = "netopt_default"
    private const val CHANNEL_NAME = "Netopt Alerts"

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
