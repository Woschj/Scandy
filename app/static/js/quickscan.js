const QuickScan = {
    currentStep: 1,
    scannedItem: null,
    scannedWorker: null,
    confirmationBarcode: null,
    
    init() {
        this.reset();
        this.setupEventListeners();
    },
    
    setupEventListeners() {
        // Event-Listener für Item-Scan
        const itemInput = document.getElementById('itemScanInput');
        if (itemInput) {
            itemInput.addEventListener('keypress', async (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const barcode = e.target.value.trim();
                    
                    // Wenn ein Bestätigungsbarcode aktiv ist, prüfen ob Enter oder der richtige Barcode
                    if (this.confirmationBarcode) {
                        if (barcode === '' || barcode === this.confirmationBarcode) {
                            this.confirmItem();
                        }
                    } else if (barcode.length >= 4) {
                        await this.handleItemScan(barcode);
                    }
                    e.target.value = '';
                }
            });
        }
        
        // Event-Listener für Worker-Scan
        const workerInput = document.getElementById('workerScanInput');
        if (workerInput) {
            workerInput.addEventListener('keypress', async (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const barcode = e.target.value.trim();
                    
                    // Wenn ein Bestätigungsbarcode aktiv ist, prüfen ob Enter oder der richtige Barcode
                    if (this.confirmationBarcode) {
                        if (barcode === '' || barcode === this.confirmationBarcode) {
                            this.processAction();
                        }
                    } else if (barcode.length >= 4) {
                        await this.handleWorkerScan(barcode);
                    }
                    e.target.value = '';
                }
            });
        }
    },
    
    async handleItemScan(barcode) {
        try {
            // Prüfe zuerst ob es ein Werkzeug ist
            const toolResponse = await fetch(`/api/inventory/tools/${barcode}`);
            let data;
            
            if (toolResponse.ok) {
                const response = await toolResponse.json();
                if (response.success) {
                    data = response.data;
                    data.itemType = 'tool';
                } else {
                    showToast('error', response.message || 'Fehler beim Laden des Werkzeugs');
                    return;
                }
            } else {
                // Wenn kein Werkzeug gefunden, prüfe ob es ein Verbrauchsmaterial ist
                const consumableResponse = await fetch(`/api/inventory/consumables/${barcode}`);
                if (consumableResponse.ok) {
                    const response = await consumableResponse.json();
                    if (response.success) {
                        data = response.data;
                        data.itemType = 'consumable';
                    } else {
                        showToast('error', response.message || 'Fehler beim Laden des Verbrauchsmaterials');
                        return;
                    }
                } else {
                    showToast('error', 'Artikel nicht gefunden');
                    return;
                }
            }
            
            this.scannedItem = data;
            
            // Bestimme Aktion und Farbe basierend auf Artikeltyp und Status
            let action, actionText, statusClass, details;
            
            if (data.itemType === 'tool') {
                if (data.current_status === 'verfügbar') {
                    action = 'lend';
                    actionText = 'Wird ausgeliehen';
                    statusClass = 'badge-success';
                } else if (data.current_status === 'ausgeliehen') {
                    action = 'return';
                    actionText = 'Wird zurückgegeben';
                    statusClass = 'badge-warning';
                } else if (data.current_status === 'defekt') {
                    action = null;
                    actionText = 'Defekt - keine Aktion möglich';
                    statusClass = 'badge-error';
                }
                details = `${data.category} | ${data.location}`;
            } else {
                action = 'consume';
                actionText = 'Wird ausgegeben';
                statusClass = data.quantity <= data.min_quantity ? 'badge-warning' : 'badge-success';
                details = `Bestand: ${data.quantity} | Mindestbestand: ${data.min_quantity}`;
            }
            
            // Zeige Artikeldetails
            document.getElementById('itemName').textContent = data.name;
            document.getElementById('itemStatus').className = `badge badge-lg ${statusClass}`;
            document.getElementById('itemStatus').textContent = data.status_text;
            document.getElementById('itemAction').textContent = actionText;
            document.getElementById('itemDetails').textContent = details;
            
            if (action) {
                // Generiere Bestätigungsbarcode
                this.confirmationBarcode = Math.random().toString(36).substring(2, 8).toUpperCase();
                const canvas = document.getElementById('itemConfirmBarcode');
                JsBarcode(canvas, this.confirmationBarcode, {
                    format: "CODE128",
                    width: 2,
                    height: 50,
                    displayValue: true
                });
                document.getElementById('scannedItemInfo').classList.remove('hidden');
            } else {
                showToast('error', 'Keine Aktion für diesen Artikel möglich');
            }
            
        } catch (error) {
            showToast('error', 'Fehler beim Scannen des Artikels');
            console.error(error);
        }
    },
    
    confirmItem() {
        this.confirmationBarcode = null;
        this.goToStep(2);
        document.getElementById('workerScanInput').focus();
    },
    
    async handleWorkerScan(barcode) {
        try {
            console.log('Verarbeite Worker-Scan:', barcode);
            const response = await fetch(`/api/inventory/workers/${barcode}`);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error('Mitarbeiter nicht gefunden');
            }
            
            this.scannedWorker = result;
            console.log('Gescannter Mitarbeiter:', this.scannedWorker);
            
            // Aktualisiere finale Übersicht
            document.getElementById('finalItemInfo').innerHTML = `
                <div class="font-bold">${this.scannedItem.name}</div>
                <div class="text-sm opacity-70">${this.scannedItem.itemType === 'tool' ? 'Werkzeug' : 'Verbrauchsmaterial'}</div>
                <div class="badge badge-sm mt-2">${this.determineAction() === 'lend' ? 'Ausleihen' : 
                                                 this.determineAction() === 'return' ? 'Rückgabe' : 'Ausgabe'}</div>
            `;
            
            document.getElementById('finalWorkerInfo').innerHTML = `
                <div class="font-bold">${this.scannedWorker.firstname} ${this.scannedWorker.lastname}</div>
                <div class="text-sm opacity-70">${this.scannedWorker.department || ''}</div>
            `;
            
            // Generiere finalen Bestätigungsbarcode
            this.confirmationBarcode = Math.random().toString(36).substring(2, 8).toUpperCase();
            const canvas = document.getElementById('finalConfirmBarcode');
            JsBarcode(canvas, this.confirmationBarcode, {
                format: "CODE128",
                width: 2,
                height: 50,
                displayValue: true
            });
            
            document.getElementById('workerInfo').classList.remove('hidden');
            
            // Event-Listener für Enter-Taste oder Barcode-Scan zur Bestätigung
            const workerInput = document.getElementById('workerScanInput');
            workerInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const scannedCode = e.target.value.trim();
                    if (scannedCode === '' || scannedCode === this.confirmationBarcode) {
                        this.processAction();
                    }
                    e.target.value = '';
                }
            });
            
        } catch (error) {
            console.error('Worker-Scan Fehler:', error);
            showToast('error', 'Fehler: ' + error.message);
        }
    },
    
    async processAction() {
        try {
            if (!this.scannedItem || !this.scannedWorker) {
                showToast('error', 'Bitte wählen Sie einen Artikel und einen Mitarbeiter aus');
                return;
            }

            const action = this.determineAction();
            const requestData = {
                item_barcode: this.scannedItem.barcode,
                worker_barcode: this.scannedWorker.barcode,
                action: action,
                quantity: this.scannedItem.itemType === 'consumable' ? 1 : undefined
            };
            
            console.log('Sende Anfrage:', requestData);
            
            // Headers vorbereiten
            const headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            };

            // CSRF-Token nur hinzufügen wenn verfügbar
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }
            
            const response = await fetch('/api/quickscan/process_lending', {
                method: 'POST',
                headers: headers,
                credentials: 'same-origin',
                body: JSON.stringify(requestData)
            });
            
            // Debug-Informationen
            console.log('Response Status:', response.status);
            console.log('Response Headers:', Object.fromEntries(response.headers.entries()));
            
            // Lese zuerst den rohen Text
            const responseText = await response.text();
            console.log('Raw Response:', responseText);
            
            // Versuche den Text als JSON zu parsen
            let result;
            try {
                result = JSON.parse(responseText);
            } catch (parseError) {
                console.error('JSON Parse Error:', parseError);
                if (response.redirected) {
                    showToast('error', 'Unerwartete Weiterleitung');
                    return;
                }
                throw new Error('Ungültige Server-Antwort: ' + responseText);
            }
            
            // Prüfe auf HTTP-Fehler
            if (!response.ok) {
                throw new Error(result.message || `HTTP error! status: ${response.status}`);
            }
            
            if (result.success) {
                document.getElementById('successMessage').textContent = result.message;
                this.goToStep(3); // Success Step
                showToast('success', result.message);
                
                // Verzögere das Neuladen der Seite
                setTimeout(() => {
                    window.location.reload();
                }, 3000);
            } else {
                throw new Error(result.message || 'Fehler beim Verarbeiten der Aktion');
            }
            
        } catch (error) {
            console.error('Fehler in processAction:', error);
            showToast('error', error.message || 'Fehler beim Verarbeiten der Aktion');
            // NICHT neuladen bei Fehler
        }
    },
    
    determineAction() {
        if (this.scannedItem.itemType === 'tool') {
            return this.scannedItem.current_status === 'verfügbar' ? 'lend' : 'return';
        }
        return 'consume';
    },
    
    goToStep(step) {
        // Verstecke alle Schritte
        document.querySelectorAll('.scan-step').forEach(el => el.classList.add('hidden'));
        
        // Zeige aktuellen Schritt
        const stepElement = document.getElementById(step === 3 ? 'successStep' : `step${step}`);
        if (stepElement) {
            stepElement.classList.remove('hidden');
        }
        
        // Aktualisiere Fortschrittsanzeige
        document.querySelectorAll('.steps .step').forEach((el, index) => {
            if (index + 1 <= step) {
                el.classList.add('step-primary');
            } else {
                el.classList.remove('step-primary');
            }
        });
        
        this.currentStep = step;
    },
    
    reset() {
        this.scannedItem = null;
        this.scannedWorker = null;
        this.confirmationBarcode = null;
        this.goToStep(1);
        
        // Reset UI
        document.querySelectorAll('.scan-step').forEach(el => el.classList.add('hidden'));
        document.getElementById('step1').classList.remove('hidden');
        document.getElementById('itemScanInput').value = '';
        document.getElementById('workerScanInput').value = '';
        document.getElementById('itemScanInput').focus();
    }
};

// QuickScan initialisieren wenn Modal geöffnet wird
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('quickScanModal');
    if (modal) {
        modal.addEventListener('show', () => {
            QuickScan.init();
        });
    }
}); 