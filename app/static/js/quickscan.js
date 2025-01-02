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
            
            this.scannedData = {
                item: null,
                worker: null,
                action: null
            };
            
            this.setupEventListeners();
        }

        setupEventListeners() {
            // Scanner Input Events
            document.getElementById('itemScanInput').addEventListener('keyup', (e) => {
                if (e.key === 'Enter' && e.target.value) {
                    this.handleItemScan(e.target.value);
                }
            });

            document.getElementById('workerScanInput').addEventListener('keyup', (e) => {
                if (e.key === 'Enter' && e.target.value) {
                    this.handleWorkerScan(e.target.value);
                }
            });

            // Modal Events
            this.modal.addEventListener('close', () => {
                this.resetScan();
                this.stopWebcam();
            });
        }

        async switchMode(mode) {
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
                    if (input) input.focus();
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
                const response = await fetch(`/api/inventory/item/${barcode}`);
                const item = await response.json();
                
                if (item.error) throw new Error(item.error);
                
                this.scannedData.item = item;
                this.updateItemInfo(item);
                this.moveToStep(2);
            } catch (error) {
                this.showError('Item nicht gefunden');
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
            document.getElementById('confirmItemStatus').textContent = 
                `${item.type === 'tool' ? 'Werkzeug' : 'Verbrauchsmaterial'} - ${item.status || 'Verfügbar'}`;
        }

        confirmAction(action) {
            if (!this.scannedData.item) return;
            
            this.scannedData.action = action;
            this.moveToStep(3);
            
            // Enable worker scan input
            const workerInput = document.getElementById('workerScanInput');
            workerInput.disabled = false;
            workerInput.focus();
        }

        async handleWorkerScan(barcode) {
            try {
                const response = await fetch(`/api/workers/${barcode}`);
                const worker = await response.json();
                
                if (worker.error) throw new Error(worker.error);
                
                this.scannedData.worker = worker;
                this.updateWorkerInfo(worker);
                this.moveToStep(4);
                await this.generateFinalBarcode();
            } catch (error) {
                this.showError('Mitarbeiter nicht gefunden');
            }
        }

        updateWorkerInfo(worker) {
            document.getElementById('scannedWorkerInfo').classList.remove('hidden');
            document.getElementById('workerName').textContent = 
                `${worker.firstname} ${worker.lastname}`;
            document.getElementById('workerDepartment').textContent = 
                worker.department || 'Keine Abteilung';
        }

        async generateFinalBarcode() {
            const confirmCode = `CONFIRM-${Date.now()}`;
            const response = await fetch(`/api/barcode/${confirmCode}`);
            const data = await response.json();
            
            document.getElementById('finalConfirmation').innerHTML = `
                <img src="${data.barcode}" alt="Bestätigungs-Barcode">
            `;
            
            document.getElementById('finalSummary').textContent = `
                ${this.scannedData.item.name} wird ${this.scannedData.action === 'lend' ? 'ausgeliehen an' : 'genutzt von'}
                ${this.scannedData.worker.firstname} ${this.scannedData.worker.lastname}
            `;
        }

        moveToStep(step) {
            this.currentStep = step;
            
            // Update Progress Steps in der Leiste oben
            document.querySelectorAll('.steps-horizontal .step').forEach((el, index) => {
                el.classList.toggle('step-primary', index < step);
            });
            
            // Aktiven Step anzeigen, andere ausblenden
            ['step1', 'step2', 'step3', 'step4'].forEach((stepId, index) => {
                const stepElement = document.getElementById(stepId);
                if (stepElement) {
                    stepElement.classList.toggle('hidden', index + 1 !== step);
                    stepElement.style.opacity = index + 1 === step ? '1' : '0.5';
                }
            });
            
            // Fokus und Input-Status setzen
            if (step === 1) {
                const input = document.getElementById('itemScanInput');
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
            }
        }

        async finalizeScan() {
            if (!this.scannedData.item || !this.scannedData.worker) return;
            
            try {
                const response = await fetch('/api/lending/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        item_id: this.scannedData.item.id,
                        worker_id: this.scannedData.worker.id,
                        type: this.scannedData.item.type,
                        action: this.scannedData.action
                    })
                });
                
                const result = await response.json();
                if (result.error) throw new Error(result.error);
                
                this.showSuccess('Vorgang erfolgreich abgeschlossen');
                this.modal.close();
                
            } catch (error) {
                this.showError('Fehler beim Abschließen: ' + error.message);
            }
        }

        resetScan() {
            this.currentStep = 1;
            this.scannedData = { item: null, worker: null, action: null };
            this.moveToStep(1);
            
            // Reset all inputs and info displays
            ['itemScanInput', 'workerScanInput'].forEach(id => {
                const input = document.getElementById(id);
                if (input) {
                    input.value = '';
                    input.disabled = false;
                }
            });
            
            ['scannedItemInfo', 'scannedWorkerInfo'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.classList.add('hidden');
            });
        }

        showError(message) {
            window.toast.show(message, 'error');
        }

        showSuccess(message) {
            window.toast.show(message, 'success');
        }

        async processLending() {
            if (!this.scannedData.item || !this.scannedData.worker) {
                this.showError('Unvollständige Daten für Ausleihe');
                return;
            }
            
            try {
                const response = await fetch('/api/lending/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content
                    },
                    body: JSON.stringify({
                        item_id: this.scannedData.item.barcode,
                        worker_id: this.scannedData.worker.barcode,
                        type: this.scannedData.item.type,
                        action: this.scannedData.action
                    })
                });
                
                const result = await response.json();
                if (!response.ok) throw new Error(result.error || 'Fehler beim Verarbeiten');
                
                this.showSuccess('Vorgang erfolgreich abgeschlossen');
                this.modal.close();
                // Seite neu laden um Liste zu aktualisieren
                window.location.reload();
                
            } catch (error) {
                this.showError(`Fehler: ${error.message}`);
            }
        }
    }

    // Initialisierung
    document.addEventListener('DOMContentLoaded', () => {
        window.quickScan = new QuickScan();
    }); 
}

// Initialisierung
document.addEventListener('DOMContentLoaded', () => {
    window.quickScan = new QuickScan();
}); 