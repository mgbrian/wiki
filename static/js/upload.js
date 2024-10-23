const uploadForm = document.getElementById("file-upload-form");
const fileInput = document.getElementById("file-input");
const fileList = document.getElementById("file-list");
const FILE_UPLOAD_ENDPOINT = "/upload";
const FILE_LIST_ENDPOINT = "/files";

document.addEventListener("DOMContentLoaded", fetchFileList);
uploadForm.addEventListener("submit", uploadFile);

/* Event handler for the file upload form. */
async function uploadFile(event) {
  event.preventDefault();

  const file = fileInput.files[0];

  if (!file) {
    alert("Please select a file!");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(FILE_UPLOAD_ENDPOINT, {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      alert("File uploaded successfully!");
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
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = `/files/${file.filename}`;
      a.textContent = file.filename;
      a.setAttribute("target", "_blank");
      li.appendChild(a);
      fileList.appendChild(li);
    }
  } catch (error) {
    console.error("Error fetching file list:", error);
  }
}
