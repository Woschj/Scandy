// IIFE um globalen Scope zu vermeiden
(function() {
    class QuickScan {
        constructor() {
            // Warte auf DOM-Laden
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.init());
            } else {
                this.init();
            }
        }

        init() {
            this.modal = document.getElementById('quickScanModal');
            if (!this.modal) {
                console.error('QuickScan Modal nicht gefunden');
                return;
            }

            this.currentStep = 1;
            this.scanMode = 'scanner';
            this.codeReader = new ZXing.BrowserMultiFormatReader();
            this.isScanning = false;
            this.isProcessing = false;
            
            this.scannedData = {
                item: null,
                worker: null,
                confirmationCode: null
            };
            
            this.setupEventListeners();
            console.log('QuickScan initialisiert');
        }

        setupEventListeners() {
            // Scanner Input Events
            const itemInput = document.getElementById('itemScanInput');
            if (itemInput) {
                itemInput.addEventListener('keyup', (e) => {
                    if (e.key === 'Enter' && e.target.value) {
                        this.handleItemScan(e.target.value);
                        e.target.value = '';
                    }
                });
            }

            const workerInput = document.getElementById('workerScanInput');
            if (workerInput) {
                workerInput.addEventListener('keyup', (e) => {
                    if (e.key === 'Enter' && e.target.value) {
                        this.handleWorkerScan(e.target.value);
                        e.target.value = '';
                    }
                });
            }

            // Modal Events
            this.modal.addEventListener('close', () => {
                this.resetScan();
                this.stopWebcam();
            });

            // Modus-Umschaltung Events
            document.getElementById('scannerModeBtn')?.addEventListener('click', () => this.switchMode('scanner'));
            document.getElementById('webcamModeBtn')?.addEventListener('click', () => this.switchMode('webcam'));
        }

        async switchMode(mode) {
            console.log('Wechsle zu Modus:', mode);
            this.scanMode = mode;
            
            // Update Button States
            document.getElementById('scannerModeBtn').classList.toggle('btn-active', mode === 'scanner');
            document.getElementById('webcamModeBtn').classList.toggle('btn-active', mode === 'webcam');
            
            // Toggle Visibility
            const scannerMode = document.getElementById('step1');
            const webcamMode = document.getElementById('webcamMode');
            
            if (mode === 'webcam') {
                if (webcamMode) {
                    webcamMode.classList.remove('hidden');
                    await this.startWebcam();
                }
                if (scannerMode) scannerMode.classList.add('hidden');
            } else {
                if (webcamMode) webcamMode.classList.add('hidden');
                if (scannerMode) {
                    scannerMode.classList.remove('hidden');
                    const input = document.getElementById('itemScanInput');
                    if (input) {
                        input.value = '';
                        input.focus();
                    }
                }
                this.stopWebcam();
            }
        }

        async startWebcam() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: "environment" } 
                });
                const video = document.getElementById('video');
                if (video) {
                    video.srcObject = stream;
                    await video.play();
                    
                    this.isScanning = true;
                    this.startWebcamScanning();
                }
            } catch (error) {
                this.showError('Webcam nicht verfügbar');
                this.switchMode('scanner');
            }
        }

        stopWebcam() {
            this.isScanning = false;
            const video = document.getElementById('video');
            if (video?.srcObject) {
                video.srcObject.getTracks().forEach(track => track.stop());
                video.srcObject = null;
            }
        }

        async startWebcamScanning() {
            while (this.isScanning) {
                try {
                    const result = await this.codeReader.decodeFromVideoElement(
                        document.getElementById('video')
                    );
                    if (result) {
                        if (this.currentStep === 1) {
                            await this.handleItemScan(result.text);
                        } else if (this.currentStep === 3) {
                            await this.handleWorkerScan(result.text);
                        } else if (this.currentStep === 4) {
                            if (result.text === this.scannedData.finalConfirmationCode) {
                                await this.processLending();
                            }
                        }
                    }
                } catch (error) {
                    // Ignoriere Fehler und scanne weiter
                }
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }

        async handleItemScan(barcode) {
            try {
                // Prüfe ob es ein Bestätigungscode ist
                if (barcode.startsWith('CONFIRM-')) {
                    if (barcode === this.scannedData.confirmationCode) {
                        this.moveToStep(3);
                        // Fokus auf Worker-Scan setzen
                        const workerInput = document.getElementById('workerScanInput');
                        if (workerInput) {
                            workerInput.disabled = false;
                            workerInput.focus();
                        }
                        return;
                    } else if (barcode === this.scannedData.finalConfirmationCode) {
                        this.processLending();
                        return;
                    } else {
                        throw new Error('Ungültiger Bestätigungscode');
                    }
                }

                // Normaler Item-Scan
                console.log('Verarbeite Item-Scan:', barcode);
                const response = await fetch(`/api/scan`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        barcode: barcode,
                        step: 'tool'
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Artikel nicht gefunden');
                }
                
                if (!data.success && data.error) {
                    throw new Error(data.error);
                }
                
                this.scannedData.item = data.item;
                this.updateItemInfo(data.item);
            } catch (error) {
                this.showError(error.message);
            }
        }

        updateItemInfo(item) {
            // Update Step 1 Info
            document.getElementById('scannedItemInfo').classList.remove('hidden');
            document.getElementById('itemDetails').innerHTML = `
                <strong>${item.name}</strong><br>
                ${item.type === 'tool' ? 'Werkzeug' : 'Verbrauchsmaterial'}<br>
                Status: ${item.status || 'Verfügbar'}
            `;
            
            // Update Step 2 Info
            document.getElementById('confirmItemName').textContent = item.name;
            const action = item.status === 'ausgeliehen' ? 'Rückgabe' : 'Ausleihe';
            document.getElementById('confirmItemStatus').textContent = 
                `${item.type === 'tool' ? 'Werkzeug' : 'Verbrauchsmaterial'} - ${action}`;

            // Generiere und zeige Bestätigungsbarcode
            this.generateConfirmationBarcode(item, action);
        }

        async generateConfirmationBarcode(item, action) {
            try {
                const confirmationCode = `CONFIRM-${Date.now()}`;
                this.scannedData.confirmationCode = confirmationCode;
                this.scannedData.action = action.toLowerCase();

                // Zeige Barcode und Anweisungen
                const confirmArea = document.getElementById('step2');
                confirmArea.innerHTML = `
                    <div class="bg-base-200 rounded-lg p-4">
                        <div class="alert alert-info shadow-sm text-sm py-2 mb-3">
                            <div class="flex flex-col">
                                <span id="confirmItemName" class="font-medium">${item.name}</span>
                                <span id="confirmItemStatus" class="text-xs">
                                    ${action} durchführen
                                </span>
                            </div>
                        </div>
                        <div class="flex flex-col items-center">
                            <div class="bg-white p-4 rounded-lg mb-2">
                                <svg id="confirmationBarcode"></svg>
                            </div>
                            <p class="text-sm text-center mb-4">
                                Scannen Sie diesen Barcode oder drücken Sie Enter um die ${action} zu bestätigen
                            </p>
                            <div class="form-control">
                                <input type="text" 
                                       id="confirmInput"
                                       class="input input-bordered w-full text-center" 
                                       placeholder="Enter drücken zum Bestätigen"
                                       autocomplete="off">
                            </div>
                        </div>
                    </div>
                `;

                // Generiere Barcode mit JsBarcode
                JsBarcode("#confirmationBarcode", confirmationCode, {
                    format: "code128",
                    width: 2,
                    height: 100,
                    displayValue: true,
                    text: `${action} bestätigen`,
                    fontOptions: "bold",
                    textAlign: "center",
                    textPosition: "bottom",
                    textMargin: 2,
                    fontSize: 14,
                    background: "#ffffff",
                    lineColor: "#000000",
                    margin: 10
                });

                // Event-Listener für Enter-Taste
                const confirmInput = document.getElementById('confirmInput');
                if (confirmInput) {
                    confirmInput.addEventListener('keyup', (e) => {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            this.moveToStep(3);
                            // Fokus auf Worker-Scan setzen
                            const workerInput = document.getElementById('workerScanInput');
                            if (workerInput) {
                                workerInput.disabled = false;
                                workerInput.focus();
                            }
                        }
                    });
                    // Setze Fokus nach kurzem Delay
                    setTimeout(() => {
                        confirmInput.focus();
                    }, 100);
                }

                this.moveToStep(2);
            } catch (error) {
                this.showError('Fehler beim Generieren des Bestätigungscodes: ' + error.message);
            }
        }

        async handleWorkerScan(barcode) {
            try {
                console.log('Verarbeite Worker-Scan:', barcode);
                const response = await fetch(`/api/scan`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        barcode: barcode,
                        step: 'worker'
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Mitarbeiter nicht gefunden');
                }
                
                if (!data.success && data.error) {
                    throw new Error(data.error);
                }
                
                this.scannedData.worker = data.worker;
                this.updateWorkerInfo(data.worker);
                this.showFinalConfirmation();
            } catch (error) {
                this.showError(error.message);
            }
        }

        updateWorkerInfo(worker) {
            document.getElementById('scannedWorkerInfo').classList.remove('hidden');
            document.getElementById('workerName').textContent = 
                `${worker.firstname} ${worker.lastname}`;
            document.getElementById('workerDepartment').textContent = 
                worker.department || 'Keine Abteilung';
        }

        showFinalConfirmation() {
            const action = this.scannedData.item.status === 'ausgeliehen' ? 'Rückgabe' : 'Ausleihe';
            const confirmationCode = `CONFIRM-FINAL-${Date.now()}`;
            this.scannedData.finalConfirmationCode = confirmationCode;

            // Zeige finale Bestätigung
            const confirmArea = document.getElementById('step4');
            confirmArea.innerHTML = `
                <div class="bg-base-200 rounded-lg p-4">
                    <div class="alert ${action === 'Rückgabe' ? 'alert-warning' : 'alert-info'} shadow-sm text-sm py-2 mb-3">
                        <div class="flex flex-col gap-2">
                            <h3 class="font-bold">Finale Bestätigung - ${action}</h3>
                            <div class="divider my-0"></div>
                            <div>
                                <p class="font-medium">Werkzeug/Material:</p>
                                <p>${this.scannedData.item.name}</p>
                                <p class="text-xs opacity-70">Barcode: ${this.scannedData.item.barcode}</p>
                                <p class="text-xs opacity-70">Status: ${this.scannedData.item.status}</p>
                            </div>
                            <div class="divider my-0"></div>
                            <div>
                                <p class="font-medium">Mitarbeiter:</p>
                                <p>${this.scannedData.worker.firstname} ${this.scannedData.worker.lastname}</p>
                                <p class="text-xs opacity-70">${this.scannedData.worker.department || ''}</p>
                                <p class="text-xs opacity-70">Barcode: ${this.scannedData.worker.barcode}</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex flex-col items-center">
                        <div class="bg-white p-4 rounded-lg mb-2">
                            <svg id="finalConfirmationBarcode"></svg>
                        </div>
                        <p class="text-sm text-center mb-4">
                            Scannen Sie diesen Barcode oder drücken Sie Enter um die ${action} abzuschließen
                        </p>
                        <div class="form-control">
                            <input type="text" 
                                   id="finalConfirmInput"
                                   class="input input-bordered w-full text-center" 
                                   placeholder="Enter drücken zum Bestätigen"
                                   autocomplete="off">
                        </div>
                    </div>
                </div>
            `;

            // Generiere Barcode
            JsBarcode("#finalConfirmationBarcode", confirmationCode, {
                format: "code128",
                width: 2,
                height: 100,
                displayValue: true,
                text: `${action} abschließen`,
                fontOptions: "bold",
                textAlign: "center",
                textPosition: "bottom",
                textMargin: 2,
                fontSize: 14,
                background: "#ffffff",
                lineColor: "#000000",
                margin: 10
            });

            // Event-Listener für Enter-Taste
            const finalConfirmInput = document.getElementById('finalConfirmInput');
            if (finalConfirmInput) {
                finalConfirmInput.addEventListener('keyup', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        this.processLending();
                    }
                });
                // Setze Fokus nach kurzem Delay
                setTimeout(() => {
                    finalConfirmInput.focus();
                }, 100);
            }

            this.moveToStep(4);
        }

        moveToStep(step) {
            console.log('Wechsle zu Schritt:', step);
            this.currentStep = step;
            
            // Update Progress Steps
            document.querySelectorAll('.steps-horizontal .step').forEach((el, index) => {
                el.classList.toggle('step-primary', index < step);
            });
            
            // Show/Hide Steps
            ['step1', 'step2', 'step3', 'step4'].forEach((stepId, index) => {
                const stepElement = document.getElementById(stepId);
                if (stepElement) {
                    stepElement.classList.toggle('hidden', index + 1 !== step);
                }
            });
            
            // Focus Management
            setTimeout(() => {
                if (step === 1) {
                    const input = document.getElementById('itemScanInput');
                    if (input) {
                        input.disabled = false;
                        input.focus();
                    }
                } else if (step === 2) {
                    const input = document.getElementById('confirmInput');
                    if (input) {
                        input.disabled = false;
                        input.focus();
                    }
                } else if (step === 3) {
                    const input = document.getElementById('workerScanInput');
                    if (input) {
                        input.disabled = false;
                        input.focus();
                    }
                } else if (step === 4) {
                    const input = document.getElementById('finalConfirmInput');
                    if (input) {
                        input.disabled = false;
                        input.focus();
                    }
                }
            }, 100);
        }

        async processLending() {
            if (this.isProcessing) {
                console.log('Verarbeitung läuft bereits...');
                return;
            }

            if (!this.scannedData.item || !this.scannedData.worker) {
                this.showError('Unvollständige Daten für Ausleihe');
                return;
            }
            
            try {
                this.isProcessing = true;
                console.log('Verarbeite Ausleihe/Rückgabe:', {
                    tool: this.scannedData.item,
                    worker: this.scannedData.worker
                });

                const response = await fetch('/api/quickscan/process_lending', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        tool_barcode: this.scannedData.item.barcode,
                        worker_barcode: this.scannedData.worker.barcode
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Fehler beim Verarbeiten');
                }
                
                if (!data.success && data.error) {
                    throw new Error(data.error);
                }
                
                this.showSuccess(data.message || 'Vorgang erfolgreich abgeschlossen');
                this.modal.close();
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } catch (error) {
                this.showError(error.message);
                this.isProcessing = false;
            }
        }

        resetScan() {
            this.currentStep = 1;
            this.isProcessing = false;
            this.scannedData = { 
                item: null, 
                worker: null, 
                confirmationCode: null,
                finalConfirmationCode: null 
            };
            this.moveToStep(1);
            
            // Reset inputs
            ['itemScanInput', 'workerScanInput', 'confirmInput', 'finalConfirmInput'].forEach(id => {
                const input = document.getElementById(id);
                if (input) {
                    input.value = '';
                    input.disabled = false;
                }
            });
            
            // Reset info displays
            ['scannedItemInfo', 'scannedWorkerInfo'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.classList.add('hidden');
            });
        }

        showError(message) {
            console.error('Fehler:', message);
            window.toast?.show(message, 'error') || alert(message);
        }

        showSuccess(message) {
            console.log('Erfolg:', message);
            window.toast?.show(message, 'success') || alert(message);
        }
    }

    // Initialisierung
    window.quickScan = new QuickScan();
})(); 