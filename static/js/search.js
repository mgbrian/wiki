const keywordSearchRadioButton = document.getElementById(
  "keyword-search-radio-button",
);
const semanticSearchRadioButton = document.getElementById(
  "semantic-search-radio-button",
);

const semanticSearchSliderContainer = document.getElementById(
  "semantic-similarity-threshold-slider-container",
);
const semanticSearchSlider = document.getElementById(
  "semantic-similarity-threshold-slider",
);
const semanticSearchSliderValueDisplay = document.getElementById(
  "semantic-similarity-threshold-value",
);
const searchInputBox = document.getElementById("search");
const resultsBox = document.getElementById("results-box");

const SEARCH_ENDPOINT = "/search";
const DOCUMENT_ENDPOINT_PREFIX = "/document";

document.addEventListener(
  "DOMContentLoaded",
  toggleSemanticSearchSliderVisibility,
);

keywordSearchRadioButton.addEventListener(
  "change",
  toggleSemanticSearchSliderVisibility,
);
semanticSearchRadioButton.addEventListener(
  "change",
  toggleSemanticSearchSliderVisibility,
);

searchInputBox.addEventListener("input", updateSearchResults);

semanticSearchSlider.addEventListener("change", (event) => {
  sliderValue = event.target.value;
  semanticSearchSliderValueDisplay.textContent = sliderValue;
});

/* Send the current contents of the search box to the backend and update the
   results box with the results.
*/
async function updateSearchResults() {
  // Clear the results box of its current contents.
  resultsBox.innerHTML = "";
  let searchResults = await search(searchInputBox.value);

  // Hide the results box if there are no results to show. It is hidden by
  // default -- see HTML/CSS.
  if (searchResults.length > 0) {
    resultsBox.classList.remove("hidden");
  } else {
    resultsBox.classList.add("hidden");
  }

  for (let result of searchResults) {
    resultsBox.innerHTML += `
      <a href="${DOCUMENT_ENDPOINT_PREFIX}/${result.document.id}#${result.number}">
          <p class="search-result">
              <small class="search-result-header">${result.document.name} - ${result.number}</small>
              <span class="search-result-text">${result.text}</span>
          </p>
      </a>
    `;
  }
}

/* POST the searchTest to the backend and return the results.

  @param {string} searchText - The text to search for.

  @returns {Array of Object} - The relevant search results.
*/
async function search(searchText) {
  if (searchText === "") {
    return [];
  }

  try {
    const response = await fetch(SEARCH_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: searchText, mode: getSelectedSearchMode() }),
    });

    if (!response.ok) {
      console.error("HTTP Error! Response:");
      console.error(response);
      throw new Error(`Something went wrong.`);
    }

    const results = await response.json();
    console.log("----");
    console.log(`Searching for ${searchText} returned:`);
    console.log(results);
    console.log("----");
    return results;
  } catch (error) {
    console.error(`Error searching for ${searchText}`);
    console.error("Error:", error);
  }
}

function toggleSemanticSearchSliderVisibility() {
  if (keywordSearchRadioButton.checked) {
    semanticSearchSliderContainer.classList.add("hidden");
  } else {
    semanticSearchSliderContainer.classList.remove("hidden");
  }
}

function getSelectedSearchMode() {
  const selectedMode = document.querySelector('input[name="mode"]:checked');
  return selectedMode ? selectedMode.value : null;
}
