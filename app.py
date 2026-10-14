"""
Flask Application Entrypoint
============================
Provides direct access to the Flask app instance for WSGI servers or `flask run`.

Usage:
    python3 app.py
    # or
    flask run
"""

from web_dashboard import app, start_server

if __name__ == "__main__":
    start_server()
