package de.l0rz.m110

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothManager
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.google.android.material.tabs.TabLayout

class MainActivity : AppCompatActivity() {

    private lateinit var status: TextView
    private lateinit var statusChip: TextView
    private lateinit var settingsPanel: View
    private lateinit var languageSpinner: Spinner
    private lateinit var deviceSpinner: Spinner
    private lateinit var labelSpinner: Spinner
    private lateinit var textInput: EditText
    private lateinit var textSizeSpinner: Spinner
    private lateinit var textAlignSpinner: Spinner
    private lateinit var codeInput: EditText
    private lateinit var aiKeyInput: EditText
    private lateinit var aiPromptInput: EditText
    private lateinit var imagePreview: ImageView
    private lateinit var chkDither: CheckBox
    private lateinit var rotateSpinner: Spinner
    private lateinit var offXSeek: SeekBar
    private lateinit var offYSeek: SeekBar
    private lateinit var offXLabel: TextView
    private lateinit var offYLabel: TextView
    private lateinit var panels: List<View>

    private var devices: List<BluetoothDevice> = emptyList()
    private var currentLabel: Bitmap? = null
    private var lastBuilder: (() -> Bitmap)? = null

    private val prefs by lazy { getSharedPreferences("m110", Context.MODE_PRIVATE) }

    private val reqPerms = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { loadDevices() }

    private val pickImage = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri: Uri? -> if (uri != null) onImagePicked(uri) }

    override fun attachBaseContext(newBase: Context) {
        val lang = newBase.getSharedPreferences(LocaleHelper.PREFS_NAME, Context.MODE_PRIVATE)
            .getString(LocaleHelper.KEY_LANG, LocaleHelper.LANG_DE) ?: LocaleHelper.LANG_DE
        super.attachBaseContext(LocaleHelper.wrap(newBase, lang))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        status = findViewById(R.id.status)
        statusChip = findViewById(R.id.statusChip)
        settingsPanel = findViewById(R.id.settingsPanel)
        languageSpinner = findViewById(R.id.languageSpinner)
        deviceSpinner = findViewById(R.id.deviceSpinner)
        labelSpinner = findViewById(R.id.labelSpinner)
        textInput = findViewById(R.id.textInput)
        textSizeSpinner = findViewById(R.id.textSizeSpinner)
        textAlignSpinner = findViewById(R.id.textAlignSpinner)
        codeInput = findViewById(R.id.codeInput)
        aiKeyInput = findViewById(R.id.aiKeyInput)
        aiPromptInput = findViewById(R.id.aiPromptInput)
        imagePreview = findViewById(R.id.imagePreview)
        chkDither = findViewById(R.id.chkDither)
        rotateSpinner = findViewById(R.id.rotateSpinner)
        offXSeek = findViewById(R.id.offXSeek)
        offYSeek = findViewById(R.id.offYSeek)
        offXLabel = findViewById(R.id.offXLabel)
        offYLabel = findViewById(R.id.offYLabel)
        panels = listOf(
            findViewById(R.id.panelText), findViewById(R.id.panelImage),
            findViewById(R.id.panelCode), findViewById(R.id.panelAi),
            findViewById(R.id.panelGallery)
        )

        setupLanguageSpinner()
        setupSpinners()
        setupAlignment()
        setupTabs()

        statusChip.setOnClickListener {
            settingsPanel.visibility =
                if (settingsPanel.visibility == View.VISIBLE) View.GONE else View.VISIBLE
        }
        findViewById<Button>(R.id.btnConnect).setOnClickListener { connect(devices.getOrNull(deviceSpinner.selectedItemPosition)) }
        findViewById<Button>(R.id.btnPrint).setOnClickListener { doPrint() }
        findViewById<Button>(R.id.btnTest).setOnClickListener { build { PhomemoPrinter.renderTestLabel(this@MainActivity) } }
        findViewById<Button>(R.id.btnBuildText).setOnClickListener { buildText() }
        findViewById<Button>(R.id.btnPickImage).setOnClickListener { pickImage.launch("image/*") }
        findViewById<Button>(R.id.btnBuildQr).setOnClickListener { buildCode(qr = true) }
        findViewById<Button>(R.id.btnBuildBarcode).setOnClickListener { buildCode(qr = false) }
        findViewById<Button>(R.id.btnAiGenerate).setOnClickListener { aiGenerate() }
        findViewById<Button>(R.id.btnCenterReset).setOnClickListener {
            rotateSpinner.setSelection(0)
            offXSeek.progress = PhomemoPrinter.DEFAULT_OFFSET_X + 80
            offYSeek.progress = PhomemoPrinter.DEFAULT_OFFSET_Y + 80
        }
        chkDither.setOnCheckedChangeListener { _, _ -> rebuild() }

        aiKeyInput.setText(prefs.getString("openai_key", ""))
        updateConnStatus()
        ensurePerms()
    }

    private fun setupLanguageSpinner() {
        languageSpinner.adapter = ArrayAdapter(
            this,
            android.R.layout.simple_spinner_dropdown_item,
            resources.getStringArray(R.array.languages)
        )
        val saved = prefs.getString(LocaleHelper.KEY_LANG, LocaleHelper.LANG_DE)
        languageSpinner.setSelection(if (saved == LocaleHelper.LANG_EN) 1 else 0)
        languageSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(p: AdapterView<*>?, v: View?, pos: Int, id: Long) {
                val lang = if (pos == 1) LocaleHelper.LANG_EN else LocaleHelper.LANG_DE
                if (lang != prefs.getString(LocaleHelper.KEY_LANG, LocaleHelper.LANG_DE)) {
                    prefs.edit().putString(LocaleHelper.KEY_LANG, lang).apply()
                    recreate()
                }
            }
            override fun onNothingSelected(p: AdapterView<*>?) {}
        }
    }

    private fun setupTabs() {
        val tabs = findViewById<TabLayout>(R.id.tabLayout)
        showPanel(0)
        tabs.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab) = showPanel(tab.position)
            override fun onTabUnselected(tab: TabLayout.Tab) {}
            override fun onTabReselected(tab: TabLayout.Tab) {}
        })
    }

    private fun showPanel(i: Int) {
        panels.forEachIndexed { idx, p -> p.visibility = if (idx == i) View.VISIBLE else View.GONE }
        if (i == 4) refreshGallery()
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()

    private fun refreshGallery() {
        val grid = findViewById<GridLayout>(R.id.gridGallery)
        val hint = findViewById<TextView>(R.id.galleryHint)
        grid.removeAllViews()
        val files = LabelStore.list(this)
        hint.visibility = if (files.isEmpty()) View.VISIBLE else View.GONE
        val cols = 3
        val size = (resources.displayMetrics.widthPixels - dp(48)) / cols
        for (f in files) {
            val thumb = LabelStore.loadThumb(f, 260) ?: continue
            val iv = ImageView(this)
            iv.layoutParams = GridLayout.LayoutParams().apply {
                width = size; height = size; setMargins(dp(3), dp(3), dp(3), dp(3))
            }
            iv.scaleType = ImageView.ScaleType.FIT_CENTER
            iv.setBackgroundColor(0x11888888)
            iv.setImageBitmap(thumb)
            iv.setOnClickListener {
                val full = LabelStore.loadFull(f) ?: return@setOnClickListener
                currentLabel = full; lastBuilder = null
                imagePreview.setImageBitmap(full)
                status.text = getString(R.string.gallery_loaded)
                toast(getString(R.string.loaded_to_preview))
            }
            iv.setOnLongClickListener {
                androidx.appcompat.app.AlertDialog.Builder(this)
                    .setMessage(getString(R.string.delete_label))
                    .setPositiveButton(getString(R.string.delete)) { _, _ -> LabelStore.delete(f); refreshGallery() }
                    .setNegativeButton(getString(R.string.cancel), null).show()
                true
            }
            grid.addView(iv)
        }
    }

    private fun setupSpinners() {
        labelSpinner.adapter = ArrayAdapter(this,
            android.R.layout.simple_spinner_dropdown_item,
            PhomemoPrinter.LABEL_SIZES.map { getString(it.nameRes) })
        labelSpinner.setSelection(prefs.getInt("label_idx", 0).coerceIn(0, PhomemoPrinter.LABEL_SIZES.size - 1))
        PhomemoPrinter.labelSize = PhomemoPrinter.LABEL_SIZES[labelSpinner.selectedItemPosition]
        labelSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(p: AdapterView<*>?, v: View?, pos: Int, id: Long) {
                PhomemoPrinter.labelSize = PhomemoPrinter.LABEL_SIZES[pos]
                prefs.edit().putInt("label_idx", pos).apply(); rebuild()
            }
            override fun onNothingSelected(p: AdapterView<*>?) {}
        }
        textSizeSpinner.adapter = ArrayAdapter(this,
            android.R.layout.simple_spinner_dropdown_item, resources.getStringArray(R.array.text_sizes))
        textAlignSpinner.adapter = ArrayAdapter(this,
            android.R.layout.simple_spinner_dropdown_item, resources.getStringArray(R.array.alignments))
    }

    private val rotations = listOf(0, 90, 180, 270)

    private fun setupAlignment() {
        rotateSpinner.adapter = ArrayAdapter(this,
            android.R.layout.simple_spinner_dropdown_item, rotations.map { "$it°" })
        rotateSpinner.setSelection(prefs.getInt("rot_idx", 0).coerceIn(0, rotations.size - 1))
        PhomemoPrinter.rotationDeg = rotations[rotateSpinner.selectedItemPosition]
        rotateSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(p: AdapterView<*>?, v: View?, pos: Int, id: Long) {
                PhomemoPrinter.rotationDeg = rotations[pos]
                prefs.edit().putInt("rot_idx", pos).apply(); rebuild()
            }
            override fun onNothingSelected(p: AdapterView<*>?) {}
        }
        offXSeek.progress = (prefs.getInt("off_x", PhomemoPrinter.DEFAULT_OFFSET_X) + 80).coerceIn(0, 160)
        offYSeek.progress = (prefs.getInt("off_y", PhomemoPrinter.DEFAULT_OFFSET_Y) + 80).coerceIn(0, 160)
        applyOffsets(save = false)
        val listener = object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(s: SeekBar?, p: Int, fromUser: Boolean) { applyOffsets(save = false) }
            override fun onStartTrackingTouch(s: SeekBar?) {}
            override fun onStopTrackingTouch(s: SeekBar?) { applyOffsets(save = true) }
        }
        offXSeek.setOnSeekBarChangeListener(listener)
        offYSeek.setOnSeekBarChangeListener(listener)
    }

    private fun applyOffsets(save: Boolean) {
        val ox = offXSeek.progress - 80; val oy = offYSeek.progress - 80
        PhomemoPrinter.offsetX = ox; PhomemoPrinter.offsetY = oy
        offXLabel.text = getString(R.string.offset_x_fmt, ox)
        offYLabel.text = getString(R.string.offset_y_fmt, oy)
        if (save) prefs.edit().putInt("off_x", ox).putInt("off_y", oy).apply()
    }

    // ---------------------------------------------------------------- Vorschau

    private fun build(builder: () -> Bitmap) {
        lastBuilder = builder
        status.text = getString(R.string.generating_preview)
        Thread {
            try {
                val bmp = PhomemoPrinter.orient(builder())
                runOnUiThread {
                    currentLabel = bmp
                    imagePreview.setImageBitmap(bmp)
                    status.text = getString(R.string.preview_ready, bmp.width, bmp.height)
                }
            } catch (e: Exception) { runOnUiThread { status.text = getString(R.string.preview_error, e.message) } }
        }.start()
    }

    private fun rebuild() { lastBuilder?.let { build(it) } }

    private fun doPrint() {
        val bmp = currentLabel ?: run { toast(getString(R.string.need_preview)); return }
        if (!PhomemoPrinter.isConnected) { toast(getString(R.string.need_connect)); settingsPanel.visibility = View.VISIBLE; return }
        status.text = getString(R.string.printing)
        Thread {
            try {
                PhomemoPrinter.printBitmap(PhomemoPrinter.applyPrintOffset(bmp))
                val saved = try { LabelStore.save(this, bmp, System.currentTimeMillis()) } catch (_: Exception) { false }
                runOnUiThread {
                    status.text = getString(if (saved) R.string.printed_saved else R.string.printed_duplicate)
                }
            }
            catch (e: IllegalStateException) {
                runOnUiThread {
                    status.text = getString(R.string.status_not_connected)
                    toast(getString(R.string.need_connect))
                }
            }
            catch (e: Exception) { runOnUiThread { status.text = getString(R.string.print_error, e.message) } }
        }.start()
    }

    private fun buildText() {
        val t = textInput.text.toString().trim()
        if (t.isEmpty()) { toast(getString(R.string.enter_text)); return }
        val size = when (textSizeSpinner.selectedItemPosition) { 1 -> 34f; 2 -> 52f; 3 -> 76f; else -> 0f }
        val align = when (textAlignSpinner.selectedItemPosition) {
            1 -> PhomemoPrinter.Align.LEFT; 2 -> PhomemoPrinter.Align.RIGHT; else -> PhomemoPrinter.Align.CENTER
        }
        build { PhomemoPrinter.renderText(t, size, align) }
    }

    private fun buildCode(qr: Boolean) {
        val c = codeInput.text.toString().trim()
        if (c.isEmpty()) { toast(getString(R.string.enter_content)); return }
        build { if (qr) PhomemoPrinter.renderQr(c) else PhomemoPrinter.renderBarcode(c) }
    }

    private fun onImagePicked(uri: Uri) {
        try {
            val raw = contentResolver.openInputStream(uri).use { BitmapFactory.decodeStream(it) }
                ?: run { toast(getString(R.string.image_unreadable)); return }
            build { PhomemoPrinter.renderImage(raw, chkDither.isChecked) }
        } catch (e: Exception) { toast(getString(R.string.error_fmt, e.message)) }
    }

    private fun aiGenerate() {
        val key = aiKeyInput.text.toString().trim()
        val prompt = aiPromptInput.text.toString().trim()
        if (key.isEmpty()) { toast(getString(R.string.need_api_key)); settingsPanel.visibility = View.VISIBLE; return }
        if (prompt.isEmpty()) { toast(getString(R.string.enter_prompt)); return }
        prefs.edit().putString("openai_key", key).apply()
        status.text = getString(R.string.generating_ai)
        Thread {
            try {
                val raw = OpenAiImage.generatePictogram(this@MainActivity, key, prompt)
                runOnUiThread { build { PhomemoPrinter.renderImage(raw, chkDither.isChecked) } }
            } catch (e: Exception) { runOnUiThread { status.text = getString(R.string.ai_error, e.message) } }
        }.start()
    }

    // ---------------------------------------------------------------- BT

    private fun neededPerms(): Array<String> =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S)
            arrayOf(Manifest.permission.BLUETOOTH_CONNECT, Manifest.permission.BLUETOOTH_SCAN)
        else arrayOf(Manifest.permission.BLUETOOTH, Manifest.permission.BLUETOOTH_ADMIN)

    private fun hasPerms() = neededPerms().all {
        ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
    }

    private fun ensurePerms() { if (hasPerms()) loadDevices() else reqPerms.launch(neededPerms()) }

    private fun loadDevices() {
        if (!hasPerms()) { statusChip.text = getString(R.string.bt_no_permission); return }
        val mgr = getSystemService(BLUETOOTH_SERVICE) as BluetoothManager
        val adapter: BluetoothAdapter? = mgr.adapter
        if (adapter == null || !adapter.isEnabled) { statusChip.text = getString(R.string.bt_off); return }
        try { devices = adapter.bondedDevices.toList() }
        catch (e: SecurityException) { statusChip.text = getString(R.string.bt_no_permission); return }
        val names = devices.map { d -> try { "${d.name ?: "?"} (${d.address})" } catch (e: SecurityException) { d.address } }
        deviceSpinner.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item,
            if (names.isEmpty()) listOf(getString(R.string.no_devices)) else names)
        val lastAddr = prefs.getString("last_device", null)
        val idx = (if (lastAddr != null) devices.indexOfFirst { it.address == lastAddr } else -1)
            .let { if (it >= 0) it else names.indexOfFirst { n -> n.contains("M110", true) || n.contains("Phomemo", true) } }
        if (idx >= 0) deviceSpinner.setSelection(idx)
        if (lastAddr != null && !PhomemoPrinter.isConnected)
            devices.firstOrNull { it.address == lastAddr }?.let { connect(it) }
    }

    private fun connect(d: BluetoothDevice?) {
        if (d == null) { toast(getString(R.string.pair_first)); return }
        statusChip.text = getString(R.string.connecting)
        Thread {
            try {
                PhomemoPrinter.connect(d)
                prefs.edit().putString("last_device", d.address).apply()
                runOnUiThread { updateConnStatus(); settingsPanel.visibility = View.GONE }
            } catch (e: Exception) {
                runOnUiThread {
                    statusChip.text = getString(R.string.connect_failed)
                    settingsPanel.visibility = View.VISIBLE
                    toast(getString(R.string.connect_error, e.message))
                }
            }
        }.start()
    }

    private fun updateConnStatus() {
        if (PhomemoPrinter.isConnected) {
            statusChip.text = getString(R.string.connected_fmt, PhomemoPrinter.connectedName ?: getString(R.string.connected))
        } else {
            statusChip.text = getString(R.string.status_not_connected)
        }
    }

    private fun toast(s: String) = Toast.makeText(this, s, Toast.LENGTH_SHORT).show()

    override fun onPause() {
        super.onPause()
        // API-Key einmalig aus den Einstellungen sichern
        prefs.edit().putString("openai_key", aiKeyInput.text.toString().trim()).apply()
    }

    override fun onDestroy() { super.onDestroy(); PhomemoPrinter.disconnect() }
}
