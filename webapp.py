from flask import Flask, render_template, request, jsonify, session
import base64
import io
from pathlib import Path

import criar_geodb as geodb
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

# secret key for session (insecure default, override with env var)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/save', methods=['POST'])
def save():
    data = request.get_json() or {}
    expr = data.get('expr')
    image_data = data.get('image')  # data:image/png;base64,....
    if not expr:
        return jsonify({'ok': False, 'error': 'expr required'}), 400

    img_bytes = None
    if image_data and image_data.startswith('data:image'):
        try:
            header, b64 = image_data.split(',', 1)
            img_bytes = base64.b64decode(b64)
        except Exception as e:
            return jsonify({'ok': False, 'error': 'invalid image data', 'detail': str(e)}), 400

    user_id = session.get('user_id')
    ok = geodb.save_calculation(expr, None, img_bytes, user_id=user_id)
    if ok:
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'db save failed'}), 500


@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'ok': False, 'error': 'username and password required'}), 400
    ph = generate_password_hash(password)
    ok = geodb.create_user(username, ph)
    if ok:
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'create failed'}), 500


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'ok': False, 'error': 'username and password required'}), 400
    row = geodb.get_user_by_username(username)
    if not row:
        return jsonify({'ok': False, 'error': 'invalid'}), 401
    user_id, usern, password_hash, created_at = row
    if not check_password_hash(password_hash, password):
        return jsonify({'ok': False, 'error': 'invalid'}), 401
    session['user_id'] = user_id
    session['username'] = usern
    return jsonify({'ok': True, 'username': usern})


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({'ok': True})


@app.route('/api/current_user')
def api_current_user():
    return jsonify({'user_id': session.get('user_id'), 'username': session.get('username')})


@app.route('/api/list')
def api_list():
    # list only current user's calculations
    user_id = session.get('user_id')
    if user_id is None:
        return jsonify([])
    rows = geodb.list_calculations(limit=200)
    # filter by user_id
    out = []
    for r in rows:
        # r: id, expr, result, created_at, octet_length, user_id
        if len(r) >= 6 and r[5] == user_id:
            out.append({'id': r[0], 'expr': r[1], 'result': r[2], 'created_at': str(r[3])})
    return jsonify(out)


def start():
    # try create table
    geodb.init_db()
    app.run(debug=True)


if __name__ == '__main__':
    start()
