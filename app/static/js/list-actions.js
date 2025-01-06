function editTool(barcode) {
    window.location.href = `/tools/${barcode}/edit`;
}

function deleteTool(barcode) {
    if (confirm('Werkzeug wirklich löschen?')) {
        fetch(`/tools/${barcode}/delete`, {
            method: 'DELETE'
        }).then(response => response.json())
        .then(data => {
            if (data.success) {
                refreshList();
            } else {
                alert('Fehler beim Löschen: ' + data.message);
            }
        });
    }
}

function editConsumable(barcode) {
    window.location.href = `/consumables/${barcode}`;
}

function deleteConsumable(barcode) {
    if (confirm('Verbrauchsmaterial wirklich löschen?')) {
        fetch(`/consumables/${barcode}/delete`, {
            method: 'DELETE'
        }).then(response => response.json())
        .then(data => {
            if (data.success) {
                refreshList();
            } else {
                alert('Fehler beim Löschen: ' + data.message);
            }
        });
    }
}

function editWorker(barcode) {
    window.location.href = `/workers/${barcode}/edit`;
}

function deleteWorker(barcode) {
    if (confirm('Mitarbeiter wirklich löschen?')) {
        fetch(`/workers/${barcode}/delete`, {
            method: 'DELETE'
        }).then(response => response.json())
        .then(data => {
            if (data.success) {
                refreshList();
            } else {
                alert('Fehler beim Löschen: ' + data.message);
            }
        });
    }
}

// Funktion zum Neuladen der Übersichtsseite
function refreshList() {
    window.location.reload();
} 