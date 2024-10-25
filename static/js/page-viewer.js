const pageThumbnailContainers = document.querySelectorAll(".page-thumbnail");
const pageDisplay = document.querySelector("#page-display");
const PAGE_IMAGE_ENDPOINT_PREFIX = "/page/";

for (let pageThumbnailContainer of pageThumbnailContainers) {
  pageThumbnailContainer.addEventListener("click", displayPage);
}

document.addEventListener("DOMContentLoaded", () => {
  if (pageThumbnailContainers.length) {
    pageThumbnailContainers[0].click();
  }
});

/* Display a page. Click handler for page thumbnails. */
function displayPage(event) {
  let pageThumbnailContainer = event.currentTarget;
  pageDisplay.innerHTML = "";

  let pageId = pageThumbnailContainer.dataset.pageId;

  let pageImage = document.createElement("img");
  pageImage.src = `${PAGE_IMAGE_ENDPOINT_PREFIX}/${pageId}`;
  pageDisplay.appendChild(pageImage);
}
