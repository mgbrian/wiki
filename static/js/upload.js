const uploadForm = document.getElementById("file-upload-form");
const fileInput = document.getElementById("file-input");
const uploadButton = document.querySelector(
  "#files-list-container .upload-button",
);
const fileUploadQueueContainer = document.getElementById(
  "file-upload-queue-container",
);
const fileUploadQueueUl = document.getElementById("file-upload-queue");
// const retryUploadButton = document.querySelector(
//   "#file-upload-queue .retry-upload-button",
// );
const fileList = document.getElementById("file-list");
const FILE_UPLOAD_ENDPOINT = "/upload";
const FILE_LIST_ENDPOINT = "/files";
const DOCUMENT_ENDPOINT_PREFIX = "/document";

const fileUploadQueue = {
  queued: [],
  uploading: [],
  failed: [],
};
// Whether or not the queue is currently being processed.
let queueProcessing = false;

document.addEventListener("DOMContentLoaded", fetchFileList);
uploadButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", queueFiles);

/* Add selected files to the file upload queue. Event handler for fileInput change.*/
async function queueFiles(event) {
  // ** TODO: Dedupe! **
  if (!fileInput.files.length) {
    console.log("No files.");
    return;
  }
  for (let file of fileInput.files) {
    console.log(file);
    fileUploadQueue["queued"].push({
      name: file.name,
      size: file.size,
      id: crypto.randomUUID(),
      file: file,
    });
  }
  // Reset file input
  fileInput.value = "";
  renderFileUploadQueue();
  processQueue();
}

/* Re-add a failed file to the queue -- onclick handler for retry upload buttons.

  @param {string} fileId - The id of a file in the failed list that should be
    moved to the queued list.
*/
async function requeueFailedFile(fileId) {
  const file = fileUploadQueue["failed"].filter((f) => f.id === fileId)[0];

  if (!file) {
    return;
  }
  fileUploadQueue["queued"].push(file);

  // Remove from failed list.
  fileUploadQueue["failed"] = fileUploadQueue["failed"].filter(
    (f) => f.id !== fileId,
  );
  renderFileUploadQueue();
  processQueue();
}

/* Attempt to upload queued files. Mark upload failures accordingly. */
async function processQueue() {
  if (queueProcessing) {
    return;
  }
  queueProcessing = true;
  while (fileUploadQueue["queued"].length > 0) {
    const file = fileUploadQueue["queued"].shift();
    fileUploadQueue["uploading"].push(file);

    try {
      const fileUploadSuccessful = await uploadFile(file);
      // Remove file from uploading queue
      fileUploadQueue["uploading"] = fileUploadQueue["uploading"].filter(
        (f) => f.id !== file.id,
      );
      // ..and add it to failed queue if it failed
      if (!fileUploadSuccessful) {
        fileUploadQueue["failed"].push(file);
      }
    } catch (error) {
      fileUploadQueue["failed"].push(file);
      // TODO: Render errors somewhere in the UI
      console.error("Upload failed for file:", file, error);
    }

    // Update queue display
    renderFileUploadQueue();
  }
  queueProcessing = false;
}

/* Upload a given file.

  @param {object} - Object representing the file to upload.
*/
async function uploadFile(file) {
  // TODO: Standardize file vs document naming convention.
  if (!file) {
    return;
  }

  const formData = new FormData();
  formData.append("file", file.file);
  formData.append("id", file.id);

  try {
    const response = await fetch(FILE_UPLOAD_ENDPOINT, {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      fetchFileList();
      return true;
    } else {
      let errorMessagePayload = await response.json();
      alert("Failed to upload file. " + errorMessagePayload.error || "");
      return false;
    }
  } catch (error) {
    console.error("Error uploading file:", error);
    alert("An error occurred while uploading the file.");
    return false;
  }
}

/* Fetch and display the list of uploaded files */
async function fetchFileList() {
  try {
    const response = await fetch(FILE_LIST_ENDPOINT);
    const files = await response.json();

    fileList.innerHTML = "";

    for (let file of files) {
      renderFileDisplay(file);
    }
  } catch (error) {
    console.error("Error fetching file list:", error);
  }
}

/* Show the file queue if it contains anything. Hide it otherwise. */
function toggleFileUploadQueueVisibility() {
  if (
    fileUploadQueue["queued"].length ||
    fileUploadQueue["uploading"].length ||
    fileUploadQueue["failed"].length
  ) {
    fileUploadQueueContainer.classList.remove("hidden");
  } else {
    fileUploadQueueContainer.classList.add("hidden");
  }
}

/* Generate HTML for a list of files to be added to the file upload queue display.

  @returns {string} - HTML to display the given files in the file upload queue.
*/
function renderFileUploadQueue() {
  toggleFileUploadQueueVisibility();

  fileUploadQueueUl.innerHTML = "";
  for (let file of fileUploadQueue["queued"]) {
    fileUploadQueueUl.innerHTML += `
      <li data-status="queued" data-id="${file.id}">
          <span>${file.name}</span>
          <small class="file-status-indicator">Queued</small>
          <span class="material-symbols-outlined remove-upload-button">cancel</span>
      </li>
    `;
  }
  for (let file of fileUploadQueue["uploading"]) {
    fileUploadQueueUl.innerHTML += `
      <li data-status="uploading" data-id="${file.id}">
          <span>${file.name}</span>
          <small class="file-status-indicator">Uploading</small>
      </li>
    `;
  }
  for (let file of fileUploadQueue["failed"]) {
    fileUploadQueueUl.innerHTML += `
      <li data-status="failed" data-id="${file.id}">
          <span>${file.name}</span>
          <small class="file-status-indicator">Failed</small>
          <span class="material-symbols-outlined retry-upload-button" onclick=requeueFailedFile("${file.id}")>refresh</span>
          <span class="material-symbols-outlined remove-upload-button">cancel</span>
      </li>
    `;
  }

  const removeUploadButtons = fileUploadQueueUl.querySelectorAll(
    ".remove-upload-button",
  );

  for (let button of removeUploadButtons) {
    button.addEventListener("click", removeUpload);
  }
}

/* Remove an file from the upload queue. Event handler for the remove upload buttons. */
function removeUpload(event) {
  let fileId = event.currentTarget.parentElement.dataset.id;

  // Remove from uploadQueue -- the only two subqueues it could be in
  fileUploadQueue["uploading"] = fileUploadQueue["uploading"].filter(
    (f) => f.id !== fileId,
  );
  fileUploadQueue["failed"] = fileUploadQueue["failed"].filter(
    (f) => f.id !== fileId,
  );

  renderFileUploadQueue();
}

function renderFileDisplay(file) {
  const li = document.createElement("li");
  li.dataset.status = file.status;
  li.dataset.id = file.id || null;

  const fileLink = document.createElement("a");
  if (file.id) {
    fileLink.href = `${DOCUMENT_ENDPOINT_PREFIX}/${file.id}`;
  } else {
    fileLink.href = "#";
  }
  fileLink.textContent = file.filename;
  fileLink.setAttribute("target", "_blank");

  const statusIndicator = document.createElement("small");
  statusIndicator.textContent = file.status;
  statusIndicator.classList.add("file-status-indicator");

  const deleteButton = document.createElement("a");
  deleteButton.classList.add("delete-button");
  deleteButton.addEventListener("click", async () => {
    if (!confirm("Are you sure you want to delete the document?")) {
      return;
    }
    if (await deleteDocument(file.id)) {
      li.remove();
    } else {
      alert("There was a problem deleting the document.");
    }
  });

  const deleteButtonIcon = document.createElement("span");
  deleteButtonIcon.classList.add("material-symbols-outlined");
  deleteButtonIcon.textContent = "delete";
  deleteButton.appendChild(deleteButtonIcon);

  const downloadButton = document.createElement("a");
  downloadButton.classList.add("download-button");
  const downloadEndpoint = `/document/${file.id}/download`;
  downloadButton.href = downloadEndpoint;
  downloadButton.target = "_blank";
  const downloadButtonIcon = document.createElement("span");
  downloadButtonIcon.classList.add("material-symbols-outlined");
  downloadButtonIcon.textContent = "download";
  downloadButton.appendChild(downloadButtonIcon);

  li.appendChild(fileLink);
  li.appendChild(statusIndicator);
  li.appendChild(downloadButton);
  li.appendChild(deleteButton);

  fileList.appendChild(li);
}

/* Delete a document, given its id.

  @returns {boolean} - true if document is successfully deleted. False otherwise.
*/
async function deleteDocument(documentId) {
  const deleteEndpoint = `/document/${documentId}/delete`;

  try {
    const response = await fetch(deleteEndpoint);

    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }

    const responseData = await response.json();
    console.log("Delete successful:", responseData);

    return true;
  } catch (error) {
    console.error("Error: ", error);
    return false;
  }
}
