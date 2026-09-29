"""Authenticate every predictor endpoint before importing the model application."""
import json
import secrets
import time
from datetime import timedelta
from threading import Lock
from flask import Flask, request, session, redirect, render_template_string, Response
from werkzeug.security import check_password_hash

LOGIN = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Predictor · Sign in</title><style>
body{font:17px system-ui;background:#f1f5fa;color:#14213d;margin:0;display:grid;min-height:100vh;place-items:center}
main{background:white;padding:36px;border-radius:18px;width:min(360px,80vw);box-shadow:0 10px 40px #14213d15}
h1{font-size:26px}input,button{box-sizing:border-box;width:100%;padding:13px;border-radius:8px;margin-top:12px;font:inherit}
input{border:1px solid #a9b7cc}button{border:0;background:#244ea1;color:white;cursor:pointer}.error{color:#9b2d2d}</style>
<main><h1>Disease predictors</h1><p>Enter your password to continue.</p>
{% if error %}<p class="error" role="alert">{{error}}</p>{% endif %}
<form method="post" action="{{ login_url }}"><input type="hidden" name="csrf" value="{{csrf}}">
<label for="password">Password</label><input id="password" type="password" name="password" required autocomplete="current-password" autofocus maxlength="256">
<button type="submit">Sign in</button></form></main></html>'''

def create_application(config_path, predictor_factory=None):
    config = json.loads(config_path.read_text())  # Missing config fails closed.
    if not config.get('password_hash') or len(config.get('secret_key', '')) < 32:
        raise RuntimeError('A password hash and strong session secret are required.')
    mount = config.get('mount_path', '').rstrip('/')
    gate = Flask('predictor_login')
    gate.config.update(SECRET_KEY=config['secret_key'], SESSION_COOKIE_NAME='predictor_session',
        SESSION_COOKIE_PATH=mount or '/', SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8), MAX_CONTENT_LENGTH=4096)
    state = {'app': None, 'attempts': []}
    model_lock, auth_lock = Lock(), Lock()

    @gate.after_request
    def secure_headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    @gate.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        status = 200
        if request.method == 'POST':
            token = session.get('csrf', '')
            if not token or not secrets.compare_digest(token, request.form.get('csrf', '')):
                error, status = 'Please reload and try again.', 400
            else:
                with auth_lock:
                    now = time.monotonic()
                    state['attempts'] = [t for t in state['attempts'] if t > now - 300]
                    blocked = len(state['attempts']) >= 10
                    if not blocked:
                        state['attempts'].append(now)
                if blocked:
                    error, status = 'Too many attempts. Try again in five minutes.', 429
                elif check_password_hash(config['password_hash'], request.form.get('password', '')):
                    session.clear()
                    session['authenticated'] = True
                    session.permanent = True
                    return redirect(mount + '/')
                else:
                    error, status = 'Incorrect password.', 401
        session.setdefault('csrf', secrets.token_urlsafe(32))
        return render_template_string(LOGIN, csrf=session['csrf'], error=error, login_url=mount + '/login'), status

    @gate.post('/logout')
    def logout():
        session.clear()
        return redirect(mount + '/login')

    def application(environ, start_response):
        if environ.get('wsgi.url_scheme') != 'https':
            return redirect(config['public_origin'].rstrip('/') + mount + '/login', code=303)(environ, start_response)
        with gate.request_context(environ):
            if request.path in ('/login', '/logout'):
                return gate.wsgi_app(environ, start_response)
            if not session.get('authenticated'):
                return redirect(mount + '/login', code=303)(environ, start_response)
        with model_lock:
            if state['app'] is None:
                if predictor_factory is None:
                    from app import app
                    state['app'] = app
                else:
                    state['app'] = predictor_factory()
        return state['app'](environ, start_response)
    return application
