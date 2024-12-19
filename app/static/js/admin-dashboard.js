document.addEventListener('DOMContentLoaded', function() {
    const consumableTable = document.querySelector('#consumableUsageTable');
    if (!consumableTable) return;

    const headers = consumableTable.querySelectorAll('th');
    
    headers.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.dataset.column;
            let filterValue;
            
            // Verschiedene Filter-Typen je nach Spalte
            switch(column) {
                case 'consumable':
                case 'worker':
                    filterValue = prompt(`Nach ${this.textContent} filtern:`);
                    break;
                case 'amount':
                    filterValue = prompt('Nach Menge filtern (Zahl eingeben):', '1');
                    break;
                case 'date':
                    filterValue = prompt('Nach Datum filtern (YYYY-MM-DD):', new Date().toISOString().split('T')[0]);
                    break;
                default:
                    return;
            }
            
            if (filterValue === null || filterValue.trim() === '') return;

            // AJAX Request zum Server
            fetch('/admin/filter_consumable_usages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `filter_type=${column}&filter_value=${filterValue}`
            })
            .then(response => response.json())
            .then(data => {
                const tbody = consumableTable.querySelector('tbody');
                tbody.innerHTML = '';
                
                data.forEach(row => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${row.consumable_name}</td>
                        <td>${row.worker_name}</td>
                        <td>${row.quantity}</td>
                        <td>${new Date(row.timestamp).toLocaleString()}</td>
                    `;
                    tbody.appendChild(tr);
                });
            })
            .catch(error => console.error('Error:', error));
        });
    });
}); 