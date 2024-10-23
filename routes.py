import os

from quart import Quart, render_template, jsonify

import env


app = Quart(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')


@app.route('/', methods=['GET'])
async def index():
    return await render_template('index.html')


@app.route('/admin', methods=['GET'])
async def admin():
    return await render_template('admin.html')


@app.route('/search', methods=['POST'])
async def search():
    dummy_data = [
        {'text': 'cat'},
        {'text': 'dog'},
        {'text': 'monkey'}
    ]
    return jsonify(dummy_data)
