package de.l0rz.m110

import android.content.Context
import android.content.res.Configuration
import android.os.LocaleList
import java.util.Locale

/**
 * Wendet die vom Nutzer gewählte App-Sprache unabhängig von der Systemsprache an.
 * Die Wahl wird in den SharedPreferences gespeichert und beim nächsten Start geladen.
 */
object LocaleHelper {

    const val PREFS_NAME = "m110"
    const val KEY_LANG = "lang"
    const val LANG_DE = "de"
    const val LANG_EN = "en"

    fun wrap(context: Context, lang: String): Context {
        val locale = Locale.forLanguageTag(lang)
        Locale.setDefault(locale)
        val config = Configuration(context.resources.configuration)
        config.setLocales(LocaleList(locale))
        return context.createConfigurationContext(config)
    }
}
