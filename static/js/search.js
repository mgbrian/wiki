const searchInputBox = document.getElementById("search");
const resultsBox = document.getElementById("results-box");

const SEARCH_ENDPOINT = "/search";

searchInputBox.addEventListener("input", updateSearchResults);

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
    resultsBox.innerHTML += `<p class="search-result">${result.text}</p>`;
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
