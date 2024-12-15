from flask import Blueprint, render_template
from app.utils.decorators import login_required

bp = Blueprint('quick_scan', __name__)

@bp.route('/quick_scan')
@login_required
def quick_scan():
    return render_template('quick_scan.html') 