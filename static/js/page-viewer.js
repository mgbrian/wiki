const pageThumbnailContainers = document.querySelectorAll(".page-thumbnail");
const pageDisplay = document.querySelector("#page-display");
const PAGE_IMAGE_ENDPOINT_PREFIX = "/page";
// Used to weed out invalid page numbers passed through the url.
let validPageNumbers = new Set();

document.addEventListener("DOMContentLoaded", () => {
  for (let pageThumbnailContainer of pageThumbnailContainers) {
    pageThumbnailContainer.addEventListener("click", (event) => {
      window.location.hash = event.currentTarget.dataset.pageNumber;
    });
    validPageNumbers.add(parseInt(pageThumbnailContainer.dataset.pageNumber));
  }

  if (window.location.hash) {
    navigateToPage();
  } else if (pageThumbnailContainers.length) {
    pageThumbnailContainers[0].click();
  }
});

window.addEventListener("hashchange", navigateToPage);

/* Display the page with the number in the url # fragment, if it exists. */
function navigateToPage() {
  if (window.location.hash) {
    let pageNumber = parseInt(window.location.hash.substring(1));

    if (validPageNumbers.has(pageNumber)) {
      displayPage(pageNumber);
    }
  }
}

/* Display a page, given its number.

  @param {number} pageNumber - The page to "navigate" to.
*/
function displayPage(pageNumber) {
  pageDisplay.innerHTML = "";

  let pageImage = document.createElement("img");
  pageImage.src = `${PAGE_IMAGE_ENDPOINT_PREFIX}/${DOCUMENT_ID}/${pageNumber}`;
  pageDisplay.appendChild(pageImage);
}
