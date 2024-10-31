const uploadForm = document.getElementById("file-upload-form");
const fileInput = document.getElementById("file-input");
const uploadButton = document.querySelector(
  "#files-list-container .upload-button",
);
const fileUploadQueueContainer = document.getElementById(
  "file-upload-queue-container",
);
const fileUploadQueueUl = document.getElementById("file-upload-queue");
const fileList = document.getElementById("file-list");
const FILE_UPLOAD_ENDPOINT = "/upload";
const FILE_LIST_ENDPOINT = "/files";
const DOCUMENT_ENDPOINT_PREFIX = "/document";

const fileUploadQueue = {
  queued: [],
  uploading: [],
  failed: [],
};

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
  fileUploadQueue["queued"].push(...Array.from(fileInput.files));
  // Reset file input
  fileInput.value = "";
  fileUploadQueueUl.innerHTML += renderFileUploadQueue();
  toggleFileUploadQueueVisibility();
}

/* Upload a given file.

  @param {object} - Object representing the file to upload.
*/
async function uploadFile(file) {
  // TODO: Standardize file vs document naming convention.

  if (!file) {
    return;
  }
  const documentId = crypto.randomUUID();

  const formData = new FormData();
  formData.append("file", file);
  formData.append("id", documentId);

  try {
    const response = await fetch(FILE_UPLOAD_ENDPOINT, {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      // ** 1. Remove file from upload queue (and file list -- maybe have own queue structure) and add to file list with status uploaded
      // 2. If error mark it as such and display in UI
      // 3. Call toggleUploadQueueDisplay
      fileInput.value = "";
      fetchFileList();
    } else {
      let errorMessagePayload = await response.json();
      alert("Failed to upload file. " + errorMessagePayload.error || "");
    }
  } catch (error) {
    console.error("Error uploading file:", error);
    alert("An error occurred while uploading the file.");
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
  let resultHTML = "";
  for (let file of fileUploadQueue["queued"]) {
    resultHTML += `
      <li data-status="queued" data-id="">
          <span>${file.name}</span>
          <small class="file-status-indicator">Queued</small>
          <span class="material-symbols-outlined remove-upload-button">cancel</span>
      </li>
    `;
  }
  for (let file of fileUploadQueue["uploading"]) {
    resultHTML += `
      <li data-status="uploading" data-id="">
          <span>${file.name}</span>
          <small class="file-status-indicator">Uploading</small>
      </li>
    `;
  }
  for (let file of fileUploadQueue["failed"]) {
    resultHTML += `
      <li data-status="failed" data-id="">
          <span>${file.name}</span>
          <small class="file-status-indicator">Failed</small>
          <span class="material-symbols-outlined retry-upload-button">refresh</span>
      </li>
    `;
  }
  return resultHTML;
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
