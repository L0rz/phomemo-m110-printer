#!/usr/bin/env python3
"""
Quick Debug für QR/Barcode Integration
Testet die problematischen Teile
"""

def test_imports():
    """Testet alle Imports"""
    print("🧪 Testing imports...")
    
    try:
        print("  ✅ Basic imports...")
        import os, sys, logging
        
        print("  ✅ PIL...")
        from PIL import Image, ImageDraw, ImageFont
        
        print("  ✅ QR-Code...")
        import qrcode
        
        print("  ✅ Config...")
        from config import *
        
        print("  ✅ Code Generator...")
        from code_generator import CodeGenerator
        
        print("  ✅ Printer Controller...")
        from printer_controller import EnhancedPhomemoM110
        
        print("✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_qr_generation():
    """Testet QR-Code-Generierung"""
    print("\n🔲 Testing QR generation...")
    
    try:
        from code_generator import CodeGenerator
        generator = CodeGenerator()
        
        # QR-Code erstellen
        qr_img = generator.generate_qr_code("https://example.com", 100)
        if qr_img:
            print(f"  ✅ QR created: {qr_img.width}x{qr_img.height}")
        else:
            print("  ❌ QR creation failed")
        
        # Barcode erstellen
        bar_img = generator.generate_barcode("ART-12345", 50)
        if bar_img:
            print(f"  ✅ Barcode created: {bar_img.width}x{bar_img.height}")
        else:
            print("  ❌ Barcode creation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return False

def test_text_parsing():
    """Testet Text-Parsing"""
    print("\n📝 Testing text parsing...")
    
    try:
        from code_generator import CodeGenerator
        generator = CodeGenerator()
        
        test_text = """Test:
#qr#https://example.com#qr#
Code: #bar#12345#bar#"""
        
        processed, codes = generator.parse_and_process_text(test_text)
        print(f"  ✅ Parsed {len(codes)} codes")
        for code in codes:
            print(f"    • {code['type']}: {code['content']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parsing error: {e}")
        return False

def test_combined_image():
    """Testet kombinierte Bild-Erstellung"""
    print("\n🖼️ Testing combined image...")
    
    try:
        from code_generator import CodeGenerator
        generator = CodeGenerator(384, 240)  # Standard Label-Größe
        
        test_text = """# Test Label
QR: #qr:80#https://example.com#qr#
Barcode: #bar:40#12345#bar#"""
        
        img = generator.create_combined_image(test_text, 18, 'center')
        if img:
            print(f"  ✅ Combined image: {img.width}x{img.height}")
            img.save("debug_test.png")
            print("  💾 Saved as debug_test.png")
        else:
            print("  ❌ Combined image failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Combined image error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_printer_controller():
    """Testet Printer Controller"""
    print("\n🖨️ Testing printer controller...")
    
    try:
        from printer_controller import EnhancedPhomemoM110
        
        # Dummy MAC für Test
        printer = EnhancedPhomemoM110("00:00:00:00:00:00")
        
        if hasattr(printer, 'code_generator') and printer.code_generator:
            print("  ✅ Code generator available")
        else:
            print("  ⚠️ Code generator not available")
        
        # Test Offset-Methode
        if hasattr(printer, 'apply_offsets'):
            print("  ✅ apply_offsets method exists")
        else:
            print("  ❌ apply_offsets method missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Printer controller error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 QR/Barcode Debug Tool")
    print("=" * 40)
    
    success = True
    success &= test_imports()
    success &= test_qr_generation()
    success &= test_text_parsing()
    success &= test_combined_image()
    success &= test_printer_controller()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed! QR/Barcode should work.")
    else:
        print("⚠️ Some tests failed. Check errors above.")
    
    print("\n💡 Next steps:")
    print("   1. Fix any errors shown above")
    print("   2. Start server: python3 main.py")
    print("   3. Test in web interface")
