#!/usr/bin/env python3
"""
ULTRA-FAST Speed Test
Testet die neue ultra-optimierte send_bitmap Funktion
"""

import requests
import time
from PIL import Image, ImageDraw
import io

BASE_URL = "http://localhost:8080"

def quick_ultra_fast_test():
    """Schneller Test der Ultra-Fast Optimierung"""
    print("🚀 ULTRA-FAST SPEED TEST")
    print("=" * 40)
    
    # Kleine Test-Bilder
    sizes = [
        ("Tiny", 100, 50),
        ("Small", 200, 100), 
        ("Medium", 300, 150)
    ]
    
    for name, w, h in sizes:
        print(f"\n📏 {name} Test ({w}x{h}px):")
        
        # Bild erstellen
        img = Image.new('RGB', (w, h), 'white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), f"ULTRA-FAST {name}", fill='black')
        draw.text((10, 30), f"Speed Test {w}x{h}", fill='black')
        draw.rectangle([5, 5, w-5, h-5], outline='black', width=2)
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        
        print(f"   📊 Image size: {len(image_data)} bytes")
        
        # Speed-Test
        files = {'data': (f'ultra_fast_{name.lower()}.png', image_data, 'image/png')}
        data = {'use_queue': 'false', 'fit_to_label': 'true'}
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        duration = time.time() - start_time
        
        if response.json()['success']:
            print(f"   ✅ {name}: {duration:.2f}s")
            
            if duration < 1:
                print(f"   🚀🚀 ULTRA-FAST! ({duration:.2f}s)")
            elif duration < 2:
                print(f"   🚀 VERY FAST! ({duration:.2f}s)")
            elif duration < 5:
                print(f"   👍 Fast ({duration:.2f}s)")
            else:
                print(f"   😐 Still slow ({duration:.2f}s)")
        else:
            print(f"   ❌ {name} failed")
        
        time.sleep(1)  # Pause zwischen Tests
    
    print(f"\n🎯 ULTRA-FAST Test completed!")
    print("📋 Erwartung: Alle Tests unter 2 Sekunden!")

if __name__ == "__main__":
    quick_ultra_fast_test()
