#!/usr/bin/env python3
"""
Demo und Test für QR-Code und Barcode-Funktionalität
Testet die neue Markdown-Syntax lokal
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from code_generator import CodeGenerator
from PIL import Image
import io
import base64

def test_code_generation():
    """Testet die Code-Generierung"""
    print("Testing QR-Code and Barcode Generation")
    print("=" * 50)
    
    generator = CodeGenerator()
    
    # Test 1: QR-Code Parsing
    print("\nTest 1: Text Parsing")
    test_text = """
Willkommen zum Test!

QR-Code: #qr#https://github.com/phomemo-m110-printer#qr#

Artikel-Nr: #bar#ART-12345#bar#

Grosser QR: #qr:150#Groesserer QR-Code mit mehr Inhalt fuer bessere Lesbarkeit#qr#

Hoher Barcode: #bar:80#LONG-BARCODE-TEXT#bar#

Ende des Tests
    """
    
    processed_text, codes = generator.parse_and_process_text(test_text)
    print(f"Original Text: {len(test_text)} chars")
    print(f"Processed Text: {processed_text}")
    print(f"Codes gefunden: {len(codes)}")
    
    for i, code in enumerate(codes):
        print(f"  {i+1}. {code['type'].upper()}: '{code['content']}' (Size/Height: {code.get('size', code.get('height', 'default'))})")
    
    # Test 2: QR-Code Generation
    print("\nTest 2: QR-Code Generation")
    qr_img = generator.generate_qr_code("https://example.com", 100)
    if qr_img:
        print(f"QR-Code erstellt: {qr_img.width}x{qr_img.height}px")
        qr_img.save("test_qr.png")
        print("Gespeichert als: test_qr.png")
    else:
        print("QR-Code Erstellung fehlgeschlagen")
    
    # Test 3: Barcode Generation
    print("\nTest 3: Barcode Generation")
    barcode_img = generator.generate_barcode("123456789", 60)
    if barcode_img:
        print(f"Barcode erstellt: {barcode_img.width}x{barcode_img.height}px")
        barcode_img.save("test_barcode.png")
        print("Gespeichert als: test_barcode.png")
    else:
        print("Barcode Erstellung fehlgeschlagen")
    
    # Test 4: Combined Image
    print("\nTest 4: Combined Image Creation")
    combined_img = generator.create_combined_image(test_text, font_size=18)
    if combined_img:
        print(f"Kombiniertes Bild erstellt: {combined_img.width}x{combined_img.height}px")
        combined_img.save("test_combined.png")
        print("Gespeichert als: test_combined.png")
        
        # Als Base64 für Web-Interface
        img_buffer = io.BytesIO()
        combined_img.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        print(f"Base64 Length: {len(img_base64)} chars")
    else:
        print("Kombiniertes Bild Erstellung fehlgeschlagen")
    
    # Test 5: Syntax Help
    print("\nTest 5: Syntax Help")
    help_text = generator.get_syntax_help()
    print(help_text)

def test_special_cases():
    """Testet Spezialfaelle und Edge Cases"""
    print("\nSpecial Cases Test")
    print("=" * 30)
    
    generator = CodeGenerator()
    
    test_cases = [
        # WLAN QR-Code
        "WLAN: #qr#WIFI:S:MeinWLAN;T:WPA;P:passwort123;H:false;;#qr#",
        
        # Mehrere Codes in einer Zeile
        "Codes: #qr:80#QR1#qr# und #bar#BAR1#bar#",
        
        # Nur Codes ohne Text
        "#qr#Nur QR#qr#\n#bar#Nur Barcode#bar#",
        
        # Sehr langer Content
        "#qr#Das ist ein sehr langer QR-Code Content der getestet werden soll um zu sehen ob alles funktioniert#qr#",
        
        # Spezialzeichen
        "#bar#CODE-123_AOU!@#$%^&*()#bar#",
        
        # Leere Codes
        "#qr##qr#\n#bar##bar#"
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}: {test_case[:50]}...")
        processed_text, codes = generator.parse_and_process_text(test_case)
        print(f"  Codes found: {len(codes)}")
        
        if codes:
            img = generator.create_combined_image(test_case, font_size=16)
            if img:
                img.save(f"test_case_{i+1}.png")
                print(f"  Image saved: test_case_{i+1}.png ({img.width}x{img.height})")
            else:
                print(f"  Image creation failed")

def demo_api_integration():
    """Zeigt die Integration mit der API"""
    print("\nAPI Integration Demo")
    print("=" * 30)
    
    # Beispiel API Request Bodies
    api_examples = {
        "text_with_codes": {
            "text": "Produkt Info:\n#qr#https://shop.example.com/product/123#qr#\nArtikel: #bar#ART-456789#bar#",
            "font_size": 20,
            "alignment": "center",
            "immediate": True
        },
        
        "preview_request": {
            "text": "Event Ticket:\n#qr:120#EVENT:2025-08-15;LOC:Berlin;PRICE:25EUR#qr#\nTicket: #bar:60#TICKET-789123#bar#",
            "font_size": 18,
            "alignment": "center"
        }
    }
    
    for endpoint, body in api_examples.items():
        print(f"\n{endpoint.upper()}:")
        print("Request Body:")
        for key, value in body.items():
            print(f"  {key}: {value}")
        
        # Simuliere Verarbeitung
        generator = CodeGenerator()
        img = generator.create_combined_image(
            body["text"], 
            body.get("font_size", 22), 
            body.get("alignment", "center")
        )
        
        if img:
            print(f"Response: Image {img.width}x{img.height}px created")
        else:
            print("Response: Error creating image")

if __name__ == "__main__":
    print("Phomemo M110 QR/Barcode Test Suite")
    print("=" * 60)
    
    try:
        test_code_generation()
        test_special_cases()
        demo_api_integration()
        
        print("\nAll tests completed!")
        print("\nGenerated files:")
        print("  - test_qr.png")
        print("  - test_barcode.png") 
        print("  - test_combined.png")
        print("  - test_case_*.png")
        
        print("\nNext steps:")
        print("  1. pip install qrcode code128")
        print("  2. Test with: python demo_codes.py")
        print("  3. Integration in Web-Interface:")
        print("     - Neue API Routes verfuegbar:")
        print("       * /api/print-text-with-codes")
        print("       * /api/preview-text-with-codes") 
        print("       * /api/code-syntax-help")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
