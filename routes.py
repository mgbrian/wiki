import asyncio
import os

import aiofiles
from asgiref.sync import sync_to_async
from quart import Quart, render_template, request, jsonify, send_from_directory

from db.models import Document
import env


app = Quart(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'media/'
)

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


@app.route('/upload', methods=['POST'])
async def upload_file():
    form = await request.files
    file = form.get('file')

    if not file:
        return jsonify({"error": "No file provided."}), 400

    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Save the file to the uploads directory
    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(file.read())

    file_metadata = {
        'filename': filename,
        'path': filepath
    }

    _ = await Document.objects.acreate(name=filename, filepath=filepath)

    return jsonify({"message": "File uploaded successfully", 'metadata': file_metadata})


@app.route('/files', methods=['GET'])
async def list_files():

    documents = await sync_to_async(list)(Document.objects.all())

    files_list = [
        {
            "filename": document.name,
            "filepath": document.filepath,
            "id": document.id,
            "status": document.get_status_display()
        }
        for document in documents
    ]

    return jsonify(files_list), 200


@app.route('/files/<filename>', methods=['GET'])
async def serve_file(filename):
    # TODO: Use a better identifier than filename.
    return await send_from_directory(UPLOAD_FOLDER, filename)
