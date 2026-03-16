package com.netopt.app

import android.app.Application
import cn.jpush.android.api.JPushInterface

class NetoptApp : Application() {
  override fun onCreate() {
    super.onCreate()
    JPushInterface.setDebugMode(BuildConfig.DEBUG)
    JPushInterface.init(this)
  }
}
