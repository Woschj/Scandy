document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('manual-lending-form');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                worker_barcode: document.getElementById('worker_barcode').value,
                item_type: document.getElementById('item_type').value,
                item_barcode: document.getElementById('item_barcode').value,
                amount: document.getElementById('amount').value
            };

            fetch('/admin/process_lending', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Ausleihe erfolgreich verarbeitet!');
                    form.reset();
                } else {
                    alert('Fehler: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ein Fehler ist aufgetreten: ' + error);
            });
        });
    }
}); 