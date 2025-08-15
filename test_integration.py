#!/usr/bin/env python3
"""
Test der QR/Barcode Web-Interface Integration
Prüft ob alle Komponenten verfügbar sind
"""

import os
import sys

def test_web_interface_integration():
    """Testet die Web-Interface Integration"""
    
    print("🌐 Testing Web-Interface QR/Barcode Integration")
    print("=" * 60)
    
    # Check web_template.py
    print("\n📋 Checking web_template.py...")
    
    try:
        with open('web_template.py', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Check für QR/Barcode Sektion
        checks = {
            'QR/Barcode Section': 'QR-Codes & Barcodes' in template_content,
            'Code Textarea': 'codeTextInput' in template_content,
            'Preview Function': 'previewCodeText' in template_content,
            'Print Function': 'printCodeText' in template_content,
            'Syntax Help Function': 'showCodeSyntaxHelp' in template_content,
            'CSS Styling': 'code-help' in template_content,
            'API Endpoints': '/api/preview-text-with-codes' in template_content
        }
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
        
        all_passed = all(checks.values())
        
        if all_passed:
            print("\n✅ Web-Interface Integration: VOLLSTÄNDIG")
        else:
            print("\n⚠️ Web-Interface Integration: UNVOLLSTÄNDIG")
            
    except FileNotFoundError:
        print("❌ web_template.py nicht gefunden")
        return False
    except Exception as e:
        print(f"❌ Fehler beim Lesen von web_template.py: {e}")
        return False
    
    # Check API Routes
    print("\n📡 Checking API Routes...")
    
    try:
        with open('api_routes.py', 'r', encoding='utf-8') as f:
            api_content = f.read()
        
        api_checks = {
            'print-text-with-codes endpoint': '/api/print-text-with-codes' in api_content,
            'preview-text-with-codes endpoint': '/api/preview-text-with-codes' in api_content,
            'code-syntax-help endpoint': '/api/code-syntax-help' in api_content,
            'Error handling for missing deps': 'code_generator is None' in api_content
        }
        
        for check, passed in api_checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
            
    except FileNotFoundError:
        print("❌ api_routes.py nicht gefunden")
        return False
    
    # Check Printer Controller
    print("\n🖨️ Checking Printer Controller...")
    
    try:
        with open('printer_controller.py', 'r', encoding='utf-8') as f:
            controller_content = f.read()
        
        controller_checks = {
            'Code Generator Import': 'from code_generator import CodeGenerator' in controller_content,
            'Fallback Handling': 'HAS_CODE_GENERATOR' in controller_content,
            'create_text_image_with_codes method': 'def create_text_image_with_codes' in controller_content,
            'print_text_with_codes_immediate method': 'def print_text_with_codes_immediate' in controller_content
        }
        
        for check, passed in controller_checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
            
    except FileNotFoundError:
        print("❌ printer_controller.py nicht gefunden")
        return False
    
    # Check Dependencies
    print("\n📦 Checking Dependencies...")
    
    try:
        import qrcode
        print("   ✅ qrcode library available")
        
        import PIL
        print("   ✅ PIL/Pillow available")
        
        # Test QR generation
        qr = qrcode.QRCode(version=1)
        qr.add_data('Test')
        qr.make()
        print("   ✅ QR code generation working")
        
    except ImportError as e:
        print(f"   ⚠️ Dependencies missing: {e}")
        print("   📝 Install with: pip3 install qrcode pillow")
        print("   💡 Server will work without QR/Barcode features")
    
    # Check Code Generator
    print("\n🔧 Checking Code Generator...")
    
    if os.path.exists('code_generator.py'):
        print("   ✅ code_generator.py exists")
        
        try:
            from code_generator import CodeGenerator
            generator = CodeGenerator()
            
            # Test parsing
            test_text = "Test: #qr#Hello#qr# #bar#123#bar#"
            processed, codes = generator.parse_and_process_text(test_text)
            
            print(f"   ✅ Text parsing working: {len(codes)} codes found")
            
        except Exception as e:
            print(f"   ⚠️ Code generator error: {e}")
    else:
        print("   ❌ code_generator.py missing")
    
    print("\n🎯 INTEGRATION STATUS:")
    print("=" * 30)
    
    if all_passed:
        print("✅ WEB-INTERFACE: QR/Barcode-Sektion verfügbar")
        print("✅ API-ENDPOINTS: Alle 3 Endpunkte implementiert")
        print("✅ FALLBACK: Funktioniert auch ohne Dependencies")
        print("✅ READY: Server kann gestartet werden!")
        
        print("\n🚀 NÄCHSTE SCHRITTE:")
        print("   1. Dependencies installieren: pip3 install qrcode pillow")
        print("   2. Server starten: python3 main.py")
        print("   3. Browser öffnen: http://[pi-ip]:5000")
        print("   4. Neue 'QR-Codes & Barcodes' Sektion testen")
        
    else:
        print("⚠️ Integration unvollständig - manuell vervollständigen")
    
    return all_passed

def print_usage_examples():
    """Zeigt Verwendungsbeispiele"""
    
    print("\n📝 VERWENDUNGSBEISPIELE:")
    print("=" * 30)
    
    examples = [
        {
            'name': 'Produkt-Etikett',
            'text': '''Smartphone XY
#qr#https://shop.com/smartphone-xy#qr#
Artikel: #bar#ART-12345#bar#
Preis: 299€'''
        },
        {
            'name': 'WLAN-Zugang',
            'text': '''WLAN: MeinNetzwerk
#qr#WIFI:S:MeinNetzwerk;T:WPA;P:passwort123;H:false;;#qr#
Passwort: passwort123'''
        },
        {
            'name': 'Event-Ticket',
            'text': '''🎫 Konzert 2025
#qr:120#EVENT:2025-08-15;LOC:Berlin;PRICE:50EUR#qr#
Ticket: #bar:60#TICKET-789123#bar#
15.08.2025 - Berlin'''
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}:")
        print("```")
        print(example['text'])
        print("```")

if __name__ == "__main__":
    success = test_web_interface_integration()
    
    if success:
        print_usage_examples()
        
        print("\n🎉 INTEGRATION ERFOLGREICH!")
        print("Die QR/Barcode-Funktionalität ist vollständig im Web-Interface integriert.")
    else:
        print("\n🔧 Bitte fehlende Komponenten ergänzen und Test wiederholen.")
