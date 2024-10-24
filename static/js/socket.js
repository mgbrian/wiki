const socket = new WebSocket(`ws://${window.location.host}/ws/status/`);
const clientId = crypto.randomUUID(); // Identify ourselves to server.

socket.onopen = () => {
  socket.send(clientId);
};

socket.onmessage = handleServerMessage;

/* Handle a message from the server.

  A server message will look like:
    message : {
      'action': ... an indication of what message is about,
      'payload: {
        ... actual data being sent
      }
    }
  }
*/
function handleServerMessage(event) {
  const message = JSON.parse(event.data);
  console.log(event.data);

  if (message.action === "connection-ack") {
    console.log(`WebSocket connection established. Client id ${clientId}`);
  } else if (message.action === "file-status-update") {
    fileLiElement = document.querySelector(`#file-list [data-id="1"]`);
    fileLiElement.dataset.status = message.payload.status;
    fileLiElement.querySelector("file-status-indicator").textContent =
      message.payload.status;
  }
}

socket.onclose = () => {
  console.log("WebSocket connection closed");
};
