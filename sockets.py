from quart import websocket

from __main__ import app

# To keep track of socket connections.
connected_clients = {}


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
