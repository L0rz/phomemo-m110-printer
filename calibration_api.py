"""
Kalibrierungs-API für Web Interface Integration
"""

import logging
from flask import request, jsonify
from calibration_tool import PhomemoCalibration

logger = logging.getLogger(__name__)

def setup_calibration_routes(app, printer):
    """Registriert Kalibrierungs-API-Routes"""
    
    calibration = PhomemoCalibration(printer)
    
    @app.route('/api/calibration/border', methods=['POST'])
    def api_calibration_border():
        """Druckt Rahmen-Kalibrierung"""
        try:
            offset_x = int(request.form.get('offset_x', 0))
            offset_y = int(request.form.get('offset_y', 0))
            thickness = int(request.form.get('thickness', 2))
            
            img = calibration.create_border_test(thickness, offset_x, offset_y)
            description = f"Rahmen-Test (Offset: {offset_x},{offset_y}, Dicke: {thickness}px)"
            
            success = calibration.print_calibration_image(img, description)
            
            return jsonify({
                'success': success,
                'message': description,
                'image_size': f"{img.width}x{img.height}px"
            })
            
        except Exception as e:
            logger.error(f"Calibration border error: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/calibration/grid', methods=['POST'])
    def api_calibration_grid():
        """Druckt Gitter-Kalibrierung"""
        try:
            offset_x = int(request.form.get('offset_x', 0))
            offset_y = int(request.form.get('offset_y', 0))
            spacing = int(request.form.get('spacing', 5))
            
            img = calibration.create_grid_test(spacing, offset_x, offset_y)
            description = f"Gitter-Test ({spacing}mm, Offset: {offset_x},{offset_y})"
            
            success = calibration.print_calibration_image(img, description)
            
            return jsonify({
                'success': success,
                'message': description,
                'image_size': f"{img.width}x{img.height}px"
            })
            
        except Exception as e:
            logger.error(f"Calibration grid error: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/calibration/rulers', methods=['POST'])
    def api_calibration_rulers():
        """Druckt Lineal-Kalibrierung"""
        try:
            offset_x = int(request.form.get('offset_x', 0))
            offset_y = int(request.form.get('offset_y', 0))
            
            img = calibration.create_measurement_rulers(offset_x, offset_y)
            description = f"Lineal-Test (Offset: {offset_x},{offset_y})"
            
            success = calibration.print_calibration_image(img, description)
            
            return jsonify({
                'success': success,
                'message': description,
                'image_size': f"{img.width}x{img.height}px"
            })
            
        except Exception as e:
            logger.error(f"Calibration rulers error: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/calibration/corners', methods=['POST'])
    def api_calibration_corners():
        """Druckt Ecken-Kalibrierung"""
        try:
            offset_x = int(request.form.get('offset_x', 0))
            offset_y = int(request.form.get('offset_y', 0))
            corner_size = int(request.form.get('corner_size', 15))
            
            img = calibration.create_corner_test(corner_size, offset_x, offset_y)
            description = f"Ecken-Test (Größe: {corner_size}px, Offset: {offset_x},{offset_y})"
            
            success = calibration.print_calibration_image(img, description)
            
            return jsonify({
                'success': success,
                'message': description,
                'image_size': f"{img.width}x{img.height}px"
            })
            
        except Exception as e:
            logger.error(f"Calibration corners error: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/calibration/series', methods=['POST'])
    def api_calibration_series():
        """Druckt Offset-Serie"""
        try:
            base_offset_x = int(request.form.get('offset_x', 0))
            base_offset_y = int(request.form.get('offset_y', 0))
            
            tests = calibration.create_offset_test_series(base_offset_x, base_offset_y)
            
            results = []
            for i, (img, desc) in enumerate(tests):
                success = calibration.print_calibration_image(img, desc)
                results.append({
                    'test_number': i + 1,
                    'description': desc,
                    'success': success
                })
                
                if not success:
                    break
                    
                if i < len(tests) - 1:
                    import time
                    time.sleep(1)  # Kurze Pause zwischen Drucken
            
            return jsonify({
                'success': all(r['success'] for r in results),
                'message': f"Offset-Serie ({len(results)} Tests)",
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Calibration series error: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/calibration/info')
    def api_calibration_info():
        """Gibt Kalibrierungs-Informationen zurück"""
        try:
            return jsonify({
                'printer_width_pixels': calibration.width_pixels,
                'printer_width_mm': calibration.width_mm,
                'label_width_mm': calibration.label_width_mm,
                'label_height_mm': calibration.label_height_mm,
                'label_width_px': calibration.label_width_px,
                'label_height_px': calibration.label_height_px,
                'pixels_per_mm': calibration.pixels_per_mm,
                'available_modes': ['border', 'grid', 'rulers', 'corners', 'series']
            })
        except Exception as e:
            return jsonify({'error': str(e)})
