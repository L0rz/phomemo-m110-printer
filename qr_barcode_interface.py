"""
QR/Barcode Web Interface Erweiterung für Phomemo M110
Fügt dem bestehenden Interface neue Funktionalität hinzu
"""

QR_BARCODE_INTERFACE = '''
            <!-- QR-Code & Barcode Printing -->
            <div class="card">
                <h2>🔲 QR-Codes & Barcodes</h2>
                
                <div class="code-help" style="margin: 10px 0; padding: 15px; background: #e8f4fd; border-radius: 8px; border-left: 4px solid #2196F3;">
                    <h4 style="margin: 0 0 10px 0; color: #1976D2;">📖 Code-Syntax:</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-family: monospace; font-size: 13px;">
                        <div>
                            <strong>QR-Codes:</strong><br>
                            <code>#qr#Inhalt#qr#</code> → Standard QR<br>
                            <code>#qr:150#Größer#qr#</code> → 150px QR<br>
                            <code>#qr#https://example.com#qr#</code> → URL QR
                        </div>
                        <div>
                            <strong>Barcodes:</strong><br>
                            <code>#bar#1234567890#bar#</code> → Standard Barcode<br>
                            <code>#bar:80#Code#bar#</code> → 80px hoher Barcode<br>
                            <code>#bar#ART-12345#bar#</code> → Artikel-Code
                        </div>
                    </div>
                    <div style="margin-top: 10px; color: #555;">
                        <strong>💡 Tipps:</strong> Codes werden automatisch zentriert. Text kann vor/nach Codes stehen. Mehrere Codes pro Label möglich.
                    </div>
                </div>
                
                <textarea id="codeTextInput" rows="6" placeholder="Text mit QR-Codes und Barcodes eingeben..." oninput="debouncedCodePreview()">Produkt Information:

#qr#https://shop.example.com/product/123#qr#

Artikel-Nr: #bar#ART-456789#bar#

Datum: $TIME$</textarea>
                
                <div class="grid" style="gap: 10px; margin: 10px 0;">
                    <div>
                        <label>Schriftgröße:</label>
                        <select id="codeFontSize" onchange="updateCodePreview()">
                            <option value="16">Klein (16px)</option>
                            <option value="20" selected>Normal (20px)</option>
                            <option value="24">Groß (24px)</option>
                            <option value="28">Extra Groß (28px)</option>
                        </select>
                    </div>
                    <div>
                        <label>Ausrichtung:</label>
                        <select id="codeAlignment" onchange="updateCodePreview()">
                            <option value="left">Links</option>
                            <option value="center" selected>Zentriert</option>
                            <option value="right">Rechts</option>
                        </select>
                    </div>
                </div>
                
                <div class="grid" style="gap: 10px;">
                    <button onclick="previewCodeText()" class="btn">🔍 Vorschau mit Codes</button>
                    <button onclick="printCodeText(false)" class="btn-primary">📄 In Queue</button>
                    <button onclick="printCodeText(true)" class="btn-warning">⚡ Sofort drucken</button>
                    <button onclick="showCodeSyntaxHelp()" class="btn" style="background: #4CAF50; color: white;">📖 Syntax-Hilfe</button>
                </div>
                
                <!-- Code Preview Container -->
                <div id="codePreview" class="preview-container" style="display: none; margin-top: 15px;">
                    <h4>🔍 Vorschau mit Codes:</h4>
                    <div class="preview-image-container">
                        <img id="codePreviewImage" style="max-width: 100%; border: 2px solid #ddd; border-radius: 5px; background: white;">
                    </div>
                    <div id="codePreviewInfo" class="preview-info"></div>
                </div>
            </div>
'''

QR_BARCODE_JAVASCRIPT = '''
        // QR/Barcode spezifische Funktionen
        let codePreviewDebounceTimer;
        
        function debouncedCodePreview() {
            clearTimeout(codePreviewDebounceTimer);
            codePreviewDebounceTimer = setTimeout(updateCodePreview, 500);
        }
        
        function updateCodePreview() {
            const text = document.getElementById('codeTextInput').value;
            if (text.trim() && (text.includes('#qr#') || text.includes('#bar#'))) {
                previewCodeText();
            }
        }
        
        async function previewCodeText() {
            const text = document.getElementById('codeTextInput').value;
            const fontSize = document.getElementById('codeFontSize').value;
            const alignment = document.getElementById('codeAlignment').value;
            
            if (!text.trim()) {
                alert('Bitte Text eingeben');
                return;
            }
            
            showLoading('Erstelle Vorschau mit Codes...');
            
            const formData = new FormData();
            formData.append('text', text);
            formData.append('font_size', fontSize);
            formData.append('alignment', alignment);
            
            try {
                const response = await fetch('/api/preview-text-with-codes', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                hideLoading();
                
                if (result.success) {
                    const previewContainer = document.getElementById('codePreview');
                    const previewImage = document.getElementById('codePreviewImage');
                    const previewInfo = document.getElementById('codePreviewInfo');
                    
                    previewImage.src = 'data:image/png;base64,' + result.preview_base64;
                    previewContainer.style.display = 'block';
                    
                    // Info anzeigen
                    const info = result.info;
                    previewInfo.innerHTML = `
                        <strong>📐 Abmessungen:</strong> ${info.width}×${info.height}px<br>
                        <strong>🔤 Schrift:</strong> ${info.font_size}px, ${info.alignment}<br>
                        <strong>🔲 Codes gefunden:</strong> ${info.codes_found}<br>
                        ${info.codes && info.codes.length > 0 ? 
                            '<strong>📋 Code-Details:</strong><br>' + 
                            info.codes.map(code => 
                                `&nbsp;&nbsp;• ${code.type.toUpperCase()}: "${code.content}" (${code.size || code.height || 'default'}px)`
                            ).join('<br>')
                            : ''
                        }
                    `;
                    
                    // Scroll to preview
                    previewContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                } else {
                    alert('Vorschau-Fehler: ' + (result.error || 'Unbekannter Fehler'));
                }
            } catch (error) {
                hideLoading();
                alert('Netzwerk-Fehler: ' + error.message);
            }
        }
        
        async function printCodeText(immediate = false) {
            const text = document.getElementById('codeTextInput').value;
            const fontSize = document.getElementById('codeFontSize').value;
            const alignment = document.getElementById('codeAlignment').value;
            
            if (!text.trim()) {
                alert('Bitte Text eingeben');
                return;
            }
            
            showLoading(immediate ? 'Drucke Text mit Codes...' : 'Füge zu Queue hinzu...');
            
            const formData = new FormData();
            formData.append('text', text);
            formData.append('font_size', fontSize);
            formData.append('alignment', alignment);
            formData.append('immediate', immediate.toString());
            
            try {
                const response = await fetch('/api/print-text-with-codes', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                hideLoading();
                
                if (result.success) {
                    const message = immediate ? 
                        'Text mit Codes erfolgreich gedruckt!' : 
                        `Text mit Codes zur Queue hinzugefügt (Job ID: ${result.job_id})`;
                    showMessage(message, 'success');
                    
                    // Statistiken aktualisieren
                    setTimeout(updateStatus, 1000);
                } else {
                    showMessage('Fehler: ' + (result.error || result.message || 'Unbekannter Fehler'), 'error');
                }
            } catch (error) {
                hideLoading();
                showMessage('Netzwerk-Fehler: ' + error.message, 'error');
            }
        }
        
        async function showCodeSyntaxHelp() {
            try {
                const response = await fetch('/api/code-syntax-help');
                const result = await response.json();
                
                if (result.success) {
                    const helpText = result.syntax_help;
                    const examples = result.examples;
                    
                    const helpWindow = window.open('', '_blank', 'width=600,height=700,scrollbars=yes');
                    helpWindow.document.write(`
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>QR/Barcode Syntax-Hilfe</title>
                            <style>
                                body { font-family: Arial, sans-serif; padding: 20px; }
                                pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
                                code { background: #e8e8e8; padding: 2px 4px; border-radius: 3px; }
                                .examples { background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 15px 0; }
                                h1 { color: #333; }
                                h2 { color: #555; }
                            </style>
                        </head>
                        <body>
                            <h1>🔲 QR-Code & Barcode Syntax-Hilfe</h1>
                            <pre>${helpText}</pre>
                            
                            <h2>📝 Beispiele zum Kopieren:</h2>
                            <div class="examples">
                                ${examples.map(ex => `<code>${ex}</code>`).join('<br><br>')}
                            </div>
                            
                            <h2>🌐 Spezielle QR-Codes:</h2>
                            <div class="examples">
                                <strong>WLAN:</strong><br>
                                <code>#qr#WIFI:S:MeinWLAN;T:WPA;P:passwort123;H:false;;#qr#</code><br><br>
                                
                                <strong>vCard Kontakt:</strong><br>
                                <code>#qr#BEGIN:VCARD\\nFN:Max Mustermann\\nTEL:+49123456789\\nEMAIL:max@example.com\\nEND:VCARD#qr#</code><br><br>
                                
                                <strong>SMS:</strong><br>
                                <code>#qr#SMSTO:+49123456789:Hallo#qr#</code><br><br>
                                
                                <strong>E-Mail:</strong><br>
                                <code>#qr#mailto:test@example.com?subject=Betreff&body=Nachricht#qr#</code>
                            </div>
                            
                            <button onclick="window.close()" style="margin-top: 20px; padding: 10px 20px; background: #2196F3; color: white; border: none; border-radius: 5px;">Schließen</button>
                        </body>
                        </html>
                    `);
                    helpWindow.document.close();
                } else {
                    alert('Fehler beim Laden der Syntax-Hilfe: ' + result.error);
                }
            } catch (error) {
                alert('Netzwerk-Fehler beim Laden der Syntax-Hilfe: ' + error.message);
            }
        }
'''

# Quick Templates für häufige QR/Barcode-Anwendungen
QR_BARCODE_TEMPLATES = {
    'product_label': {
        'name': 'Produkt-Etikett',
        'template': '''Produkt: {product_name}

#qr#{product_url}#qr#

Artikel: #bar#{article_number}#bar#

Preis: {price}€''',
        'fields': ['product_name', 'product_url', 'article_number', 'price']
    },
    
    'event_ticket': {
        'name': 'Event-Ticket',
        'template': '''🎫 {event_name}

#qr#EVENT:{event_date};LOC:{location};PRICE:{price}EUR#qr#

Ticket: #bar#{ticket_number}#bar#

{event_date} - {location}''',
        'fields': ['event_name', 'event_date', 'location', 'price', 'ticket_number']
    },
    
    'wifi_access': {
        'name': 'WLAN-Zugang',
        'template': '''📶 WLAN: {wifi_name}

#qr#WIFI:S:{wifi_name};T:WPA;P:{wifi_password};H:false;;#qr#

Passwort: {wifi_password}

Einfach QR-Code scannen!''',
        'fields': ['wifi_name', 'wifi_password']
    },
    
    'contact_card': {
        'name': 'Kontakt-Karte',
        'template': '''👤 {name}

#qr#BEGIN:VCARD
FN:{name}
TEL:{phone}
EMAIL:{email}
ORG:{company}
END:VCARD#qr#

📞 {phone}
✉️ {email}''',
        'fields': ['name', 'phone', 'email', 'company']
    }
}

if __name__ == "__main__":
    print("QR/Barcode Web Interface Komponenten:")
    print("- QR_BARCODE_INTERFACE: HTML für neue Sektion")
    print("- QR_BARCODE_JAVASCRIPT: JavaScript-Funktionen")
    print("- QR_BARCODE_TEMPLATES: Vorgefertigte Templates")
