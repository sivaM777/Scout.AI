package com.scoutai.share

import android.content.Intent
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.facebook.react.modules.core.DeviceEventManagerModule

class ShareIntentModule(private val reactContext: ReactApplicationContext) : ReactContextBaseJavaModule(reactContext) {
    companion object {
        private var instance: ShareIntentModule? = null
        private const val EVENT_NAME = "ShareIntentReceived"

        fun handleIntent(intent: Intent?) {
            instance?.emitShareIntent(intent)
        }
    }

    init {
        instance = this
    }

    override fun getName(): String = "ShareIntent"

    @ReactMethod
    fun getInitialSharedText(promise: Promise) {
        promise.resolve(extractSharedText(currentActivity?.intent))
    }

    @ReactMethod
    fun clearInitialSharedText() {
        currentActivity?.intent?.removeExtra(Intent.EXTRA_TEXT)
    }

    @ReactMethod
    fun addListener(eventName: String) {}

    @ReactMethod
    fun removeListeners(count: Int) {}

    private fun emitShareIntent(intent: Intent?) {
        val sharedText = extractSharedText(intent) ?: return

        reactContext
            .getJSModule(DeviceEventManagerModule.RCTDeviceEventEmitter::class.java)
            .emit(EVENT_NAME, sharedText)
    }

    private fun extractSharedText(intent: Intent?): String? {
        if (intent?.action != Intent.ACTION_SEND) {
            return null
        }

        val type = intent.type ?: return null
        if (!type.startsWith("text/")) {
            return null
        }

        return intent.getStringExtra(Intent.EXTRA_TEXT)
    }
}
