import os

import aiofiles
from quart import Quart, render_template, request, jsonify, send_from_directory

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

    # TODO: ** Save file metadata to DB here.**

    return jsonify({"message": "File uploaded successfully", 'metadata': file_metadata})


@app.route('/files', methods=['GET'])
async def list_files():
    # TODO: ** Get these from DB. **

    files_list = []

    # List *files* in the upload directory.
    for item in os.listdir(UPLOAD_FOLDER):
        full_path = os.path.join(UPLOAD_FOLDER, item)

        if os.path.isfile(full_path):
            files_list.append({
                'filename': item,
                'path': full_path
            })

    return jsonify(files_list), 200


@app.route('/files/<filename>', methods=['GET'])
async def serve_file(filename):
    # TODO: Use a better identifier than filename.
    return await send_from_directory(UPLOAD_FOLDER, filename)
