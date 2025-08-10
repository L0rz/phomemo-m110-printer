# 🔄 Phomemo M110 - ERWEITERTE VERSION mit Reconnect

**Automatisches Bluetooth-Reconnect für zuverlässige Druckerverbindung**

## 🆕 NEUE FEATURES

### 🔗 Verbindungsmanagement
- **Automatisches Reconnect** bei Verbindungsabbruch
- **Force Reconnect** für hartnäckige Verbindungsprobleme  
- **Live Connection Status** mit visueller Anzeige
- **Retry-Logik** für alle Druckvorgänge
- **Auto-Status-Updates** alle 10 Sekunden

### 🎛️ Erweiterte Benutzeroberfläche
- **Connection Status Panel** mit detaillierten Informationen
- **Reconnect-Buttons** für manuelle Steuerung
- **Visuelle Verbindungsanzeige** (Grün/Rot/Orange)
- **Auto-Refresh Toggle** für Status-Updates
- **Reconnect-Test-Funktion**

### ⚡ Automatische Wiederherstellung
- **Socket-basierte Verbindungsprüfung**
- **Threading-sicheres Verbindungsmanagement**  
- **Konfigurierbarer Retry-Mechanismus**
- **Bluetooth-Service-Monitoring**

## 🚀 Installation & Setup

### 1. Voraussetzungen (gleich wie Standard-Version)
```bash
sudo apt update
sudo apt install python3 python3-pip bluetooth bluez
pip3 install -r requirements.txt
```

### 2. Erweiterte Version starten
```bash
python3 phomemo_server_extended.py
```

### 3. Web-Interface öffnen
```
http://localhost:8080
```

## 🔧 Neue Funktionen im Detail

### Connection Status Panel
Das neue Dashboard zeigt:
- **Verbindungsstatus** (Verbunden/Getrennt)
- **Drucker-MAC** Adresse
- **rfcomm Device** Pfad
- **Auto-Reconnect** Status
- **Letzte Verbindungsprüfung**

### Reconnect-Buttons
- **🔍 Status prüfen** - Aktuelle Verbindung prüfen
- **🔄 Reconnect** - Standard-Wiederverbindung
- **⚡ Force Reconnect** - Erzwungene Neuverbindung
- **🤖 Auto-Reconnect** - Automatik ein/aus

### Auto-Features
- **Auto-Status-Update**: Prüft alle 10s die Verbindung
- **Auto-Reconnect**: Stellt Verbindung automatisch wieder her
- **Retry-Logik**: Wiederholt fehlgeschlagene Druckvorgänge

## 📊 Verbindungs-Monitoring

### Live-Anzeige
```
🟢 Verbunden ✓    - Drucker bereit
🔴 Getrennt ✗     - Keine Verbindung  
🟠 Verbinde...    - Reconnect läuft
```

### Detaillierte Informationen
- MAC-Adresse: `12:7E:5A:E9:E5:22`
- Device: `/dev/rfcomm0`
- Letzte Prüfung: `14:23:15`
- Auto-Reconnect: `Aktiv`

## 🛠️ Fehlerbehebung - ERWEITERT

### Automatische Problembehebung
Die erweiterte Version löst häufige Probleme automatisch:

1. **Verbindung verloren** → Auto-Reconnect
2. **rfcomm belegt** → Automatische Freigabe & Neuverbindung
3. **Bluetooth-Timeout** → Retry mit längerer Wartezeit
4. **Socket-Fehler** → Force Reconnect

### Manuelle Problembehebung

**Problem: Drucker antwortet nicht**
```
1. Klicke "🔍 Status prüfen"
2. Falls rot: "🔄 Reconnect" klicken
3. Falls weiterhin Probleme: "⚡ Force Reconnect"
```

**Problem: Häufige Verbindungsabbrüche**
```
1. Auto-Reconnect prüfen (sollte "Aktiv" sein)
2. Bluetooth-Entfernung verringern
3. Andere Bluetooth-Geräte temporär deaktivieren
```

**Problem: Drucken schlägt fehl**
```
→ Automatische Retry-Logik aktiviert
→ Verbindung wird automatisch wiederhergestellt
→ Druckvorgang wird wiederholt
```

### Debug-Modi

**Verbose Logging aktivieren:**
```python
# In phomemo_server_extended.py
logging.basicConfig(level=logging.DEBUG)
```

**Verbindung manuell testen:**
```bash
# Terminal-Test
bluetoothctl
> connect 12:7E:5A:E9:E5:22
> info 12:7E:5A:E9:E5:22
```

## 🔄 API-Erweiterungen

### Neue Endpoints

```
GET  /api/connection-status    - Detaillierter Verbindungsstatus
POST /api/reconnect           - Standard Reconnect
POST /api/force-reconnect     - Force Reconnect
POST /api/toggle-auto-reconnect - Auto-Reconnect ein/aus
POST /api/disconnect          - Verbindung trennen (Test)
```

### Erweiterte Responses

**Connection Status:**
```json
{
  "connected": true,
  "mac_address": "12:7E:5A:E9:E5:22",
  "rfcomm_device": "/dev/rfcomm0",
  "auto_reconnect": true,
  "reconnect_attempts": 0,
  "last_check": "14:23:15",
  "device_exists": true,
  "bluetooth_service": "active"
}
```

## ⚙️ Konfiguration

### Reconnect-Parameter anpassen
```python
# In phomemo_server_extended.py anpassen:
printer.max_reconnect_attempts = 5      # Standard: 3
printer.reconnect_delay = 3             # Standard: 2 Sekunden  
printer.connection_check_interval = 10  # Standard: 5 Sekunden
printer.auto_reconnect_enabled = True   # Standard: True
```

### Performance-Optimierung
```python
# Für langsamere Systeme:
printer.connection_check_interval = 15  # Seltener prüfen
printer.reconnect_delay = 5             # Längere Wartezeit
```

## 📈 Verbesserungen gegenüber Standard-Version

| Feature | Standard | Erweitert |
|---------|----------|-----------|
| Reconnect | ❌ Manuell | ✅ Automatisch |
| Verbindungsstatus | ❌ Unbekannt | ✅ Live-Anzeige |
| Fehlerbehebung | ❌ Manuell | ✅ Automatisch |
| Retry-Logik | ❌ Keine | ✅ Intelligent |
| UI-Updates | ❌ Statisch | ✅ Auto-Refresh |
| Debug-Info | ❌ Begrenzt | ✅ Detailliert |

## 🔧 Migration von Standard-Version

1. **Backup erstellen:**
   ```bash
   cp phomemo_server.py phomemo_server_backup.py
   ```

2. **Erweiterte Version verwenden:**
   ```bash
   python3 phomemo_server_extended.py
   ```

3. **Konfiguration übertragen:**
   - MAC-Adresse in `PRINTER_MAC` anpassen
   - Offsets aus alter Version übernehmen

## 📞 Support & Troubleshooting

### Häufige Fragen

**Q: Auto-Reconnect funktioniert nicht?**
A: Prüfe `sudo`-Rechte für `rfcomm`-Befehle

**Q: Verbindung bricht ständig ab?**  
A: Verringere Entfernung zum Drucker, prüfe Bluetooth-Service

**Q: Force Reconnect schlägt fehl?**
A: Drucker aus/ein schalten, Bluetooth-Service neustarten

**Q: Status-Updates zu häufig?**
A: Auto-Refresh deaktivieren oder Intervall erhöhen

### Log-Analyse
```bash
# Python-Logs ansehen
python3 phomemo_server_extended.py 2>&1 | tee printer.log

# System Bluetooth-Logs
journalctl -u bluetooth -f
```

## 🎯 Kommende Features

- **📱 Mobile App** Integration
- **📊 Verbindungsstatistiken** 
- **🔔 Push-Benachrichtigungen** bei Problemen
- **🌐 Remote-Monitoring** über Internet
- **📈 Performance-Metriken**

---

**🔄 Mit der erweiterten Version wird Ihr Phomemo M110 zu einem zuverlässigen, selbstverwaltenden Drucker!**
