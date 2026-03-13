package com.netopt.app

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.webkit.GeolocationPermissions
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.result.ActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
  private lateinit var webView: WebView
  private var injectedTokenOnce: Boolean = false
  private var filePathCallback: ValueCallback<Array<android.net.Uri>>? = null

  private val requestLocation = registerForActivityResult(
    ActivityResultContracts.RequestPermission()
  ) { granted ->
    if (granted) webView.reload()
  }

  private val pickFiles = registerForActivityResult(
    ActivityResultContracts.StartActivityForResult()
  ) { result: ActivityResult ->
    val cb = filePathCallback
    filePathCallback = null
    if (cb == null) return@registerForActivityResult
    if (result.resultCode != Activity.RESULT_OK || result.data == null) {
      cb.onReceiveValue(null)
      return@registerForActivityResult
    }
    val data = result.data
    val clip = data?.clipData
    if (clip != null) {
      val uris = Array(clip.itemCount) { i -> clip.getItemAt(i).uri }
      cb.onReceiveValue(uris)
      return@registerForActivityResult
    }
    val uri = data?.data
    if (uri != null) cb.onReceiveValue(arrayOf(uri)) else cb.onReceiveValue(null)
  }

  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    setContentView(R.layout.activity_main)

    val prefs = getSharedPreferences("netopt", MODE_PRIVATE)
    val savedToken = (prefs.getString("token", "") ?: "").trim()

    webView = findViewById(R.id.webview)
    webView.webViewClient = object : WebViewClient() {
      override fun onPageFinished(view: WebView, url: String) {
        super.onPageFinished(view, url)
        view.evaluateJavascript("localStorage.getItem('token')") { v ->
          val cur = (v ?: "").trim().trim('"')
          if (cur.isNotBlank() && cur != "null") {
            prefs.edit().putString("token", cur).apply()
            return@evaluateJavascript
          }
          if (!injectedTokenOnce && savedToken.isNotBlank()) {
            injectedTokenOnce = true
            view.evaluateJavascript("localStorage.setItem('token', '${savedToken.replace("'", "\\'")}');") { }
            view.reload()
          }
        }
      }
    }
    webView.webChromeClient = object : WebChromeClient() {
      override fun onGeolocationPermissionsShowPrompt(
        origin: String,
        callback: GeolocationPermissions.Callback
      ) {
        callback.invoke(origin, true, false)
      }

      override fun onShowFileChooser(
        webView: WebView,
        filePathCallback: ValueCallback<Array<android.net.Uri>>,
        fileChooserParams: FileChooserParams
      ): Boolean {
        this@MainActivity.filePathCallback?.onReceiveValue(null)
        this@MainActivity.filePathCallback = filePathCallback
        val intent = try {
          fileChooserParams.createIntent()
        } catch (_: Exception) {
          Intent(Intent.ACTION_GET_CONTENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "image/*"
            putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true)
          }
        }
        return try {
          pickFiles.launch(intent)
          true
        } catch (_: Exception) {
          this@MainActivity.filePathCallback = null
          filePathCallback.onReceiveValue(null)
          false
        }
      }
    }

    val s = webView.settings
    s.javaScriptEnabled = true
    s.domStorageEnabled = true
    s.cacheMode = WebSettings.LOAD_DEFAULT
    s.setGeolocationEnabled(true)
    s.mediaPlaybackRequiresUserGesture = false

    ensureLocationPermission()
    webView.loadUrl(BuildConfig.BASE_URL + "/m/home")

    onBackPressedDispatcher.addCallback(this) {
      if (webView.canGoBack()) webView.goBack() else finish()
    }
  }

  private fun ensureLocationPermission() {
    val p = Manifest.permission.ACCESS_FINE_LOCATION
    val ok = ContextCompat.checkSelfPermission(this, p) == PackageManager.PERMISSION_GRANTED
    if (!ok) requestLocation.launch(p)
  }
}

