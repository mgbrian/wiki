const SEARCH_INPUT_BOX = document.getElementById("search");
const RESULTS_BOX = document.getElementById("results-box");

const SEARCH_ENDPOINT = "/search";

SEARCH_INPUT_BOX.addEventListener("input", updateSearchResults);

/* Send the current contents of the search box to the backend and update the
   results box with the results.
*/
async function updateSearchResults() {
  // Clear the results box of its current contents.
  RESULTS_BOX.innerHTML = "";
  let searchResults = await search(SEARCH_INPUT_BOX.value);

  // Hide the results box if there are no results to show. It is hidden by
  // default -- see HTML/CSS.
  if (searchResults.length > 0) {
    RESULTS_BOX.classList.remove("hidden");
  } else {
    RESULTS_BOX.classList.add("hidden");
  }

  for (let result of searchResults) {
    RESULTS_BOX.innerHTML += `<p class="search-result">${result.text}</p>`;
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
      body: JSON.stringify({ text: searchText }),
    });

    if (!response.ok) {
      console.error(`HTTP Error! Response: ${response}`);
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
