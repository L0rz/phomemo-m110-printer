#!/usr/bin/env python3
"""
WHITE LABEL DIAGNOSTIC
Diagnostiziert warum nur weiße Labels gedruckt werden
"""

import requests
import time
from PIL import Image, ImageDraw
import io

BASE_URL = "http://localhost:8080"

def diagnose_white_labels():
    """Diagnostiziert das weiße Label Problem"""
    print("🔍 WHITE LABEL DIAGNOSTIC")
    print("=" * 50)
    print("📋 Testet verschiedene Ursachen für weiße Labels")
    print("=" * 50)
    
    # Test 1: Sehr einfaches schwarzes Quadrat
    print("\n1️⃣ SIMPLE BLACK SQUARE TEST:")
    test_simple_black_square()
    
    # Test 2: Text funktioniert noch?
    print("\n2️⃣ TEXT COMPARISON TEST:")
    test_text_vs_image()
    
    # Test 3: Image-to-Printer-Format Test
    print("\n3️⃣ IMAGE FORMAT TEST:")
    test_image_format()

def test_simple_black_square():
    """Testet einfachstes schwarzes Quadrat"""
    try:
        # MINIMAL schwarzes Quadrat
        img = Image.new('1', (100, 100), 1)  # Weiß
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 90, 90], fill=0)  # Schwarz
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        
        print(f"   📊 Simple square: {len(image_data)} bytes")
        
        files = {'data': ('black_square.png', image_data, 'image/png')}
        data = {'use_queue': 'false', 'fit_to_label': 'true'}
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print("   ✅ Simple square sent successfully")
            square_result = input("   ❓ War das Quadrat sichtbar? (y/N): ").lower().strip()
            return square_result == 'y'
        else:
            print(f"   ❌ Simple square failed: {result.get('error', '?')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Simple square error: {e}")
        return False

def test_text_vs_image():
    """Vergleicht Text-Druck mit Bild-Druck"""
    try:
        # Text-Test
        print("   📝 Testing text print...")
        text_response = requests.post(f"{BASE_URL}/api/print-text", data={
            'text': 'WHITE LABEL DEBUG\n\nText Test\nLine 1\nLine 2',
            'font_size': '18',
            'alignment': 'center',
            'immediate': 'true'
        })
        
        if text_response.json()['success']:
            print("   ✅ Text printed successfully")
            text_visible = input("   ❓ War der Text sichtbar? (y/N): ").lower().strip()
            
            if text_visible == 'y':
                print("   🎯 TEXT FUNKTIONIERT - Problem ist bei Bild-Verarbeitung")
                return True
            else:
                print("   ⚠️ AUCH TEXT ist weiß - Grundlegendes Problem")
                return False
        else:
            print("   ❌ Text failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Text test error: {e}")
        return False

def test_image_format():
    """Testet verschiedene Bildformate"""
    try:
        print("   🖼️ Testing different image formats...")
        
        # RGB Bild
        img_rgb = Image.new('RGB', (100, 50), 'white')
        draw_rgb = ImageDraw.Draw(img_rgb)
        draw_rgb.text((10, 15), "RGB TEST", fill='black')
        
        # S/W Bild 
        img_bw = Image.new('1', (100, 50), 1)
        draw_bw = ImageDraw.Draw(img_bw)
        draw_bw.text((10, 15), "B/W TEST", fill=0)
        
        # L (Graustufen) Bild
        img_l = Image.new('L', (100, 50), 255)
        draw_l = ImageDraw.Draw(img_l)
        draw_l.text((10, 15), "GRAY TEST", fill=0)
        
        formats = [
            ("RGB", img_rgb),
            ("BW", img_bw), 
            ("GRAY", img_l)
        ]
        
        for name, img in formats:
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            image_data = buffer.getvalue()
            
            print(f"      🧪 {name} format: {len(image_data)} bytes")
            
            files = {'data': (f'{name.lower()}_test.png', image_data, 'image/png')}
            data = {'use_queue': 'false'}
            
            response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
            
            if response.json()['success']:
                print(f"      ✅ {name} sent")
                visible = input(f"      ❓ {name} sichtbar? (y/N): ").lower().strip()
                if visible == 'y':
                    print(f"      🎉 {name} FORMAT FUNKTIONIERT!")
                    return True
            else:
                print(f"      ❌ {name} failed")
            
            time.sleep(1)
        
        return False
        
    except Exception as e:
        print(f"   ❌ Format test error: {e}")
        return False

def suggest_fixes():
    """Schlägt Lösungen vor basierend auf Tests"""
    print("\n🔧 LÖSUNGSVORSCHLÄGE:")
    print("1. DATEN-PROBLEM: image_to_printer_format invertiert Bits?")
    print("2. HEADER-PROBLEM: Bitmap-Header falsch?") 
    print("3. CHUNK-PROBLEM: 4096-Byte Chunks zu groß?")
    print("4. TIMING-PROBLEM: Pausen zu kurz?")
    
    print("\n💡 QUICK-FIXES zum Testen:")
    print("a) Zurück zu kleinen 256-Byte Chunks")
    print("b) Bit-Inversion in image_to_printer_format prüfen")
    print("c) Original send_bitmap von Commit 047e4ad verwenden")
    
    fix_choice = input("\nWelchen Fix soll ich implementieren? (a/b/c): ").lower().strip()
    
    if fix_choice == 'a':
        return "small_chunks"
    elif fix_choice == 'b':
        return "check_inversion"
    elif fix_choice == 'c':
        return "restore_original"
    else:
        return "manual_debug"

if __name__ == "__main__":
    print("🔍 WHITE LABEL DIAGNOSTIC TOOL")
    print("📋 Findet heraus warum Labels weiß bleiben")
    print()
    
    # Führe Diagnose durch
    diagnose_white_labels()
    
    # Lösungsvorschläge
    fix_type = suggest_fixes()
    
    print(f"\n🎯 Empfohlener Fix: {fix_type}")
    print("📋 Nächster Schritt: Fix implementieren und erneut testen")
