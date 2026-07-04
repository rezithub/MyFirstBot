from flask import Flask
import threading
import os
import json
import sources.main as main

app = Flask(__name__)

@app.route('/')
def home():
    return "bot is running"

@app.route('/health')
def health():
    return "OK"

if __name__ == "__main__":
    threading.Thread(target=main.start_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)