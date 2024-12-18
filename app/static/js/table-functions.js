document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('lendingsTable');
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');

    if (!table || !searchInput || !categoryFilter) return;

    let sortDirection = {};

    // Hilfsfunktion zum Ermitteln des Spaltenindex
    function getColumnIndex(column) {
        switch(column) {
            case 'item': return 0;    // Artikel
            case 'worker': return 2;  // Ausgeliehen/Ausgegeben an
            case 'date': return 4;    // Datum
            default: return 0;
        }
    }

    // Suchfunktion
    function filterTable() {
        const searchTerm = searchInput.value.toLowerCase();
        const category = categoryFilter.value;
        const rows = Array.from(table.querySelectorAll('tbody tr'));

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const categoryCell = row.querySelector('td:nth-child(6)');
            const rowCategory = categoryCell ? categoryCell.textContent.trim() : '';
            const matchesSearch = text.includes(searchTerm);
            const matchesCategory = !category || rowCategory === category;
            row.style.display = matchesSearch && matchesCategory ? '' : 'none';
        });
    }

    // Sortierfunktion
    function sortTable(column) {
        console.log('Sorting by:', column);  // Debug
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        const direction = sortDirection[column] = !sortDirection[column];

        // Sortier-Icons aktualisieren
        table.querySelectorAll('th[data-sort] i').forEach(icon => {
            icon.className = 'fas fa-sort ml-1';
        });
        const currentIcon = table.querySelector(`th[data-sort="${column}"] i`);
        if (currentIcon) {
            currentIcon.className = `fas fa-sort-${direction ? 'up' : 'down'} ml-1`;
        }

        rows.sort((a, b) => {
            const colIndex = getColumnIndex(column);
            console.log('Column index:', colIndex);  // Debug
            const aVal = a.children[colIndex].textContent.trim();
            const bVal = b.children[colIndex].textContent.trim();
            console.log('Comparing:', aVal, bVal);  // Debug

            // Spezielle Behandlung für Datumsspalte
            if (column === 'date') {
                const aDate = new Date(aVal.split('.').reverse().join('-'));
                const bDate = new Date(bVal.split('.').reverse().join('-'));
                return direction ? aDate - bDate : bDate - aDate;
            }

            return direction ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        });

        const tbody = table.querySelector('tbody');
        rows.forEach(row => tbody.appendChild(row));
    }

    // Event Listener
    searchInput.addEventListener('input', filterTable);
    categoryFilter.addEventListener('change', filterTable);

    table.querySelectorAll('th[data-sort]').forEach(th => {
        th.style.cursor = 'pointer';  // Visuelles Feedback
        th.addEventListener('click', () => {
            console.log('Clicked column:', th.dataset.sort);  // Debug
            sortTable(th.dataset.sort);
        });
    });

    // Initial sort by date
    sortTable('date');
}); 