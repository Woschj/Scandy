from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.models.database import Database
from app.utils.decorators import admin_required

# Blueprint mit korrektem Namen definieren
bp = Blueprint('consumables', __name__, url_prefix='/consumables')

@bp.route('/')
def index():
    """Verbrauchsmaterialien-Übersicht"""
    try:
        print("\n=== CONSUMABLES INDEX ===")
        
        # Hole alle Datensätze
        consumables = Database.query('''
            SELECT c.*,
                   ROUND(CAST(c.quantity AS FLOAT) / NULLIF(c.min_quantity, 0) * 100) as stock_percentage,
                   CASE
                       WHEN c.quantity >= c.min_quantity THEN 'sufficient'
                       WHEN c.quantity >= c.min_quantity * 0.5 THEN 'warning'
                       ELSE 'critical'
                   END as stock_status
            FROM consumables c
            WHERE c.deleted = 0
            ORDER BY c.name
        ''')
        
        print(f"\nGefundene Datensätze: {len(consumables)}")
        if consumables:
            print("Beispiel-Verbrauchsmaterial:", dict(consumables[0]))
        
        # Kategorien und Standorte
        categories = Database.query('''
            SELECT DISTINCT category FROM consumables 
            WHERE deleted = 0 AND category IS NOT NULL
            ORDER BY category
        ''')
        
        locations = Database.query('''
            SELECT DISTINCT location FROM consumables 
            WHERE deleted = 0 AND location IS NOT NULL
            ORDER BY location
        ''')
        
        return render_template('consumables/index.html',
                             consumables=consumables,
                             categories=[c['category'] for c in categories],
                             locations=[l['location'] for l in locations])
        
    except Exception as e:
        print(f"\nFehler beim Laden der Verbrauchsmaterialien:")
        print(f"Typ: {type(e)}")
        print(f"Message: {str(e)}")
        import traceback
        print("Traceback:")
        print(traceback.format_exc())
        
        flash(f'Fehler beim Laden der Verbrauchsmaterialien: {str(e)}', 'error')
        return redirect(url_for('error.show_error', 
                              message="Fehler beim Laden der Verbrauchsmaterialien",
                              details=str(e)))

@bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    """Neues Verbrauchsmaterial hinzufügen"""
    if request.method == 'POST':
        try:
            print("\n=== VERBRAUCHSMATERIAL HINZUFÜGEN ===")
            print("Form data:", dict(request.form))
            
            name = request.form.get('name')
            barcode = request.form.get('barcode')
            description = request.form.get('description')
            category = request.form.get('category')
            location = request.form.get('location')
            quantity = request.form.get('quantity', type=int)
            min_quantity = request.form.get('min_quantity', type=int)
            
            print("\nValidierte Daten:")
            print(f"Name: {name}")
            print(f"Barcode: {barcode}")
            print(f"Description: {description}")
            print(f"Category: {category}")
            print(f"Location: {location}")
            print(f"Quantity: {quantity}")
            print(f"Min Quantity: {min_quantity}")
            
            if not all([name, barcode, quantity is not None, min_quantity is not None]):
                missing = []
                if not name: missing.append('Name')
                if not barcode: missing.append('Barcode')
                if quantity is None: missing.append('Menge')
                if min_quantity is None: missing.append('Mindestmenge')
                
                error_msg = f'Fehlende Pflichtfelder: {", ".join(missing)}'
                print(f"\nValidierungsfehler: {error_msg}")
                flash(error_msg, 'error')
                return redirect(url_for('consumables.add'))
            
            print("\nFüge in Datenbank ein...")
            Database.query('''
                INSERT INTO consumables 
                (name, barcode, description, category, location, quantity, min_quantity, 
                 created_at, modified_at, deleted, sync_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 'pending')
            ''', [name, barcode, description, category, location, quantity, min_quantity])
            
            print("Erfolgreich eingefügt!")
            flash('Verbrauchsmaterial erfolgreich hinzugefügt', 'success')
            return redirect(url_for('consumables.index'))
            
        except Exception as e:
            print(f"\nFehler beim Hinzufügen:")
            print(f"Typ: {type(e)}")
            print(f"Message: {str(e)}")
            import traceback
            print("Traceback:")
            print(traceback.format_exc())
            
            flash(f'Fehler beim Hinzufügen: {str(e)}', 'error')
            return redirect(url_for('consumables.add'))
    
    # GET-Request
    categories = Database.query('''
        SELECT DISTINCT category FROM consumables 
        WHERE deleted = 0 AND category IS NOT NULL
        ORDER BY category
    ''')
    
    locations = Database.query('''
        SELECT DISTINCT location FROM consumables
        WHERE deleted = 0 AND location IS NOT NULL
        ORDER BY location
    ''')
    
    return render_template('admin/add_consumable.html',
                         categories=[c['category'] for c in categories],
                         locations=[l['location'] for l in locations])

@bp.route('/<barcode>')
def details(barcode):
    """Zeigt Details eines Verbrauchsmaterials"""
    consumable = Database.query('''
        SELECT * FROM consumables 
        WHERE barcode = ? AND deleted = 0
    ''', [barcode], one=True)
    
    if not consumable:
        flash('Verbrauchsmaterial nicht gefunden', 'error')
        return redirect(url_for('consumables.index'))
        
    return render_template('consumables/details.html', consumable=consumable)

@bp.route('/<barcode>/edit', methods=['GET', 'POST'])
@admin_required
def edit(barcode):
    consumable = Consumable.get_by_barcode(barcode)
    if not consumable:
        flash('Verbrauchsmaterial nicht gefunden', 'error')
        return redirect(url_for('consumables.index'))
    
    if request.method == 'POST':
        try:
            Database.query('''
                UPDATE consumables 
                SET name = ?,
                    description = ?,
                    quantity = ?,
                    min_quantity = ?,
                    location = ?,
                    category = ?
                WHERE barcode = ?
            ''', [
                request.form['name'],
                request.form.get('description', ''),
                int(request.form.get('quantity', 0)),
                int(request.form.get('min_quantity', 0)),
                request.form.get('location', ''),
                request.form.get('category', ''),
                barcode
            ])
            
            flash('Verbrauchsmaterial erfolgreich aktualisiert', 'success')
            return redirect(url_for('consumables.details', barcode=barcode))
        except Exception as e:
            flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    
    return render_template('consumable_details.html', consumable=consumable)

@bp.route('/<barcode>/delete', methods=['POST', 'DELETE'])
@admin_required
def delete(barcode):
    try:
        print(f"Lösche Verbrauchsmaterial: {barcode}")
        result = Database.soft_delete('consumables', barcode)
        print(f"Lösch-Ergebnis: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Fehler beim Löschen: {e}")
        return jsonify({
            'success': False, 
            'message': str(e)
        })