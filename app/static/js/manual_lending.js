// Globale Variablen für die Auswahl
let selectedItem = null;
let selectedWorker = null;

// Tab-Funktionalität
function switchType(type) {
    console.log('Wechsle zu Typ:', type);
    
    // Tab-Buttons aktualisieren
    document.querySelectorAll('[data-tab]').forEach(button => {
        if (button.dataset.tab === type) {
            button.classList.add('btn-active');
        } else {
            button.classList.remove('btn-active');
        }
    });
    
    // Optionen in der Select-Liste ein-/ausblenden
    const itemSelect = document.getElementById('itemSelect');
    if (itemSelect) {
        Array.from(itemSelect.options).forEach(option => {
            const optionType = option.value.split(':')[0]; // 'tool' oder 'consumable'
            if (type === 'tools' && optionType === 'tool') {
                option.style.display = '';
            } else if (type === 'consumables' && optionType === 'consumable') {
                option.style.display = '';
            } else {
                option.style.display = 'none';
            }
        });
    }
    
    // Mengenanzeige ein-/ausblenden
    const amountContainer = document.getElementById('amountContainer');
    if (amountContainer) {
        if (type === 'consumables') {
            amountContainer.classList.remove('hidden');
        } else {
            amountContainer.classList.add('hidden');
        }
    }
    
    // Reset Auswahl
    selectedItem = null;
    updatePreview();
    
    // Details ausblenden
    document.getElementById('itemDetails').classList.add('hidden');
    
    // Select-Feld zurücksetzen
    if (itemSelect) {
        itemSelect.value = '';
    }
}

// Initialisierung
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initialisiere manuelle Ausleihe...');
    
    // Elemente abrufen
    const itemSelect = document.getElementById('itemSelect');
    const workerSelect = document.getElementById('workerSelect');
    const confirmButton = document.getElementById('confirmButton');
    
    // Event Listener für Auswahl
    if (itemSelect) {
        console.log('Item Select gefunden');
        itemSelect.addEventListener('change', function(e) {
            console.log('Item ausgewählt:', e.target.value);
            updateItemDetails(e.target.value);
        });
    } else {
        console.error('Item Select nicht gefunden!');
    }
    
    if (workerSelect) {
        console.log('Worker Select gefunden');
        workerSelect.addEventListener('change', function(e) {
            console.log('Worker ausgewählt:', e.target.value);
            updateWorkerDetails(e.target.value);
        });
    } else {
        console.error('Worker Select nicht gefunden!');
    }
    
    // Bestätigungs-Button Event
    if (confirmButton) {
        console.log('Confirm Button gefunden');
        confirmButton.addEventListener('click', async function(e) {
            e.preventDefault();
            console.log('Bestätigungs-Button geklickt');
            await processLending();
        });
    } else {
        console.error('Confirm Button nicht gefunden!');
    }
});

function updateItemDetails(itemValue) {
    console.log('Update Item Details:', itemValue);
    
    const itemDetails = document.getElementById('itemDetails');
    if (!itemValue) {
        itemDetails.classList.add('hidden');
        selectedItem = null;
        updatePreview();
        return;
    }

    const [type, id, barcode, name] = itemValue.split(':');
    selectedItem = { type, id, barcode, name };
    console.log('Ausgewähltes Item:', selectedItem);

    document.getElementById('itemDetailName').textContent = name;
    document.getElementById('itemDetailBarcode').textContent = barcode;
    
    itemDetails.classList.remove('hidden');
    updatePreview();
}

function updateWorkerDetails(workerValue) {
    console.log('Update Worker Details:', workerValue);
    
    const workerDetails = document.getElementById('workerDetails');
    if (!workerValue) {
        workerDetails.classList.add('hidden');
        selectedWorker = null;
        updatePreview();
        return;
    }

    const workerSelect = document.getElementById('workerSelect');
    selectedWorker = {
        barcode: workerValue,
        name: workerSelect.options[workerSelect.selectedIndex].text
    };
    console.log('Ausgewählter Worker:', selectedWorker);

    document.getElementById('workerDetailName').textContent = selectedWorker.name;
    document.getElementById('workerDetailBarcode').textContent = selectedWorker.barcode;
    
    workerDetails.classList.remove('hidden');
    updatePreview();
}

function updatePreview() {
    const previewItem = document.getElementById('previewItem');
    const previewWorker = document.getElementById('previewWorker');
    const confirmButton = document.getElementById('confirmButton');
    
    previewItem.textContent = selectedItem ? selectedItem.name : '-';
    previewWorker.textContent = selectedWorker ? selectedWorker.name : '-';
    
    confirmButton.disabled = !(selectedItem && selectedWorker);
}

async function processLending() {
    console.log('Starte Ausleihprozess...');
    console.log('Aktuelle Auswahl:', { selectedItem, selectedWorker });
    
    if (!selectedItem || !selectedWorker) {
        const missing = [];
        if (!selectedItem) missing.push('Werkzeug');
        if (!selectedWorker) missing.push('Mitarbeiter');
        showError(`Bitte wählen Sie ${missing.join(' und ')} aus`);
        return;
    }
    
    try {
        const response = await fetch('/api/lending/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tool_barcode: selectedItem.barcode,
                worker_barcode: selectedWorker.barcode
            })
        });
        
        const data = await response.json();
        console.log('API Antwort:', data);
        
        if (response.ok) {
            showSuccess('Ausleihe erfolgreich!');
            setTimeout(() => location.reload(), 2000);
        } else {
            throw new Error(data.error || 'Fehler bei der Ausleihe');
        }
    } catch (error) {
        console.error('Fehler bei der Ausleihe:', error);
        showError(error.message);
    }
}

function showError(message) {
    console.error('Fehler:', message);
    alert(message); // Temporär Alert statt UI-Element
}

function showSuccess(message) {
    console.log('Erfolg:', message);
    alert(message); // Temporär Alert statt UI-Element
} 