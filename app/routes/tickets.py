from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app.models.database import Database
from app.utils.decorators import login_required, admin_required
import logging
from datetime import datetime

bp = Blueprint('tickets', __name__, url_prefix='/tickets')
db = Database()

@bp.route('/')
@admin_required
def index():
    """Zeigt die Übersicht aller Tickets."""
    # Filter aus Query-Parametern
    status = request.args.get('status')
    priority = request.args.get('priority')
    assigned_to = request.args.get('assigned_to')
    created_by = request.args.get('created_by')
    
    # Basis-Query
    query = """
        SELECT 
            t.*,
            creator.username as creator_name,
            assignee.username as assignee_name
        FROM tickets t
        LEFT JOIN users creator ON t.created_by = creator.username
        LEFT JOIN users assignee ON t.assigned_to = assignee.username
        WHERE 1=1
    """
    params = []
    
    # Filter anwenden
    if status and status != 'alle':
        query += " AND t.status = ?"
        params.append(status)
    if priority and priority != 'alle':
        query += " AND t.priority = ?"
        params.append(priority)
    if assigned_to:
        query += " AND t.assigned_to = ?"
        params.append(assigned_to)
    if created_by:
        query += " AND t.created_by = ?"
        params.append(created_by)
    
    query += " ORDER BY t.created_at DESC"
    
    tickets = db.query(query, params)
    return render_template('tickets/index.html', tickets=tickets)

@bp.route('/create', methods=['GET', 'POST'])
def create():
    """Erstellt ein neues Ticket."""
    if request.method == 'POST':
        try:
            data = request.get_json()
            title = data.get('title')
            description = data.get('description')
            priority = data.get('priority', 'normal')
            assigned_to = data.get('assigned_to')
            
            if not title or not description:
                return jsonify({
                    'success': False,
                    'message': 'Titel und Beschreibung sind erforderlich'
                }), 400
            
            # Benutzer aus Session oder 'Anonym'
            created_by = session.get('username', 'Anonym')
            
            db.query(
                """
                INSERT INTO tickets (title, description, priority, created_by, assigned_to)
                VALUES (?, ?, ?, ?, ?)
                """,
                [title, description, priority, created_by, assigned_to]
            )
            
            return jsonify({
                'success': True,
                'message': 'Ticket wurde erstellt'
            })
            
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Tickets: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Fehler beim Erstellen des Tickets'
            }), 500
            
    return render_template('tickets/create.html')

@bp.route('/<int:id>')
@admin_required
def detail(id):
    """Zeigt die Details eines Tickets."""
    ticket = db.query(
        """
        SELECT t.*,
               creator.username as creator_name
        FROM tickets t
        LEFT JOIN users creator ON t.created_by = creator.username
        WHERE t.id = ?
        """,
        [id],
        one=True
    )
    
    if not ticket:
        return render_template('404.html'), 404
        
    # Hole die Notizen für das Ticket
    notes = db.query(
        """
        SELECT *
        FROM ticket_notes
        WHERE ticket_id = ?
        ORDER BY created_at DESC
        """,
        [id]
    )
    
    return render_template('tickets/detail.html', ticket=ticket, notes=notes)

@bp.route('/<int:id>/update', methods=['POST'])
@login_required
def update(id):
    """Aktualisiert ein Ticket"""
    try:
        logging.info(f"Update-Anfrage für Ticket #{id} empfangen")
        logging.info(f"Content-Type: {request.content_type}")
        logging.info(f"Request Data: {request.get_data()}")
        
        # Hole die Daten entweder aus JSON oder Form-Daten
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        logging.info(f"Verarbeitete Daten: {data}")
        
        # Hole das aktuelle Ticket
        with Database.get_db() as db:
            ticket = db.execute(
                'SELECT * FROM tickets WHERE id = ?',
                [id]
            ).fetchone()
            
            if not ticket:
                flash('Ticket nicht gefunden', 'error')
                return redirect(url_for('tickets.index'))
            
            # Aktualisiere die Ticket-Daten
            db.execute('''
                UPDATE tickets 
                SET status = ?,
                    assigned_to = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', [
                data.get('status', ticket['status']),
                data.get('assigned_to', ticket['assigned_to']),
                id
            ])
            
            # Füge eine Notiz hinzu, wenn vorhanden
            resolution_notes = data.get('resolution_notes')
            if resolution_notes:
                db.execute('''
                    INSERT INTO ticket_notes 
                    (ticket_id, note, created_by)
                    VALUES (?, ?, ?)
                ''', [
                    id,
                    resolution_notes,
                    session.get('username', 'System')
                ])
            
            db.commit()
            
            flash('Ticket erfolgreich aktualisiert', 'success')
            return redirect(url_for('tickets.detail', id=id))

    except Exception as e:
        logging.error(f"Fehler beim Aktualisieren des Tickets #{id}: {str(e)}")
        flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
        return redirect(url_for('tickets.detail', id=id)) 