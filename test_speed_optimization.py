#!/usr/bin/env python3
"""
Speed Test - Vergleicht Übertragungsgeschwindigkeit
"""

import requests
import time
from PIL import Image, ImageDraw
import io

BASE_URL = "http://localhost:8080"

def create_speed_test_image(size="medium") -> bytes:
    """Erstellt Test-Bild in verschiedenen Größen"""
    sizes = {
        "small": (200, 100),
        "medium": (300, 200), 
        "large": (384, 300)
    }
    
    width, height = sizes[size]
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Test-Pattern für Speed-Messung
    draw.text((10, 10), f"SPEED TEST - {size.upper()}", fill='black')
    draw.text((10, 30), f"Size: {width}x{height}px", fill='black')
    
    # Komplexes Pattern für realistische Übertragung
    for y in range(50, height-20, 15):
        draw.line([10, y, width-10, y], fill='black', width=1)
        if y % 30 == 5:
            draw.text((15, y-8), f"Line {y}", fill='black')
    
    # Rahmen
    draw.rectangle([5, 5, width-5, height-5], outline='black', width=2)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def speed_test():
    """Misst Druckgeschwindigkeit"""
    print("🚀 SPEED TEST")
    print("=" * 50)
    print("📊 Misst Übertragungsgeschwindigkeit nach Optimierung")
    print("=" * 50)
    
    # Test verschiedene Bildgrößen
    test_sizes = ["small", "medium", "large"]
    
    for size in test_sizes:
        print(f"\n📏 SPEED TEST: {size.upper()}")
        test_single_speed(size)
        time.sleep(2)  # Pause zwischen Tests

def test_single_speed(size: str):
    """Testet Speed für eine bestimmte Bildgröße"""
    try:
        test_image = create_speed_test_image(size)
        
        print(f"   📊 Image size: {len(test_image)} bytes")
        print(f"   🚀 Starting speed test...")
        
        files = {'data': (f'speed_test_{size}.png', test_image, 'image/png')}
        data = {
            'use_queue': 'false',
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'enable_dither': 'true'
        }
        
        # Zeitmessung
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        end_time = time.time()
        
        result = response.json()
        
        if result['success']:
            duration = end_time - start_time
            speed_kbps = (len(test_image) / 1024) / duration if duration > 0 else 0
            
            print(f"   ✅ Print successful!")
            print(f"   ⏱️ Duration: {duration:.2f} seconds")
            print(f"   📈 Speed: {speed_kbps:.1f} KB/s")
            
            # Speed-Bewertung
            if duration < 5:
                print(f"   🚀 EXCELLENT SPEED!")
            elif duration < 10:
                print(f"   👍 Good speed")
            elif duration < 20:
                print(f"   ⚠️ Acceptable speed") 
            else:
                print(f"   🐌 Slow speed - weitere Optimierung nötig")
                
        else:
            print(f"   ❌ Print failed: {result.get('error', '?')}")
            
    except Exception as e:
        print(f"   ❌ Speed test error: {e}")

def compare_text_vs_image_speed():
    """Vergleicht Text- vs Bild-Geschwindigkeit"""
    print("\n⚡ TEXT vs IMAGE SPEED COMPARISON")
    
    # Text-Speed
    print("   📝 Text speed test...")
    test_text = """SPEED COMPARISON

Text Line 1
Text Line 2
Text Line 3
Text Line 4
Text Line 5

Position Test
Left  Center  Right
|     |       |

Speed Test Complete"""
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/api/print-text", data={
        'text': test_text,
        'font_size': '16',
        'alignment': 'left',
        'immediate': 'true'
    })
    text_duration = time.time() - start_time
    
    if response.json()['success']:
        print(f"      ✅ Text: {text_duration:.2f}s")
    else:
        print(f"      ❌ Text failed")
        text_duration = 999
    
    # Bild-Speed (equivalent size)
    print("   🖼️ Image speed test...")
    test_image = create_speed_test_image("medium")
    
    files = {'data': ('speed_compare.png', test_image, 'image/png')}
    data = {'use_queue': 'false', 'fit_to_label': 'true'}
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
    image_duration = time.time() - start_time
    
    if response.json()['success']:
        print(f"      ✅ Image: {image_duration:.2f}s")
    else:
        print(f"      ❌ Image failed")
        image_duration = 999
    
    # Vergleich
    print(f"\n   📊 SPEED COMPARISON:")
    print(f"      Text:  {text_duration:.2f}s")
    print(f"      Image: {image_duration:.2f}s")
    
    if image_duration <= text_duration * 1.5:
        print(f"      🎉 IMAGE SPEED IS COMPETITIVE!")
    elif image_duration <= text_duration * 3:
        print(f"      👍 Image speed is acceptable")
    else:
        print(f"      ⚠️ Image still slower than text - more optimization needed")

def quick_speed_check():
    """Schneller Speed-Check"""
    print("⚡ QUICK SPEED CHECK")
    
    test_image = create_speed_test_image("small")
    
    files = {'data': ('quick_test.png', test_image, 'image/png')}
    data = {'use_queue': 'false'}
    
    print("   🚀 Quick image test...")
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
    duration = time.time() - start_time
    
    if response.json()['success']:
        print(f"   ✅ Quick test: {duration:.2f}s")
        
        if duration < 3:
            print("   🚀 FAST!")
            return True
        elif duration < 8:
            print("   👍 Good speed")
            return True
        else:
            print("   🐌 Still slow")
            return False
    else:
        print("   ❌ Quick test failed")
        return False

if __name__ == "__main__":
    print("🚀 SPEED TEST SUITE")
    print("📈 Testet optimierte Übertragungsgeschwindigkeit")
    print()
    
    # Quick Check
    if quick_speed_check():
        print("\n📊 Running full speed tests...")
        speed_test()
        compare_text_vs_image_speed()
    else:
        print("\n⚠️ Basic speed still problematic - check server logs")
    
    print("\n🎉 Speed test completed!")
    print("📋 Erwartung: 256-Byte Chunks + reduzierte Pausen = deutlich schneller")
