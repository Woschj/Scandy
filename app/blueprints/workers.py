@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'GET':
        # Lade alle aktiven Abteilungen für das Dropdown
        departments = Database.query('''
            SELECT name 
            FROM departments 
            WHERE deleted = 0 
            ORDER BY name
        ''')
        return render_template('workers/add.html', departments=departments)

    if request.method == 'POST':
        # Bestehende POST-Logik... 