from flask import request, Blueprint

bp = Blueprint('routes', __name__)
@bp.route('/')
def index():
    return 'Backend is working'

@bp.route('/packet', methods=['POST'])
def packet():
    data = request.get_json()
    return 'JSON received'
