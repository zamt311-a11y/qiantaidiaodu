package com.netopt.app

import android.content.Context
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

object PushTokenReporter {
  private const val PREFS = "netopt"

  fun tryRegisterAll(context: Context) {
    tryRegisterFcm(context)
    tryRegisterJPush(context)
  }

  fun tryRegisterFcm(context: Context) {
    val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    val token = (prefs.getString("fcm_token", "") ?: "").trim()
    postToken(context, token, "android", "fcm_token_sent")
  }

  fun tryRegisterJPush(context: Context) {
    val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    val token = (prefs.getString("jpush_token", "") ?: "").trim()
    postToken(context, token, "jpush", "jpush_token_sent")
  }

  private fun postToken(context: Context, token: String, platform: String, sentKey: String) {
    val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    val auth = (prefs.getString("token", "") ?: "").trim()
    val sent = (prefs.getString(sentKey, "") ?: "").trim()
    if (token.isBlank() || auth.isBlank() || token == sent) return

    Thread {
      try {
        val url = URL(BuildConfig.BASE_URL + "/api/messages/device_tokens")
        val conn = url.openConnection() as HttpURLConnection
        conn.requestMethod = "POST"
        conn.setRequestProperty("Content-Type", "application/json")
        conn.setRequestProperty("Authorization", "Bearer $auth")
        conn.doOutput = true
        val json = "{\"token\":\"$token\",\"platform\":\"$platform\"}"
        OutputStreamWriter(conn.outputStream, Charsets.UTF_8).use { it.write(json) }
        val code = conn.responseCode
        if (code in 200..299) {
          prefs.edit().putString(sentKey, token).apply()
        }
        conn.disconnect()
      } catch (_: Exception) {
      }
    }.start()
  }
}
