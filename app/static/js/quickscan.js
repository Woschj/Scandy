const QuickScan = {
    currentStep: 1,
    scannedItem: null,
    scannedWorker: null,
    confirmationBarcode: null,
    lastKeyTime: 0,
    keyBuffer: '',
    isInitialized: false,
    
    init() {
        if (this.isInitialized) {
            this.reset();
        } else {
            this.setupEventListeners();
            this.isInitialized = true;
        }
        this.focusCurrentInput();
        console.log('QuickScan initialisiert');
    },
    
    setupEventListeners() {
        // Event-Listener für Item-Scan
        const itemInput = document.getElementById('itemScanInput');
        if (itemInput) {
            // Keypress Event für normale Eingaben
            itemInput.addEventListener('keypress', (e) => {
                console.log('Keypress Event:', e.key, 'KeyCode:', e.keyCode);
                this.handleKeyInput(e, itemInput);
            });

            // Input Event für Scanner-Eingaben
            itemInput.addEventListener('input', (e) => {
                console.log('Input Event:', e.target.value);
                if (e.target.value) {
                    this.handleScannerInput(e.target.value, itemInput);
                    e.target.value = ''; // Input zurücksetzen
                }
            });
        }
        
        // Event-Listener für Worker-Scan
        const workerInput = document.getElementById('workerScanInput');
        if (workerInput) {
            // Keypress Event für normale Eingaben
            workerInput.addEventListener('keypress', (e) => {
                console.log('Keypress Event:', e.key, 'KeyCode:', e.keyCode);
                this.handleKeyInput(e, workerInput);
            });

            // Input Event für Scanner-Eingaben
            workerInput.addEventListener('input', (e) => {
                console.log('Input Event:', e.target.value);
                if (e.target.value) {
                    this.handleScannerInput(e.target.value, workerInput);
                    e.target.value = ''; // Input zurücksetzen
                }
            });
        }

        // Event-Listener für Modal-Schließen
        const modal = document.getElementById('quickScanModal');
        if (modal) {
            modal.addEventListener('close', () => {
                this.reset();
            });
        }
    },

    handleKeyInput(e, input) {
        const currentTime = new Date().getTime();
        const timeDiff = currentTime - this.lastKeyTime;
        this.lastKeyTime = currentTime;

        console.log('TimeDiff:', timeDiff, 'Buffer:', this.keyBuffer);

        if (e.key === 'Enter') {
            e.preventDefault();
            if (this.keyBuffer) {
                this.handleScannerInput(this.keyBuffer, input);
                this.keyBuffer = '';
            }
        } else {
            this.keyBuffer += e.key;
        }
    },

    handleScannerInput(barcode, input) {
        console.log('Scanner Input erkannt:', barcode);
        showToast('info', 'Barcode erkannt: ' + barcode);

        if (this.confirmationBarcode && barcode === this.confirmationBarcode) {
            console.log('Bestätigungscode erkannt');
            if (input.id === 'itemScanInput') {
                this.confirmItem();
            } else {
                this.processAction();
            }
        } else if (barcode.length >= 4) {
            if (input.id === 'itemScanInput') {
                this.handleItemScan(barcode);
            } else {
                this.handleWorkerScan(barcode);
            }
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
            
            // Aktualisiere die Info-Karte
            const itemName = document.getElementById('itemName');
            const itemStatusContainer = document.getElementById('itemStatusContainer');
            const itemStatus = document.getElementById('itemStatus');
            const itemAction = document.getElementById('itemAction');
            const itemDetails = document.getElementById('itemDetails');

            itemName.textContent = data.name;
            itemName.classList.remove('opacity-50');
            
            itemStatus.className = `badge badge-lg ${statusClass}`;
            itemStatus.textContent = data.status_text;
            itemAction.textContent = actionText;
            itemStatusContainer.style.display = 'flex';
            
            itemDetails.textContent = details;
            itemDetails.classList.remove('opacity-50');
            
            if (action) {
                showToast('success', 'Artikel erkannt: ' + data.name);
                
                // Generiere Bestätigungsbarcode
                this.confirmationBarcode = Math.random().toString(36).substring(2, 8).toUpperCase();
                const canvas = document.getElementById('itemConfirmBarcode');
                JsBarcode(canvas, this.confirmationBarcode, {
                    format: "CODE128",
                    width: 2,
                    height: 50,
                    displayValue: true
                });
                document.getElementById('itemConfirm').classList.remove('hidden');
            } else {
                showToast('error', 'Keine Aktion für diesen Artikel möglich');
            }
            
        } catch (error) {
            showToast('error', 'Fehler beim Scannen des Artikels');
            console.error(error);
        }
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
            
            // Aktualisiere Worker-Bereich in der Info-Karte
            const workerName = document.getElementById('workerName');
            const workerDepartment = document.getElementById('workerDepartment');
            
            workerName.textContent = `${result.firstname} ${result.lastname}`;
            workerName.classList.remove('opacity-50');
            
            workerDepartment.textContent = result.department || 'Keine Abteilung';
            workerDepartment.classList.remove('opacity-50');
            
            showToast('success', 'Mitarbeiter erkannt: ' + result.firstname + ' ' + result.lastname);
            
            // Generiere Bestätigungsbarcode
            this.confirmationBarcode = Math.random().toString(36).substring(2, 8).toUpperCase();
            const canvas = document.getElementById('finalConfirmBarcode');
            JsBarcode(canvas, this.confirmationBarcode, {
                format: "CODE128",
                width: 2,
                height: 50,
                displayValue: true
            });
            document.getElementById('finalConfirm').classList.remove('hidden');
            
            // Direkt die Aktion ausführen
            await this.processAction();
            
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
            
            const headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            };
            
            const requestData = {
                item_barcode: this.scannedItem.barcode,
                worker_barcode: this.scannedWorker.barcode,
                action: action,
                quantity: this.scannedItem.itemType === 'consumable' ? 1 : undefined
            };
            
            const response = await fetch('/api/quickscan/process_lending', {
                method: 'POST',
                headers: headers,
                credentials: 'same-origin',
                body: JSON.stringify(requestData)
            });
            
            const contentType = response.headers.get('content-type');
            const responseText = await response.text();
            
            if (contentType?.includes('text/html')) {
                throw new Error('Sitzung abgelaufen - Bitte laden Sie die Seite neu');
            }
            
            let result;
            try {
                result = JSON.parse(responseText);
            } catch (e) {
                throw new Error('Ungültige Server-Antwort');
            }
            
            if (result.success) {
                showToast('success', 'Vorgang erfolgreich abgeschlossen');
                setTimeout(() => {
                    const modal = document.getElementById('quickScanModal');
                    if (modal) {
                        modal.close();
                    }
                    this.reset();
                }, 2000);
            } else {
                throw new Error(result.message || 'Unbekannter Fehler');
            }
        } catch (error) {
            console.error('Fehler in processAction:', error);
            showToast('error', error.message || 'Fehler beim Verarbeiten der Aktion');
        }
    },

    determineAction() {
        if (this.scannedItem.itemType === 'tool') {
            return this.scannedItem.current_status === 'verfügbar' ? 'lend' : 'return';
        }
        return 'consume';
    },
    
    goToStep(step) {
        document.querySelectorAll('.scan-step').forEach(el => el.classList.add('hidden'));
        document.getElementById(`step${step}`).classList.remove('hidden');
        
        document.querySelectorAll('.steps .step').forEach((el, index) => {
            if (index + 1 <= step) {
                el.classList.add('step-primary');
            } else {
                el.classList.remove('step-primary');
            }
        });
        
        this.currentStep = step;
        this.focusCurrentInput();
    },
    
    focusCurrentInput() {
        const currentInput = this.currentStep === 1 ? 'itemScanInput' : 'workerScanInput';
        const input = document.getElementById(currentInput);
        if (input) {
            input.focus();
        }
    },
    
    reset() {
        this.scannedItem = null;
        this.scannedWorker = null;
        this.confirmationBarcode = null;
        this.keyBuffer = '';
        this.goToStep(1);
        
        // Reset UI
        document.getElementById('itemScanInput').value = '';
        document.getElementById('workerScanInput').value = '';
        document.getElementById('itemConfirm').classList.add('hidden');
        document.getElementById('finalConfirm').classList.add('hidden');
        
        // Reset Info-Karte
        const itemName = document.getElementById('itemName');
        const itemStatusContainer = document.getElementById('itemStatusContainer');
        const itemDetails = document.getElementById('itemDetails');
        const workerName = document.getElementById('workerName');
        const workerDepartment = document.getElementById('workerDepartment');

        itemName.textContent = 'Noch kein Artikel gescannt';
        itemName.classList.add('opacity-50');
        itemStatusContainer.style.display = 'none';
        itemDetails.textContent = 'Details werden nach Scan angezeigt';
        itemDetails.classList.add('opacity-50');
        workerName.textContent = 'Noch kein Mitarbeiter gescannt';
        workerName.classList.add('opacity-50');
        workerDepartment.textContent = 'Abteilung wird nach Scan angezeigt';
        workerDepartment.classList.add('opacity-50');
        
        this.focusCurrentInput();
    },

    confirmItem() {
        this.confirmationBarcode = null;
        document.getElementById('itemConfirm').classList.add('hidden');
        this.goToStep(2);
        this.focusCurrentInput();
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