plugins {
  id("com.android.application")
  id("org.jetbrains.kotlin.android")
  id("com.google.gms.google-services")
}

android {
  namespace = "com.netopt.app"
  compileSdk = 34

  defaultConfig {
    applicationId = "com.netopt.app"
    minSdk = 26
    targetSdk = 34
    versionCode = 1
    versionName = "0.1.0"

    val jpushAppKey = (project.findProperty("JPUSH_APPKEY") as? String)?.trim().orEmpty()
    val jpushChannel = (project.findProperty("JPUSH_CHANNEL") as? String)?.trim().ifEmpty { "developer-default" }
    manifestPlaceholders["JPUSH_PKGNAME"] = applicationId
    manifestPlaceholders["JPUSH_APPKEY"] = jpushAppKey
    manifestPlaceholders["JPUSH_CHANNEL"] = jpushChannel

    buildConfigField("String", "BASE_URL", "\"https://47.103.138.58\"")
  }

  buildTypes {
    release {
      isMinifyEnabled = false
      proguardFiles(
        getDefaultProguardFile("proguard-android-optimize.txt"),
        "proguard-rules.pro",
      )
    }
  }

  compileOptions {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
  }

  kotlinOptions {
    jvmTarget = "17"
  }

  buildFeatures {
    buildConfig = true
  }
}

dependencies {
  implementation("androidx.core:core-ktx:1.12.0")
  implementation("androidx.appcompat:appcompat:1.6.1")
  implementation("com.google.android.material:material:1.11.0")
  implementation("androidx.activity:activity-ktx:1.8.2")
  implementation(platform("com.google.firebase:firebase-bom:32.7.4"))
  implementation("com.google.firebase:firebase-messaging")
  implementation("cn.jiguang.sdk:jpush:5.6.0")
}

