from flask import Flask, request, jsonify, send_from_directory, session
from functools import wraps
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = 'rifc-secret-key-change-me-in-production'

ADMIN_USER = 'rifc.admin'
ADMIN_PASS = 'alimasi123'
MATCHES_FILE = 'matches.json'


def load_matches():
    if not os.path.exists(MATCHES_FILE):
        return []
    try:
        with open(MATCHES_FILE, 'r') as f:
            return json.load(f)
    except:
        return []


def save_matches(matches):
    with open(MATCHES_FILE, 'w') as f:
        json.dump(matches, f, indent=2)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


# ---------- Pages ----------
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/admin')
@app.route('/admin.html')
def admin():
    return send_from_directory('.', 'admin.html')


@app.route('/logo.png')
def logo():
    return send_from_directory('.', 'logo.png')


# ---------- Auth ----------
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if username == ADMIN_USER and password == ADMIN_PASS:
        session['logged_in'] = True
        return jsonify({'ok': True})
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({'ok': True})


@app.route('/api/check-auth')
def check_auth():
    return jsonify({'logged_in': bool(session.get('logged_in'))})


# ---------- Matches API ----------
@app.route('/api/matches')
def get_matches():
    matches = load_matches()
    matches.sort(key=lambda m: m.get('date', '') + m.get('time', ''))
    return jsonify(matches)


@app.route('/api/matches', methods=['POST'])
@login_required
def add_match():
    data = request.get_json() or {}
    required = ['date', 'time', 'location', 'opponent', 'side', 'status']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing {field}'}), 400

    if data['status'] == 'past':
        if data.get('scoreUs') is None or data.get('scoreThem') is None:
            return jsonify({'error': 'Scores required for past matches'}), 400

    matches = load_matches()
    match = {
        'id': str(int(datetime.now().timestamp() * 1000)),
        'date': data['date'],
        'time': data['time'],
        'location': data['location'],
        'opponent': data['opponent'],
        'side': data['side'],
        'status': data['status'],
        'scoreUs': data.get('scoreUs'),
        'scoreThem': data.get('scoreThem'),
        'logo': data.get('logo')
    }
    matches.append(match)
    matches.sort(key=lambda m: m.get('date', '') + m.get('time', ''))
    save_matches(matches)
    return jsonify(match), 201


@app.route('/api/matches/<match_id>', methods=['PUT'])
@login_required
def update_match(match_id):
    data = request.get_json() or {}
    matches = load_matches()
    for i, m in enumerate(matches):
        if m['id'] == match_id:
            matches[i].update({
                'date': data.get('date', m['date']),
                'time': data.get('time', m['time']),
                'location': data.get('location', m['location']),
                'opponent': data.get('opponent', m['opponent']),
                'side': data.get('side', m['side']),
                'status': data.get('status', m['status']),
                'scoreUs': data.get('scoreUs', m.get('scoreUs')),
                'scoreThem': data.get('scoreThem', m.get('scoreThem')),
                'logo': data.get('logo', m.get('logo'))
            })
            matches.sort(key=lambda x: x.get('date', '') + x.get('time', ''))
            save_matches(matches)
            return jsonify(matches[i])
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/matches/<match_id>', methods=['DELETE'])
@login_required
def delete_match(match_id):
    matches = load_matches()
    new_matches = [m for m in matches if m['id'] != match_id]
    if len(new_matches) == len(matches):
        return jsonify({'error': 'Not found'}), 404
    save_matches(new_matches)
    return jsonify({'ok': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
