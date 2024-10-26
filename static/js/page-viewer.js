const pageThumbnailContainers = document.querySelectorAll(".page-thumbnail");
const pageDisplay = document.querySelector("#page-display");
const pageMetadataContainer = document.querySelector(
  "#page-metadata-container",
);
const pageMetadataContainerToggle = document.querySelector(
  "#page-metadata-container-toggle",
);
const PAGE_IMAGE_ENDPOINT_PREFIX = "/page";
let activePageNumber;
// Used to weed out invalid page numbers passed through the url.
let validPageNumbers = new Set();
// Array of object, where each slot holds metadata for the corresponding page
// number (1-indexed) - this in effect delays fetching the info until it's needed
// and caches it.
pageInfoRegistry = [];

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

pageMetadataContainerToggle.addEventListener("click", async () => {
  if (activePageNumber && pageMetadataContainerHidden()) {
    pageMetadataContainer.classList.remove("tucked-away");
    await showPageInfo(activePageNumber);
  } else {
    pageMetadataContainer.classList.add("tucked-away");
  }
});

/* Display the page with the number in the url # fragment, if it exists. */
function navigateToPage() {
  if (window.location.hash) {
    let pageNumber = parseInt(window.location.hash.substring(1));

    if (validPageNumbers.has(pageNumber)) {
      displayPage(pageNumber);

      // Highlight the correct page number thumbnail.
      document.querySelectorAll(`.page-thumbnail.active-page`).forEach((el) => {
        el.classList.remove("active-page");
      });
      let currentActivePageThumbnail = document.querySelector(
        `[data-page-number="${pageNumber}"]`,
      );
      activePageNumber = pageNumber;
      currentActivePageThumbnail.classList.add("active-page");

      // If the page metadata display is visible, update it with the current page's info.
      if (!pageMetadataContainerHidden()) {
        showPageInfo(pageNumber);
      }
    }
  }
}

/* Display a page, given its number.

  @param {number} pageNumber - The page to "navigate" to.
*/
function displayPage(pageNumber) {
  let displayedImage = pageDisplay.querySelector("img");
  if (displayedImage) {
    displayedImage.remove();
  }

  let pageImage = document.createElement("img");
  pageImage.src = `${PAGE_IMAGE_ENDPOINT_PREFIX}/${DOCUMENT_ID}/${pageNumber}`;
  pageDisplay.appendChild(pageImage);
}

/* Check whether the page metadata display is hidden.

  @returns {boolean} - true if the display is hidden, false if it's visible.
*/
function pageMetadataContainerHidden() {
  return pageMetadataContainer.classList.contains("tucked-away");
}

/* Get page metadata from pageInfoRegistry or the server and return it.

  Cache it in pageInfoRegistry if it wasn't already there.

  @returns {Object} - Metadata about the page.
*/
async function getPageInfo(pageNumber) {
  // Cache hit
  if (pageInfoRegistry[pageNumber]) {
    return pageInfoRegistry[pageNumber];
  }

  const pageInfoEndpoint = `/page/${DOCUMENT_ID}/${pageNumber}/info`;

  try {
    const response = await fetch(pageInfoEndpoint);

    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }

    const responseData = await response.json();
    pageInfoRegistry[pageNumber] = responseData;
    return responseData;
  } catch (error) {
    console.error("Error: ", error);
  }
}

/* Display page metadata in the sidebar. */
async function showPageInfo(pageNumber) {
  let pageInfo = await getPageInfo(pageNumber);
  console.log(pageInfo);

  const pageSummaryElement =
    pageMetadataContainer.querySelector(".page-summary");
  const pageTextElement = pageMetadataContainer.querySelector(".page-text");

  if (pageInfo["summary"]) {
    pageSummaryElement.textContent = pageInfo["summary"];
  } else {
    pageSummaryElement.textContent = "None";
  }

  if (pageInfo["text"]) {
    pageTextElement.textContent = pageInfo["text"];
  } else {
    pageTextElement.textContent = "None";
  }
}
