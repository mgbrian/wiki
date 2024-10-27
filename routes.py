import asyncio
from functools import wraps
import json
import os

import aiofiles
from asgiref.sync import sync_to_async
import magic
from pgvector.django import L2Distance, CosineDistance
from quart import (Quart, render_template, redirect, request, jsonify, session,
    url_for, send_from_directory, send_file, websocket, abort)

from db.models import Document, Page, User, calculate_embeddings
import env
import utils


app = Quart(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'media/'
)

# To keep track of socket connections.
connected_clients = {}

# To keep track of async tasks running in the bg
# See note below on keeping a reference to tasks:
# https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task
background_tasks = set()


def login_required(f):
    """View decorator to confirm login. Redirects to login page on failure."""
    @wraps(f)
    async def decorated_view(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))

        return await f(*args, **kwargs)

    return decorated_view


def admin_required(f):
    """View decorator to confirm admin status. Redirects home on failure."""
    @wraps(f)
    async def decorated_view(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))

        user = await User.objects.aget(username=session["username"])

        if not user or not user.is_admin:
            return redirect(url_for("index"))

        return await f(*args, **kwargs)

    return decorated_view


@app.route("/login", methods=["GET", "POST"])
async def login():
    if "username" in session:
        return redirect(url_for("index"))

    error_message = ""
    if request.method == "POST":
        form_data = await request.form
        username = form_data.get("username")
        password = form_data.get("password")

        try:
            user = await User.objects.aget(username=username, password=password)
            session["username"] = user.username
            if user.is_admin:
                # This won't be set for non-admins. The standard is_admin check
                # in the templates is just "admin" in session. It is removed on
                # logout.
                session["admin"] = True
            return redirect(url_for("index"))

        except User.DoesNotExist:
            error_message = "Invalid credentials, please try again."

    return await render_template("login.html", error_message=error_message)


@app.route("/logout")
async def logout():
    session.pop("username", None)
    session.pop("admin", None)
    return redirect(url_for("login"))


@app.route('/', methods=['GET'])
@login_required
async def index():
    return await render_template('index.html')


@app.route('/admin', methods=['GET'])
@admin_required
async def admin():
    return await render_template('admin.html')


@app.route('/search', methods=['POST'])
@login_required
async def search():
    search_type = 'keyword'  # or 'semantic'
    results = []
    search_payload = await request.json

    try:
        search_term = search_payload.get('text')
        search_mode = search_payload.get('mode', 'keyword')
        if search_mode not in {'keyword', 'semantic'}: search_mode = 'keyword'

        if search_term:
            # 1. Simple search:
            if search_mode == 'keyword':
                queryset = Page.objects.filter(text__icontains=search_term).select_related('document')

            # 2. Semantic Search
            else:
                threshold = search_payload.get('threshold')
                if (type(threshold) != float and type(threshold) != int) or threshold <= 0 or threshold >= 1:
                    # TODO: Parametrize this here and in JS!
                    threshold = 0.5

                print(threshold)
                search_term_embedding = await asyncio.to_thread(calculate_embeddings, search_term)
                queryset = Page.objects.alias(
                    distance=CosineDistance('text_embeddings', search_term_embedding)
                ).filter(distance__lt=(1.0 - threshold)
                ).order_by('distance'
                ).select_related('document')

            async for page in queryset:
                results.append(
                    {
                        'document': {
                            'id': page.document.id,
                            'name': page.document.name,
                        },
                        'number': page.number,
                        'id': page.number,
                        'number': page.number,
                        'text': page.text,
                        'summary': page.summary,
                    }
                )

    except (json.JSONDecodeError, KeyError) as e:
        print(e)
        return jsonify({'error': 'Malformed search payload.'}), 400

    return jsonify(results)


async def broadcast_document_update(document):
    """Update all clients of a document status change."""
    for client in connected_clients.values():
        await client.send_json(
            {
              'action': 'file-status-update',
              'payload': {
                  'filename': document.name,
                  'id': document.id,
                'status': document.get_status_display()
              }
            }
        )


@app.route('/upload', methods=['POST'])
@admin_required
async def upload_file():
    form = await request.files
    file = form.get('file')

    if not file:
        return jsonify({"error": "No file provided."}), 400

    mime = magic.Magic(mime=True)
    # Read small chunk to detect mimetype
    file_type = mime.from_buffer(file.read(1024))
    file.seek(0)

    if file_type == 'application/pdf':
        split_document = True
        # TODO: Parametrize!
        document_type = 1

    elif file_type.startswith('image/'):
        # TODO: Perhaps standardize image params e.g. resolution, size limits, etc.
        # Do this for both PDF pages and standalone images.
        split_document = False
        document_type = 2

    else:
        return jsonify({"error": "File must be a pdf or image."}), 400

    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(file.read())

    file_metadata = {
        'filename': filename,
        'path': filepath
    }

    document = await Document.objects.acreate(
        name=filename,
        filepath=filepath,
        type=document_type
    )
    file_metadata['id'] = document.id

    # Split PDF into separate image files.
    if split_document:
        def document_splitter_task_callback(document_splitter_task):
            """Update document status after page splitting is done."""
            # TODO: Handle errors here and in running the task.
            background_tasks.discard(document_splitter_task)
            # TODO: Better way to do this!
            document.status = 1

            document_save_task = asyncio.create_task(document.asave())
            document_status_broadcast_task = asyncio.create_task(
                broadcast_document_update(document)
            )

            pages = document_splitter_task.result()

            for p in pages:
                page_creation_task = asyncio.create_task(
                    Page.objects.acreate(
                        document=document,
                        number=p['number'],
                        filepath=p['filepath']
                    )
                )

        document_pages_folder = os.path.join(os.path.dirname(filepath), str(document.id))
        document_splitter_task = asyncio.create_task(
            utils.save_pdf_as_images(filepath, document_pages_folder)
        )
        background_tasks.add(document_splitter_task)
        document_splitter_task.add_done_callback(document_splitter_task_callback)

    # If document is an image.
    else:
        document.status = 1
        await document.asave()
        document_status_broadcast_task = asyncio.create_task(
            broadcast_document_update(document)
        )
        await Page.objects.acreate(
            document=document,
            number=1,
            filepath=filepath
        )

    return jsonify({"message": "File uploaded successfully", 'metadata': file_metadata})


@app.route('/files', methods=['GET'])
@admin_required
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


@app.route('/document/<id>/download', methods=['GET'])
@login_required
async def serve_document(id):
    try:
        document = await Document.objects.aget(id=id)
        return await send_file(document.filepath)

    except Document.DoesNotExist:
        abort(404)


@app.route('/document/<id>', methods=['GET'])
@login_required
async def document_detail(id):
    try:
        document = await Document.objects.aget(id=id)
        return await render_template('document-detail.html', document=document)

    except Document.DoesNotExist:
        abort(404)


@app.route('/page/<document_id>/<number>', methods=['GET'])
@login_required
async def serve_page_image(document_id, number):
    try:
        page = await Page.objects.aget(document=document_id, number=number)
        return await send_file(page.filepath)

    except Page.DoesNotExist:
        abort(404)


@app.route('/page/<document_id>/<number>/info', methods=['GET'])
@login_required
async def get_page_metadata(document_id, number):

    try:
        page = await Page.objects.aget(document=document_id, number=number)

        page_info = {
            "id": page.id,
            "text": page.text,
            "summary": page.summary,
        }

        if "admin" in session:
            page_info['status'] = page.get_status_display()
            page_info['description'] = page.description

        return jsonify(page_info), 200

    except Page.DoesNotExist:
        return jsonify({'error': 'Page not found.'}), 404


@app.route('/document/<id>/delete', methods=['GET'])
@admin_required
async def delete_document(id):
    try:
        document = await Document.objects.aget(id=id)
        await document.adelete()

        # TODO: Delete files -- add this as a pre/post_delete signal.

    except Document.DoesNotExist:
        pass

    # any other errors
    except Exception:
        return jsonify({'error': f'Document {id} deleted.'}), 500

    return jsonify({'message': f'Document {id} deleted.'})


@app.websocket('/ws/status/')
async def status_socket():
    # Connect new client.
    client_id = await websocket.receive()
    connected_clients[client_id] = websocket._get_current_object()

    # Acknowldege connection.
    await websocket.send_json({'action': 'connection-ack'})

    # Ongoing while loop to keep the WebSocket connection open.
    try:
        while True:
            await websocket.receive()
    except Exception:
        # Handle client disconnects/errors.
        if client_id in connected_clients:
            del connected_clients[client_id]


@app.errorhandler(404)
async def handler_404(error):
    return await render_template("error.html", status_code=404, error_message="Page Not Found"), 404


@app.errorhandler(500)
async def handler_500(error):
    return await render_template("error.html", status_code=500, error_message="Server Error"), 500


@app.errorhandler(403)
async def handler_403(error):
    return await render_template("error.html", status_code=403, error_message="Forbidden"), 403


@app.errorhandler(405)
async def handler_405(error):
    return await render_template("error.html", status_code=405, error_message="Method Not Allowed"), 405


@app.errorhandler(Exception)
async def generic_error_handler(error):
    """"Handler for any other HTTP errors not covered."""
    status_code = getattr(error, 'code', 500)
    error_message = error.name if hasattr(error, 'name') else "An unexpected error occurred"

    return await render_template("error.html", status_code=status_code, error_message=error_message), status_code
