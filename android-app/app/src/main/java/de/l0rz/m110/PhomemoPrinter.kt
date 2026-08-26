package de.l0rz.m110

import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothSocket
import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.Paint
import com.google.zxing.BarcodeFormat
import com.google.zxing.EncodeHintType
import com.google.zxing.MultiFormatWriter
import com.google.zxing.qrcode.decoder.ErrorCorrectionLevel
import java.io.OutputStream
import java.util.UUID

/**
 * Phomemo M110 Ansteuerung — 1:1 portiert vom Pi-Dienst (protocol.py).
 * 384 px breit (48 Byte/Zeile), Bluetooth Classic SPP.
 * Raster: ESC @ (1B 40) Reset -> GS v 0 (1D 76 30 00) + width/height -> 1-bit Daten (MSB links, 1 = schwarz).
 */
object PhomemoPrinter {

    private val SPP_UUID: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
    const val WIDTH_PX = 384
    const val WIDTH_BYTES = 48          // 384 / 8
    private const val DPI = 203         // Kopf-Auflösung wie Pi-Dienst

    /** Label-Format. Der Thermokopf ist fix 384 dot (~48 mm) breit; die Größe steuert v.a. die Höhe. */
    data class LabelSize(val nameRes: Int, val widthMm: Int, val heightMm: Int) {
        fun heightPx(): Int = (heightMm / 25.4 * DPI).toInt()
    }

    val LABEL_SIZES = listOf(
        LabelSize(R.string.label_40x30, 40, 30),
        LabelSize(R.string.label_50x30, 50, 30),
        LabelSize(R.string.label_30x50, 30, 50),
        LabelSize(R.string.label_50x25, 50, 25),
        LabelSize(R.string.label_25x25, 25, 25),
    )

    /** Aktuell gewähltes Label — bestimmt die feste Render-Höhe aller Label. */
    @Volatile var labelSize: LabelSize = LABEL_SIZES[0]
    val labelHeightPx: Int get() = labelSize.heightPx()

    /** Standard-Druckkopf-Korrektur (dot), damit der Druck auf diesem M110 mittig sitzt. */
    const val DEFAULT_OFFSET_X = 28
    const val DEFAULT_OFFSET_Y = 0

    /** Ausrichtung: Drehung in Grad (0/90/180/270) + Druckkopf-Versatz in dot (X/Y). */
    @Volatile var rotationDeg: Int = 0
    @Volatile var offsetX: Int = DEFAULT_OFFSET_X
    @Volatile var offsetY: Int = DEFAULT_OFFSET_Y

    /**
     * Orientierung fürs Vorschaubild: dreht das Label und passt es auf 384 px Breite ein.
     * OHNE Kopf-Versatz — die Vorschau bleibt visuell zentriert.
     */
    fun orient(src: Bitmap): Bitmap {
        val rotated = if (rotationDeg % 360 == 0) src else {
            val m = Matrix(); m.postRotate(rotationDeg.toFloat())
            Bitmap.createBitmap(src, 0, 0, src.width, src.height, m, true)
        }
        return if (rotated.width == WIDTH_PX) rotated
        else Bitmap.createScaledBitmap(rotated, WIDTH_PX, (rotated.height * WIDTH_PX / rotated.width).coerceAtLeast(1), true)
    }

    /**
     * Nur fürs Drucken: verschiebt das (bereits orientierte) Label um den Kopf-Versatz,
     * damit es physisch mittig auf dem Label landet.
     */
    fun applyPrintOffset(src: Bitmap): Bitmap {
        if (offsetX == 0 && offsetY == 0) return src
        val out = Bitmap.createBitmap(WIDTH_PX, src.height, Bitmap.Config.ARGB_8888)
        val c = Canvas(out); c.drawColor(Color.WHITE)
        c.drawBitmap(src, offsetX.toFloat(), offsetY.toFloat(), null)
        return out
    }

    private var socket: BluetoothSocket? = null
    private var out: OutputStream? = null
    var connectedName: String? = null
        private set

    val isConnected: Boolean get() = socket?.isConnected == true

    /** Verbindet per RFCOMM/SPP. Wirft IOException bei Fehler. */
    fun connect(device: BluetoothDevice) {
        disconnect()
        val s = device.createRfcommSocketToServiceRecord(SPP_UUID)
        s.connect()
        socket = s
        out = s.outputStream
        connectedName = try { device.name ?: device.address } catch (_: SecurityException) { device.address }
    }

    fun disconnect() {
        try { out?.flush() } catch (_: Exception) {}
        try { socket?.close() } catch (_: Exception) {}
        out = null; socket = null; connectedName = null
    }

    /** Sendet ein bereits gepacktes 1-Bit-Bitmap (48*height Bytes). */
    private fun sendBitmap(data: ByteArray, height: Int) {
        val o = out ?: throw IllegalStateException("not connected")
        // 1) Reset
        o.write(byteArrayOf(0x1B, 0x40))
        o.flush()
        // 2) Raster-Header GS v 0
        val header = byteArrayOf(
            0x1D, 0x76, 0x30, 0x00,
            (WIDTH_BYTES and 0xFF).toByte(), ((WIDTH_BYTES shr 8) and 0xFF).toByte(),
            (height and 0xFF).toByte(), ((height shr 8) and 0xFF).toByte()
        )
        o.write(header)
        o.flush()
        Thread.sleep(20)
        // 3) Bilddaten blockweise (schonend fürs SPP-Modul)
        var idx = 0
        val block = WIDTH_BYTES * 24  // 24 Zeilen pro Block
        while (idx < data.size) {
            val end = minOf(idx + block, data.size)
            o.write(data, idx, end - idx)
            o.flush()
            Thread.sleep(8)
            idx = end
        }
        // KEIN Abschluss-Vorschub: Bei 40x30-Gap-Labels triggert selbst ein kleiner
        // Feed (ESC d n) den Gap-Sensor und schiebt ein ganzes Leer-Label raus.
        // Der bewährte Pi-Dienst sendet ebenfalls nichts nach den Bilddaten.
    }

    /** Packt ein Bitmap (muss 384 px breit sein) in 1-Bit MSB-first, 1 = schwarz. */
    fun packBitmap(bmp: Bitmap): Pair<ByteArray, Int> {
        val src = if (bmp.width == WIDTH_PX) bmp
        else Bitmap.createScaledBitmap(bmp, WIDTH_PX, bmp.height * WIDTH_PX / bmp.width, true)
        val h = src.height
        val out = ByteArray(WIDTH_BYTES * h)
        val row = IntArray(WIDTH_PX)
        for (y in 0 until h) {
            src.getPixels(row, 0, WIDTH_PX, 0, y, WIDTH_PX, 1)
            for (bx in 0 until WIDTH_BYTES) {
                var b = 0
                for (bit in 0 until 8) {
                    val x = bx * 8 + bit
                    val c = row[x]
                    // Luminanz; dunkel -> Bit setzen. Alpha 0 = weiß.
                    val a = (c ushr 24) and 0xFF
                    val lum = if (a == 0) 255 else
                        (((c ushr 16 and 0xFF) * 299 + (c ushr 8 and 0xFF) * 587 + (c and 0xFF) * 114) / 1000)
                    if (lum < 128) b = b or (0x80 shr bit)
                }
                out[y * WIDTH_BYTES + bx] = b.toByte()
            }
        }
        return Pair(out, h)
    }

    fun printBitmap(bmp: Bitmap) {
        val (data, h) = packBitmap(bmp)
        sendBitmap(data, h)
    }

    // ---------------------------------------------------------------- Text

    enum class Align { LEFT, CENTER, RIGHT }

    /**
     * Rendert Text auf ein Label (Höhe = aktuelle Label-Größe) und druckt ihn.
     * @param baseSize Start-Schriftgröße (0 = automatisch einpassen)
     */
    fun printText(text: String, baseSize: Float = 0f, align: Align = Align.CENTER) {
        printBitmap(renderText(text, baseSize, align))
    }

    fun renderText(text: String, baseSize: Float = 0f, align: Align = Align.CENTER): Bitmap {
        val h = labelHeightPx
        val bmp = Bitmap.createBitmap(WIDTH_PX, h, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        c.drawColor(Color.WHITE)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.BLACK
            textAlign = when (align) {
                Align.LEFT -> Paint.Align.LEFT
                Align.RIGHT -> Paint.Align.RIGHT
                Align.CENTER -> Paint.Align.CENTER
            }
            isFakeBoldText = true
        }
        // Schriftgröße bestimmen: fest (baseSize>0) oder automatisch runter bis es passt
        var size = if (baseSize > 0f) baseSize else 72f
        while (size > 18f) {
            paint.textSize = size
            val wrapped = wrap(text, paint)
            val totalH = wrapped.size * (paint.fontMetrics.run { bottom - top })
            val maxW = wrapped.maxOf { paint.measureText(it) }
            if (totalH < h - 16 && maxW < WIDTH_PX - 16) break
            if (baseSize > 0f && size <= baseSize) { /* fest, trotzdem einpassen */ }
            size -= 4f
        }
        paint.textSize = size
        val wrapped = wrap(text, paint)
        val lineH = paint.fontMetrics.run { bottom - top }
        var y = (h - wrapped.size * lineH) / 2 - paint.fontMetrics.top
        val x = when (align) {
            Align.LEFT -> 12f
            Align.RIGHT -> WIDTH_PX - 12f
            Align.CENTER -> WIDTH_PX / 2f
        }
        for (ln in wrapped) { c.drawText(ln, x, y, paint); y += lineH }
        return bmp
    }

    private fun wrap(text: String, paint: Paint): List<String> {
        val out = ArrayList<String>()
        for (rawLine in text.split("\n")) {
            val words = rawLine.split(" ")
            var cur = StringBuilder()
            for (w in words) {
                val test = if (cur.isEmpty()) w else "$cur $w"
                if (paint.measureText(test) > WIDTH_PX - 24 && cur.isNotEmpty()) {
                    out.add(cur.toString()); cur = StringBuilder(w)
                } else cur = StringBuilder(test)
            }
            out.add(cur.toString())
        }
        return if (out.isEmpty()) listOf(text) else out
    }

    // ---------------------------------------------------------------- Bild / Foto

    /**
     * Rendert ein beliebiges Bild EINHEITLICH auf ein Label der aktuellen Größe
     * (384 × Label-Höhe), Bild mittig eingepasst (contain), optional Floyd–Steinberg-Dithering.
     */
    fun renderImage(source: Bitmap, dither: Boolean): Bitmap {
        val h = labelHeightPx
        val flat = Bitmap.createBitmap(WIDTH_PX, h, Bitmap.Config.ARGB_8888)
        val c = Canvas(flat); c.drawColor(Color.WHITE)
        val scale = minOf(WIDTH_PX.toFloat() / source.width, h.toFloat() / source.height)
        val dw = (source.width * scale).toInt().coerceAtLeast(1)
        val dh = (source.height * scale).toInt().coerceAtLeast(1)
        val scaled = Bitmap.createScaledBitmap(source, dw, dh, true)
        c.drawBitmap(scaled, (WIDTH_PX - dw) / 2f, (h - dh) / 2f, null)
        return if (dither) floydSteinberg(flat) else flat
    }

    fun printImage(source: Bitmap, dither: Boolean) = printBitmap(renderImage(source, dither))

    /** Floyd–Steinberg-Dithering nach Schwarz/Weiß — Graustufen/Fotos werden druckbar. */
    private fun floydSteinberg(bmp: Bitmap): Bitmap {
        val w = bmp.width; val h = bmp.height
        val gray = FloatArray(w * h)
        val px = IntArray(w * h)
        bmp.getPixels(px, 0, w, 0, 0, w, h)
        for (i in px.indices) {
            val c = px[i]
            gray[i] = (((c ushr 16 and 0xFF) * 299 + (c ushr 8 and 0xFF) * 587 + (c and 0xFF) * 114) / 1000).toFloat()
        }
        for (y in 0 until h) for (x in 0 until w) {
            val i = y * w + x
            val old = gray[i]
            val new = if (old < 128) 0f else 255f
            val err = old - new
            gray[i] = new
            if (x + 1 < w) gray[i + 1] += err * 7 / 16
            if (y + 1 < h) {
                if (x > 0) gray[i + w - 1] += err * 3 / 16
                gray[i + w] += err * 5 / 16
                if (x + 1 < w) gray[i + w + 1] += err * 1 / 16
            }
        }
        val outBmp = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        for (i in px.indices) {
            val v = if (gray[i] < 128) 0 else 255
            px[i] = Color.rgb(v, v, v)
        }
        outBmp.setPixels(px, 0, w, 0, 0, w, h)
        return outBmp
    }

    // ---------------------------------------------------------------- QR / Barcode

    /** QR-Code, zentriert auf einem Label der aktuellen Größe (384 × Label-Höhe). */
    fun renderQr(content: String): Bitmap {
        val h = labelHeightPx
        val size = (minOf(WIDTH_PX, h) - 24).coerceAtLeast(64)
        val matrix = MultiFormatWriter().encode(
            content, BarcodeFormat.QR_CODE, size, size,
            mapOf(EncodeHintType.ERROR_CORRECTION to ErrorCorrectionLevel.M, EncodeHintType.MARGIN to 1)
        )
        val qr = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        for (y in 0 until size) for (x in 0 until size)
            qr.setPixel(x, y, if (matrix.get(x, y)) Color.BLACK else Color.WHITE)
        return centerOnLabel(qr, h)
    }

    /** Code128-Barcode, zentriert auf einem Label der aktuellen Größe. */
    fun renderBarcode(content: String): Bitmap {
        val h = labelHeightPx
        val bw = WIDTH_PX - 40
        val bh = (h / 2).coerceIn(60, 160)
        val matrix = MultiFormatWriter().encode(
            content, BarcodeFormat.CODE_128, bw, bh, mapOf(EncodeHintType.MARGIN to 2)
        )
        val mw = matrix.width; val mh = matrix.height
        val bar = Bitmap.createBitmap(mw, mh, Bitmap.Config.ARGB_8888)
        for (y in 0 until mh) for (x in 0 until mw)
            bar.setPixel(x, y, if (matrix.get(x, y)) Color.BLACK else Color.WHITE)
        return centerOnLabel(bar, h)
    }

    fun printQr(content: String) = printBitmap(renderQr(content))
    fun printBarcode(content: String) = printBitmap(renderBarcode(content))

    /** Legt ein Bild horizontal+vertikal zentriert auf einen weißen 384×labelH-Grund. */
    private fun centerOnLabel(content: Bitmap, labelH: Int): Bitmap {
        val bmp = Bitmap.createBitmap(WIDTH_PX, labelH, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp); c.drawColor(Color.WHITE)
        val left = (WIDTH_PX - content.width) / 2f
        val top = (labelH - content.height) / 2f
        c.drawBitmap(content, left, top, null)
        return bmp
    }

    // ---------------------------------------------------------------- Test

    /** Test-Label: Rahmen + Text. */
    fun renderTestLabel(context: Context): Bitmap {
        val h = labelHeightPx
        val bmp = Bitmap.createBitmap(WIDTH_PX, h, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        c.drawColor(Color.WHITE)
        val p = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.BLACK; style = Paint.Style.STROKE; strokeWidth = 4f }
        c.drawRect(8f, 8f, WIDTH_PX - 8f, h - 8f, p)
        val tp = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.BLACK; textAlign = Paint.Align.CENTER; textSize = 44f; isFakeBoldText = true }
        c.drawText(context.getString(R.string.test_label_title), WIDTH_PX / 2f, h / 2f - 10f, tp)
        tp.textSize = 28f
        c.drawText(context.getString(R.string.test_label_subtitle), WIDTH_PX / 2f, h / 2f + 40f, tp)
        return bmp
    }
}
