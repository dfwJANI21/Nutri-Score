// Search by name: send the text to the backend, show the products it returns.
// (Barcode scanning lives in scanner.js.)

const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const pagerEl = document.getElementById("pager");
const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");
const pageLabel = document.getElementById("page-label");

let currentQuery = "";
let currentPage = 1;

function setStatus(text, isError) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", Boolean(isError));
}

// A small coloured letter, e.g. <span class="grade grade-b">B</span>
function gradeBadge(letter) {
  const span = document.createElement("span");
  span.className = "grade grade-" + letter.toLowerCase();
  span.textContent = letter.toUpperCase();
  span.setAttribute("aria-label", "Grade " + letter.toUpperCase());
  return span;
}

async function runSearch(q, page) {
  currentQuery = q;
  currentPage = page;
  setStatus("Searching...");
  resultsEl.innerHTML = "";
  pagerEl.hidden = true;
  try {
    renderResults(await searchProducts(q, page));
  } catch (err) {
    setStatus(err.message, true);              // API failure state
  }
}

function renderResults(data) {
  resultsEl.innerHTML = "";
  if (data.results.length === 0) {
    setStatus('No products found for "' + data.query + '". Try another name, or scan the barcode.');
    return;
  }

  const template = document.getElementById("result-template");
  data.results.forEach(function (hit) {
    const item = template.content.cloneNode(true);
    item.querySelector(".result-link").href = "product.html?barcode=" + encodeURIComponent(hit.barcode);
    item.querySelector(".result-name").textContent = hit.name || "Unnamed product";
    item.querySelector(".result-brand").textContent = hit.brand || "";
    item.querySelector(".result-category").textContent = hit.category || "";

    const img = item.querySelector(".result-img");
    if (hit.image_url) { img.src = hit.image_url; img.loading = "lazy"; } else { img.remove(); }

    const gradeEl = item.querySelector(".result-source-grade");
    if (hit.off_nutriscore_grade) {
      gradeEl.append("Open Food Facts grade: ", gradeBadge(hit.off_nutriscore_grade));
    } else {
      gradeEl.remove();
    }
    resultsEl.appendChild(item);
  });

  setStatus("Showing " + data.results.length + ' products for "' + data.query + '".');
  pageLabel.textContent = "Page " + data.page;
  prevBtn.disabled = data.page <= 1;
  nextBtn.disabled = data.results.length < data.page_size;
  pagerEl.hidden = false;
  document.getElementById("results-heading").focus();
}

prevBtn.addEventListener("click", function () { runSearch(currentQuery, currentPage - 1); });
nextBtn.addEventListener("click", function () { runSearch(currentQuery, currentPage + 1); });

document.getElementById("name-form").addEventListener("submit", function (e) {
  e.preventDefault();
  const q = document.getElementById("q").value.trim();
  if (q.length < 2) { setStatus("Type at least 2 characters.", true); return; }
  runSearch(q, 1);
});

setStatus("Search for a product above to see results.");
