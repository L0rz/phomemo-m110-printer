#!/usr/bin/env python3
"""
Test-Script für Phomemo M110 Robust Server Module
Prüft alle Komponenten auf Funktionsfähigkeit
"""

import sys
import os
import traceback

def test_imports():
    """Teste alle Python-Module"""
    print("🧪 Teste Python-Module...")
    
    modules = [
        'printer_controller',
        'api_routes', 
        'calibration_tool',
        'calibration_api',
        'web_template',
        'config'
    ]
    
    failed = []
    
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed.append(module)
        except Exception as e:
            print(f"  ⚠️  {module}: {e}")
    
    return len(failed) == 0

def test_dependencies():
    """Teste Python-Abhängigkeiten"""
    print("\n📦 Teste Python-Abhängigkeiten...")
    
    deps = [
        ('flask', 'Flask'),
        ('PIL', 'Pillow'),
        ('datetime', 'datetime'),
        ('threading', 'threading'),
        ('subprocess', 'subprocess'),
        ('queue', 'queue')
    ]
    
    failed = []
    
    for module, name in deps:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} - Installation: pip3 install {name.lower()}")
            failed.append(name)
    
    return len(failed) == 0

def test_printer_controller():
    """Teste Printer Controller Klasse"""
    print("\n🖨️ Teste Printer Controller...")
    
    try:
        from printer_controller import RobustPhomemoM110, ConnectionStatus, PrintJob
        
        # Test Klassen-Initialisierung
        printer = RobustPhomemoM110("00:00:00:00:00:00")  # Dummy MAC
        print("  ✅ RobustPhomemoM110 Klasse")
        
        # Test Status
        status = printer.get_connection_status()
        print("  ✅ Connection Status")
        
        # Test Enums
        assert hasattr(ConnectionStatus, 'CONNECTED')
        print("  ✅ ConnectionStatus Enum")
        
        # Test PrintJob
        job = PrintJob("test", "text", {}, 0.0)
        print("  ✅ PrintJob Klasse")
        
        # Cleanup
        printer.stop_services()
        
        return True
        
    except Exception as e:
        print(f"  ❌ Printer Controller Fehler: {e}")
        traceback.print_exc()
        return False

def test_calibration():
    """Teste Kalibrierungs-Module"""
    print("\n📐 Teste Kalibrierung...")
    
    try:
        from calibration_tool import PhomemoCalibration
        from printer_controller import RobustPhomemoM110
        
        # Test Klassen
        printer = RobustPhomemoM110("00:00:00:00:00:00")
        calibration = PhomemoCalibration(printer)
        print("  ✅ PhomemoCalibration Klasse")
        
        # Test Bild-Erstellung (ohne Druck)
        img = calibration.create_border_test()
        assert img.width > 0 and img.height > 0
        print("  ✅ Border Test Bild")
        
        img = calibration.create_grid_test()
        assert img.width > 0 and img.height > 0  
        print("  ✅ Grid Test Bild")
        
        img = calibration.create_corner_test()
        assert img.width > 0 and img.height > 0
        print("  ✅ Corner Test Bild")
        
        # Cleanup
        printer.stop_services()
        
        return True
        
    except Exception as e:
        print(f"  ❌ Kalibrierung Fehler: {e}")
        traceback.print_exc()
        return False

def test_web_components():
    """Teste Web-Komponenten"""
    print("\n🌐 Teste Web-Komponenten...")
    
    try:
        from web_template import WEB_INTERFACE
        assert len(WEB_INTERFACE) > 1000
        assert 'Phomemo M110' in WEB_INTERFACE
        print("  ✅ Web Template")
        
        # Test JavaScript-Datei
        if os.path.exists('static/app.js'):
            with open('static/app.js', 'r') as f:
                js_content = f.read()
            assert 'function checkConnection' in js_content
            assert 'function printCalibration' in js_content
            print("  ✅ JavaScript Datei")
        else:
            print("  ⚠️  JavaScript Datei nicht gefunden")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Web-Komponenten Fehler: {e}")
        return False

def test_config():
    """Teste Konfiguration"""
    print("\n⚙️ Teste Konfiguration...")
    
    try:
        import config
        
        # Test wichtige Konfigurationswerte
        assert hasattr(config, 'PRINTER_MAC')
        assert hasattr(config, 'SERVER_PORT')
        assert hasattr(config, 'PRINTER_WIDTH_PIXELS')
        print("  ✅ Basis-Konfiguration")
        
        # Test MAC-Adresse Format (grob)
        mac = config.PRINTER_MAC
        if ':' in mac and len(mac) == 17:
            print("  ✅ MAC-Adresse Format")
        else:
            print("  ⚠️  MAC-Adresse Format ungewöhnlich")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Konfiguration Fehler: {e}")
        return False

def test_files():
    """Teste Dateien und Verzeichnisse"""
    print("\n📁 Teste Dateien...")
    
    required_files = [
        'main.py',
        'printer_controller.py',
        'calibration_tool.py',
        'api_routes.py',
        'calibration_api.py',
        'web_template.py',
        'config.py',
        'static/app.js'
    ]
    
    missing = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} fehlt")
            missing.append(file)
    
    return len(missing) == 0

def main():
    """Haupttest-Funktion"""
    print("🧪 Phomemo M110 Robust Server - Modul-Tests")
    print("=" * 50)
    
    tests = [
        ("Dateien", test_files),
        ("Abhängigkeiten", test_dependencies), 
        ("Imports", test_imports),
        ("Konfiguration", test_config),
        ("Printer Controller", test_printer_controller),
        ("Kalibrierung", test_calibration),
        ("Web-Komponenten", test_web_components)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test {name} abgebrochen: {e}")
            results.append((name, False))
    
    # Zusammenfassung
    print("\n" + "=" * 50)
    print("📊 Test-Zusammenfassung:")
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Ergebnis: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("✅ Alle Tests erfolgreich! Server sollte funktionieren.")
        print("\n🚀 Zum Starten:")
        print("   python3 main.py")
    else:
        print("❌ Einige Tests fehlgeschlagen. Bitte Fehler beheben.")
        print("\n📚 Hilfe:")
        print("   - README.md für allgemeine Anleitung")
        print("   - CALIBRATION.md für Kalibrierung")
        print("   - pip3 install flask pillow für Abhängigkeiten")
    
    return passed == total

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests abgebrochen")
        sys.exit(1)
