const uploadForm = document.getElementById("file-upload-form");
const fileInput = document.getElementById("file-input");
const fileList = document.getElementById("file-list");
const FILE_UPLOAD_ENDPOINT = "/upload";
const FILE_LIST_ENDPOINT = "/files";
const DOCUMENT_ENDPOINT_PREFIX = "/document";

document.addEventListener("DOMContentLoaded", fetchFileList);
uploadForm.addEventListener("submit", uploadFile);

/* Event handler for the file upload form. */
async function uploadFile(event) {
  event.preventDefault();

  // TODO: Standardize file vs document naming convention.
  const file = fileInput.files[0];

  if (!file) {
    alert("Please select a file!");
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
      // alert("File uploaded successfully!");
      // Reset file input and refresh file list
      fileInput.value = "";
      fetchFileList();
    } else {
      alert("Failed to upload file");
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
