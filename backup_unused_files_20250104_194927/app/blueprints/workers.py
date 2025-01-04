@bp.route('/')
@login_required
def index():
    workers = Database.query('''
        SELECT * 
        FROM workers
        WHERE deleted = 0
        ORDER BY firstname, lastname
    ''')
    return render_template('workers/index.html', workers=workers) 