from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.database import Database
from app.models.tool import Tool
from app.utils.decorators import admin_required
import json

bp = Blueprint('tools', __name__)

@bp.route('/tools')
def index():
    tools = Tool.get_all_with_status()
    return render_template('tools.html', tools=tools)

@bp.route('/tools/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        barcode = request.form['barcode']
        name = request.form['name']
        description = request.form.get('description', '')
        
        try:
            Database.query(
                'INSERT INTO tools (barcode, name, description) VALUES (?, ?, ?)',
                [barcode, name, description]
            )
            flash('Werkzeug erfolgreich hinzugefügt', 'success')
            return redirect(url_for('tools.index'))
        except Exception as e:
            flash(f'Fehler beim Hinzufügen: {str(e)}', 'error')
            
    return render_template('admin/add_tool.html')

@bp.route('/tools/<barcode>')
def details(barcode):
    tool = Tool.get_by_barcode(barcode)
    if tool:
        lending_history = Tool.get_lending_history(barcode)
        return render_template('tool_details.html', tool=tool, history=lending_history)
    flash('Werkzeug nicht gefunden', 'error')
    return redirect(url_for('tools.index'))

@bp.route('/tools/<barcode>/edit', methods=['GET', 'POST'])
@admin_required
def edit(barcode):
    tool = Tool.get_by_barcode(barcode)
    if not tool:
        flash('Werkzeug nicht gefunden', 'error')
        return redirect(url_for('tools.index'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        
        try:
            Database.query(
                'UPDATE tools SET name = ?, description = ? WHERE barcode = ?',
                [name, description, barcode]
            )
            flash('Werkzeug erfolgreich aktualisiert', 'success')
            return redirect(url_for('tools.details', barcode=barcode))
        except Exception as e:
            flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    
    return render_template('admin/edit_tool.html', tool=tool)

@bp.route('/tools/<barcode>/delete', methods=['POST'])
@admin_required
def delete(barcode):
    try:
        Database.query(
            'UPDATE tools SET deleted = 1 WHERE barcode = ?',
            [barcode]
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/tools/search')
def search():
    query = request.args.get('q', '')
    try:
        tools = Database.query('''
            SELECT * FROM tools 
            WHERE (name LIKE ? OR barcode LIKE ?) 
            AND deleted = 0
        ''', [f'%{query}%', f'%{query}%'])
        return jsonify([dict(tool) for tool in tools])
    except Exception as e:
        return jsonify({'error': str(e)}), 500 