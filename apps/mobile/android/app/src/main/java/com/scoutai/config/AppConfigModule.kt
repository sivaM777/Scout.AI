package com.scoutai.config

import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.scoutai.BuildConfig

class AppConfigModule(reactContext: ReactApplicationContext) : ReactContextBaseJavaModule(reactContext) {
    override fun getName(): String = "AppConfig"

    override fun getConstants(): MutableMap<String, Any> =
        mutableMapOf(
            "apiBaseUrl" to BuildConfig.SCOUT_API_BASE_URL,
        )
}
