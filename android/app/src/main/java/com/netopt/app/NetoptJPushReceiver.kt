package com.netopt.app

import android.content.Context
import cn.jpush.android.service.JPushMessageReceiver

class NetoptJPushReceiver : JPushMessageReceiver() {
  override fun onRegister(context: Context, registrationId: String) {
    val prefs = context.getSharedPreferences("netopt", Context.MODE_PRIVATE)
    prefs.edit().putString("jpush_token", registrationId).apply()
    PushTokenReporter.tryRegisterJPush(context)
  }
}
