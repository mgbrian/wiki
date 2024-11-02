const PROTOCOL = window.location.protocol.includes("https") ? "wss" : "ws";
const SOCKET_ENDPOINT = `${PROTOCOL}://${window.location.host}/ws/status/`;
let socket;
const clientId = crypto.randomUUID(); // Identify ourselves to server.

const MAX_RECONNECT_ATTEMPTS = 5;
let reconnectAttempts = 0;

function connectSocket() {
  socket = new WebSocket(SOCKET_ENDPOINT);

  socket.onopen = () => {
    socket.send(clientId);
  };

  socket.onclose = (event) => {
    if (event.wasClean) {
      console.log("WebSocket connection closed cleanly.");
    } else {
      console.log("WebSocket connection closed abruptly");
      attemptReconnect();
    }
  };

  socket.onmessage = handleServerMessage;

  socket.onerror = (error) => {
    console.error("WebSocket error:", error);
    // Close and trigger reconnection.
    socket.close();
    attemptReconnect();
  };
}

/* Attempt socket reconnection with exponential backoff. */
function attemptReconnect() {
  if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
    reconnectAttempts++;
    const delay = Math.pow(2, reconnectAttempts) * 1000; // ms

    console.log(
      `Attempting to reconnect... Attempt ${reconnectAttempts} in ${delay / 1000} seconds`,
    );

    setTimeout(() => {
      connectSocket();
    }, delay);
  } else {
    console.log(
      "Max reconnection attempts reached. WebSocket will not reconnect.",
    );
  }
}

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
    // TODO: Need to ensure that an entry for the element exists as this could be
    // a different client from the uploader's.
    const doc = message.payload;
    fileLiElement = document.querySelector(`#file-list [data-id="${doc.id}"]`);
    fileLiElement.dataset.status = doc.status;
    fileLiElement.querySelector(".file-status-indicator").textContent =
      doc.status;
  }
}

connectSocket();
