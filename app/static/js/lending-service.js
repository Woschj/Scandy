// Sofort ausgeführte Funktion mit Debug-Logging
(function() {
    console.log('=== LENDING SERVICE INITIALIZATION START ===');
    console.log('Script location:', document.currentScript?.src || 'Unknown location');
    
    // Hilfsfunktion für formatierte Debug-Ausgaben
    function debug(area, message, data = null) {
        const timestamp = new Date().toISOString().split('T')[1];  // Nur die Uhrzeit
        const baseMsg = `[${timestamp}] [${area}] ${message}`;
        if (data) {
            console.log(baseMsg, data);
        } else {
            console.log(baseMsg);
        }
    }

    debug('INIT', 'Starting LendingService initialization');

    // Debug-Namespace
    window.ScanDebug = {
        async testLending() {
            debug('TEST', 'Starting lending test');
            try {
                const testData = {
                    itemData: {
                        type: 'tool',
                        barcode: '12345',
                        amount: 1
                    },
                    workerData: {
                        barcode: '67890'
                    }
                };
                debug('TEST', 'Using test data:', testData);
                
                debug('TEST', 'Calling processLending...');
                const result = await window.LendingService.processLending(
                    testData.itemData, 
                    testData.workerData
                );
                debug('TEST', 'Lending test completed successfully:', result);
                return result;
            } catch (error) {
                debug('TEST', 'Test failed with error:', {
                    name: error.name,
                    message: error.message,
                    stack: error.stack
                });
                throw error;
            }
        },

        // Debug-Hilfsfunktionen
        checkEnvironment() {
            debug('ENV', 'Checking environment...');
            const checks = {
                fetch: typeof fetch !== 'undefined',
                json: typeof JSON !== 'undefined',
                lendingService: typeof window.LendingService !== 'undefined',
                scanDebug: typeof window.ScanDebug !== 'undefined'
            };
            debug('ENV', 'Environment check results:', checks);
            return checks;
        }
    };

    // LendingService Definition
    window.LendingService = {
        async processLending(itemData, workerData) {
            debug('LENDING', 'ProcessLending called with:', { itemData, workerData });
            
            try {
                // Eingabevalidierung
                if (!itemData) {
                    debug('LENDING', 'Error: No item data provided');
                    throw new Error('Keine Artikeldaten vorhanden');
                }
                if (!workerData) {
                    debug('LENDING', 'Error: No worker data provided');
                    throw new Error('Keine Mitarbeiterdaten vorhanden');
                }

                const requestData = {
                    item_type: itemData.type || '',
                    item_barcode: itemData.barcode || '',
                    worker_barcode: workerData.barcode || '',
                    amount: itemData.amount || 1
                };
                
                debug('LENDING', 'Prepared request data:', requestData);
                debug('LENDING', 'Sending request to /admin/process_lending...');

                const response = await fetch('/admin/process_lending', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify(requestData)
                });

                debug('LENDING', 'Response received:', {
                    status: response.status,
                    statusText: response.statusText,
                    headers: Object.fromEntries(response.headers.entries())
                });

                const textResponse = await response.text();
                debug('LENDING', 'Raw response text:', textResponse);

                let result;
                try {
                    result = JSON.parse(textResponse);
                    debug('LENDING', 'Parsed JSON response:', result);
                } catch (parseError) {
                    debug('LENDING', 'JSON Parse Error:', parseError);
                    throw new Error(`Ungültiges Antwortformat: ${textResponse}`);
                }
                
                if (!response.ok) {
                    debug('LENDING', 'Request failed:', result);
                    throw new Error(result.message || 'Fehler bei der Ausleihe');
                }

                debug('LENDING', 'Request completed successfully');
                return result;

            } catch (error) {
                debug('LENDING', 'Error in processLending:', {
                    name: error.name,
                    message: error.message,
                    stack: error.stack
                });
                throw error;
            }
        },

        async returnItem(itemBarcode) {
            debug('RETURN', 'ReturnItem called with barcode:', itemBarcode);
            
            try {
                debug('RETURN', 'Sending return request...');
                const response = await fetch('/admin/process_return', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        item_barcode: itemBarcode
                    })
                });

                debug('RETURN', 'Return response received:', {
                    status: response.status,
                    statusText: response.statusText
                });

                const textResponse = await response.text();
                debug('RETURN', 'Raw return response:', textResponse);

                let result;
                try {
                    result = JSON.parse(textResponse);
                    debug('RETURN', 'Parsed return response:', result);
                } catch (parseError) {
                    debug('RETURN', 'Return JSON Parse Error:', parseError);
                    throw new Error(`Ungültiges Rückgabe-Format: ${textResponse}`);
                }

                if (!response.ok) {
                    debug('RETURN', 'Return request failed:', result);
                    throw new Error(result.message || 'Fehler bei der Rückgabe');
                }

                debug('RETURN', 'Return completed successfully');
                return result;

            } catch (error) {
                debug('RETURN', 'Error in returnItem:', {
                    name: error.name,
                    message: error.message,
                    stack: error.stack
                });
                throw error;
            }
        },

        async returnTool(toolBarcode) {
            debug('RETURN', 'ReturnTool called with barcode:', toolBarcode);
            
            try {
                const response = await fetch('/admin/process_return', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        item_barcode: toolBarcode
                    })
                });

                debug('RETURN', 'Response received:', {
                    status: response.status,
                    statusText: response.statusText
                });

                const result = await response.json();
                debug('RETURN', 'Return result:', result);
                
                if (!response.ok) {
                    throw new Error(result.message || 'Fehler bei der Rückgabe');
                }

                // Seite neu laden nach erfolgreicher Rückgabe
                location.reload();
                return result;

            } catch (error) {
                debug('RETURN', 'Error in returnTool:', error);
                throw error;
            }
        }
    };

    // Initialisierung abschließen
    debug('INIT', 'LendingService initialization completed');
    debug('INIT', 'Available endpoints:', {
        processLending: '/admin/process_lending',
        processReturn: '/admin/process_return'
    });

    // Umgebung überprüfen
    window.ScanDebug.checkEnvironment();

    console.log('=== LENDING SERVICE INITIALIZATION COMPLETE ===');
})(); 

function switchType(type) {
    // Toggle active state of buttons
    document.querySelectorAll('[data-tab]').forEach(btn => {
        btn.classList.toggle('btn-active', btn.dataset.tab === type);
    });
    
    // Show/hide corresponding lists
    document.getElementById('toolsList').classList.toggle('hidden', type !== 'tools');
    document.getElementById('consumablesList').classList.toggle('hidden', type !== 'consumables');
    
    // Reset search and selection
    document.getElementById('itemSearch').value = '';
    document.getElementById('itemDetails').classList.add('hidden');
} 