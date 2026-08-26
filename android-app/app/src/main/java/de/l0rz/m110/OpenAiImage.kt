package de.l0rz.m110

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Base64
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

/**
 * Erzeugt aus einem Text-Prompt ein schwarz-weiß-taugliches Piktogramm über die OpenAI Image API.
 * Läuft synchron -> immer aus einem Hintergrund-Thread aufrufen.
 */
object OpenAiImage {

    /** Gibt ein quadratisches Bitmap zurück oder wirft eine Exception mit lesbarer Meldung. */
    fun generatePictogram(context: Context, apiKey: String, prompt: String): Bitmap {
        val fullPrompt = context.getString(R.string.ai_image_prompt_fmt, prompt)

        val body = JSONObject()
            .put("model", "gpt-image-1")
            .put("prompt", fullPrompt)
            .put("n", 1)
            .put("size", "1024x1024")
            .put("background", "opaque")
            .toString()

        val conn = (URL("https://api.openai.com/v1/images/generations").openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 20000
            readTimeout = 90000
            doOutput = true
            setRequestProperty("Authorization", "Bearer $apiKey")
            setRequestProperty("Content-Type", "application/json")
        }
        OutputStreamWriter(conn.outputStream).use { it.write(body) }

        val code = conn.responseCode
        val stream = if (code in 200..299) conn.inputStream else conn.errorStream
        val resp = stream.bufferedReader().use { it.readText() }
        if (code !in 200..299) {
            val msg = try { JSONObject(resp).getJSONObject("error").getString("message") } catch (_: Exception) { resp.take(200) }
            throw RuntimeException("OpenAI $code: $msg")
        }

        val data = JSONObject(resp).getJSONArray("data").getJSONObject(0)
        // gpt-image-1 liefert b64_json
        val b64 = data.optString("b64_json", "")
        val bytes = if (b64.isNotEmpty()) Base64.decode(b64, Base64.DEFAULT)
        else {
            // Fallback falls URL zurückkommt
            val url = data.getString("url")
            URL(url).openStream().use { it.readBytes() }
        }
        return BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
            ?: throw RuntimeException(context.getString(R.string.image_decode_error))
    }
}
