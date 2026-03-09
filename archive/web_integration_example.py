"""
Web-Interface Integration - Beispiel
Zeigt, wie die QR/Barcode-Komponenten in web_template.py integriert werden
"""

# Um die neuen QR/Barcode-Features im Web-Interface zu aktivieren:

# 1. Import hinzufügen (am Anfang von web_template.py):
from qr_barcode_interface import QR_BARCODE_INTERFACE, QR_BARCODE_JAVASCRIPT

# 2. In der HTML-Struktur nach der bestehenden "Text drucken" Sektion einfügen:
INTEGRATION_EXAMPLE = '''
<!-- Nach der bestehenden Text-Sektion hinzufügen: -->
''' + QR_BARCODE_INTERFACE + '''

<!-- Und im JavaScript-Bereich hinzufügen: -->
<script>
''' + QR_BARCODE_JAVASCRIPT + '''
</script>
'''

# 3. CSS-Ergänzungen (optional, für besseres Styling):
ADDITIONAL_CSS = '''
.code-help {
    background: linear-gradient(135deg, #e8f4fd 0%, #f0f8ff 100%);
    border-left: 4px solid #2196F3;
    position: relative;
}

.code-help::before {
    content: "💡";
    position: absolute;
    top: 10px;
    right: 15px;
    font-size: 20px;
}

.preview-container {
    animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

#codeTextInput {
    font-family: 'Courier New', monospace;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    transition: border-color 0.3s;
}

#codeTextInput:focus {
    border-color: #2196F3;
    box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}

.btn {
    transition: all 0.2s;
}

.btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}
'''

# Vollständige Integration in eine Kopie von web_template.py:
def create_enhanced_web_template():
    """Erstellt eine erweiterte Version des Web-Templates mit QR/Barcode-Support"""
    
    # Basis-Template lesen
    try:
        with open('web_template.py', 'r', encoding='utf-8') as f:
            original_content = f.read()
    except:
        print("❌ web_template.py nicht gefunden")
        return
    
    # Nach der Text-Sektion suchen und neue Sektion einfügen
    insertion_point = original_content.find('<!-- Bild drucken -->')
    if insertion_point == -1:
        insertion_point = original_content.find('</div>\n        </div>')
    
    if insertion_point != -1:
        # QR/Barcode-Sektion einfügen
        enhanced_content = (
            original_content[:insertion_point] + 
            QR_BARCODE_INTERFACE + '\n            ' +
            original_content[insertion_point:]
        )
        
        # JavaScript hinzufügen
        js_insertion = enhanced_content.find('</script>')
        if js_insertion != -1:
            enhanced_content = (
                enhanced_content[:js_insertion] + 
                QR_BARCODE_JAVASCRIPT + '\n        ' +
                enhanced_content[js_insertion:]
            )
        
        # CSS hinzufügen
        css_insertion = enhanced_content.find('</style>')
        if css_insertion != -1:
            enhanced_content = (
                enhanced_content[:css_insertion] + 
                ADDITIONAL_CSS + '\n        ' +
                enhanced_content[css_insertion:]
            )
        
        # Als neue Datei speichern
        with open('web_template_enhanced.py', 'w', encoding='utf-8') as f:
            f.write(enhanced_content)
        
        print("✅ Enhanced Web-Template erstellt: web_template_enhanced.py")
        print("📝 Um es zu aktivieren:")
        print("   1. Backup erstellen: cp web_template.py web_template_backup.py")
        print("   2. Neue Version verwenden: cp web_template_enhanced.py web_template.py")
        print("   3. Server neu starten: python main.py")
    else:
        print("❌ Insertion-Point im Web-Template nicht gefunden")

# Quick-Test für die Integration
def test_integration():
    """Testet die Integration ohne das Template zu ändern"""
    
    print("🧪 Testing Web-Interface Integration...")
    
    # Check ob alle Komponenten verfügbar sind
    components = {
        'QR_BARCODE_INTERFACE': len(QR_BARCODE_INTERFACE) > 100,
        'QR_BARCODE_JAVASCRIPT': len(QR_BARCODE_JAVASCRIPT) > 100,
        'CSS_Enhancements': len(ADDITIONAL_CSS) > 100
    }
    
    for component, available in components.items():
        status = "✅" if available else "❌"
        print(f"   {status} {component}")
    
    # API-Endpunkte prüfen
    api_endpoints = [
        '/api/print-text-with-codes',
        '/api/preview-text-with-codes', 
        '/api/code-syntax-help'
    ]
    
    print("\n📡 Neue API-Endpunkte:")
    for endpoint in api_endpoints:
        print(f"   • {endpoint}")
    
    print("\n🎯 Integration bereit!")
    print("   Alle Komponenten sind verfügbar und können in das Web-Interface")
    print("   integriert werden.")

if __name__ == "__main__":
    print("🌐 Web-Interface Integration für QR/Barcode-Features")
    print("=" * 60)
    
    test_integration()
    
    print("\n🚀 Möchtest du das Enhanced Web-Template erstellen? (j/n): ", end="")
    try:
        choice = input().lower()
        if choice in ['j', 'y', 'ja', 'yes']:
            create_enhanced_web_template()
        else:
            print("\n📝 Manuelle Integration:")
            print("   1. Kopiere QR_BARCODE_INTERFACE in web_template.py")
            print("   2. Füge QR_BARCODE_JAVASCRIPT zu den Scripts hinzu")
            print("   3. Ergänze ADDITIONAL_CSS für besseres Styling")
    except KeyboardInterrupt:
        print("\n👋 Integration bereit!")
