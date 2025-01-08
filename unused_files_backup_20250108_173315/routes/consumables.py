from flask import Blueprint, jsonify, session
from database import get_db_connection
from config import DBConfig
import logging

consumables_bp = Blueprint('consumables', __name__)

@consumables_bp.route('/<barcode>/delete', methods=['DELETE'])
def delete_consumable(barcode):
    try:
        user = session.get('username', 'System')
        
        with get_db_connection(DBConfig.CONSUMABLES_DB) as conn:
            # Prüfe ob Verbrauchsmaterial existiert
            consumable = conn.execute(
                'SELECT * FROM consumables WHERE barcode = ?', 
                (barcode,)
            ).fetchone()
            
            if not consumable:
                return jsonify({'success': False, 'error': 'Verbrauchsmaterial nicht gefunden'})
            
            # Prüfe auf aktive Ausleihen
            conn.execute(f"ATTACH DATABASE '{DBConfig.LENDINGS_DB}' AS lendings_db")
            active_lendings = conn.execute('''
                SELECT COUNT(*) as count 
                FROM lendings_db.lendings 
                WHERE item_barcode = ? AND item_type = 'consumable' AND return_time IS NULL
            ''', (barcode,)).fetchone()['count']
            
            if active_lendings > 0:
                return jsonify({
                    'success': False, 
                    'error': 'Verbrauchsmaterial hat noch aktive Ausleihen'
                })
            
            # Verschiebe in deleted_consumables
            conn.execute('''
                INSERT INTO deleted_consumables 
                (barcode, bezeichnung, typ, ort, einheit, mindestbestand, aktueller_bestand, deleted_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (consumable['barcode'], consumable['bezeichnung'], consumable['typ'],
                 consumable['ort'], consumable['einheit'], consumable['mindestbestand'],
                 consumable['aktueller_bestand'], user))
            
            # Lösche Verbrauchsmaterial
            conn.execute('DELETE FROM consumables WHERE barcode = ?', (barcode,))
            conn.commit()
            
            return jsonify({'success': True})
            
    except Exception as e:
        logging.error(f"Fehler beim Löschen: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}) 