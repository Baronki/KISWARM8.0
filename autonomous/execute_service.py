#!/usr/bin/env python3
"""Execute Service - Port 5556"""
from flask import Flask, request, jsonify
from datetime import datetime
import subprocess

app = Flask(__name__)
AUTH_TOKEN = "ada6952188dce59c207b9a61183e8004"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'execute'})

@app.route('/execute', methods=['POST'])
def execute():
    token = request.headers.get('X-Auth-Token')
    if token != AUTH_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'error': 'Missing command'}), 400
    try:
        result = subprocess.run(data['command'], shell=True, capture_output=True, text=True, timeout=60, cwd='/opt/kiswarm7')
        return jsonify({'success': result.returncode == 0, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("[EXECUTE] Starting on port 5556")
    app.run(host='0.0.0.0', port=5556, debug=False)
