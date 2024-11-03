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

// How long to wait after a keyboard input to search. This is to avoid bombarding
// the server with a search query for every keystroke.
const BASE_DELAY = 500; // milliseconds. baseline delay
const MAX_DELAY = 2000; // cap to prevent excessive delays
let lastKeystrokeTime = Date.now();
let adaptiveDelay = BASE_DELAY;
let searchTimeoutId; // pointer to setTimeout call

document.addEventListener(
  "DOMContentLoaded",
  toggleSemanticSearchSliderVisibility,
);

keywordSearchRadioButton.addEventListener("change", () => {
  toggleSemanticSearchSliderVisibility();
  updateSearchResults();
});
semanticSearchRadioButton.addEventListener("change", () => {
  toggleSemanticSearchSliderVisibility();
  updateSearchResults();
});

semanticSearchSlider.addEventListener("change", (event) => {
  // sliderValue = event.target.value;
  // semanticSearchSliderValueDisplay.textContent = `>${sliderValue * 100}% similarity`;
  updateSearchResults();
});

searchInputBox.addEventListener("input", () => {
  // Clear previous timer if there's one.'
  // This is at the head of the algorithm so that initial input delay is are
  // influenced by the previous state of the input box
  // TODO: Reason through every case.
  clearTimeout(searchTimeoutId);
  searchTimeoutId = setTimeout(updateSearchResults, adaptiveDelay);

  const currentTime = Date.now();
  const timeSinceLastKeystroke = currentTime - lastKeystrokeTime;
  lastKeystrokeTime = currentTime;

  // When the input is emptied out, reset delay to BASE_DELAY so the first input
  // next time doesn't have to wait potentially up to MAX_DELAY.
  if (searchInputBox.value === "") {
    adaptiveDelay = BASE_DELAY;
  } else {
    // Adjust delay based on typing speed, capped at MAX_DELAY
    adaptiveDelay = Math.min(
      Math.max(timeSinceLastKeystroke * 1.1, BASE_DELAY),
      MAX_DELAY,
    );
  }
});

/* Send the current contents of the search box to the backend and update the
   results box with the results.
*/
async function updateSearchResults() {
  // Clear the results box of its current contents.
  resultsBox.innerHTML = "";
  let searchTerm = searchInputBox.value;
  let searchResults = await search(searchTerm);

  // Hide the results box if there are no results to show. It is hidden by
  // default -- see HTML/CSS.
  if (searchResults.length > 0) {
    resultsBox.classList.remove("hidden");
  } else {
    resultsBox.classList.add("hidden");
  }

  for (let result of searchResults) {
    let resultText = result.text;
    if (getSelectedSearchMode() == "keyword") {
      resultText = highlightTermInText(searchTerm, result.text);
    }
    resultsBox.innerHTML += `
      <a href="${DOCUMENT_ENDPOINT_PREFIX}/${result.document.id}#${result.number}">
          <p class="search-result">
              <small class="search-result-header">${result.document.name} - ${result.number}</small>
              <span class="search-result-text">${resultText}</span>
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
    let mode = getSelectedSearchMode();
    let payload = { text: searchText, mode: mode };
    if (mode === "semantic") {
      payload["threshold"] = parseFloat(semanticSearchSlider.value);
    }

    const response = await fetch(SEARCH_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
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
    // invisible instead of hidden so its width is accounted for
    // in main's min-width: fit-content on small devices.
    semanticSearchSliderContainer.classList.add("invisible");
  } else {
    semanticSearchSliderContainer.classList.remove("invisible");
  }
}

function getSelectedSearchMode() {
  const selectedMode = document.querySelector('input[name="mode"]:checked');
  return selectedMode ? selectedMode.value : null;
}

/* Highlight all occurences of a given string in a piece of text.

  @param {string} term - The term to highlight.
  @param {string} text - The text within which to highlight the term.

  @returns {string} - The text with all occurences of term surrounded with a
    <span> with a class that can be styled to achieve the highlight.
*/
function highlightTermInText(term, text) {
  if (!term || !text) return text;

  // Escape special characters
  const escapedTerm = term.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&");

  // Only match full-word occurences of term in text i.e. 'cat' shouldn't get
  // highlighted in 'category'
  // const regex = new RegExp(`\\b(${escapedTerm})\\b`, "gi");
  const regex = new RegExp(`(${escapedTerm})`, "gi");

  return text.replace(regex, '<span class="highlight">$1</span>');
}
