// Search page: form handling and rendering of results.

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

function gradeBadge(letter) {
  const span = document.createElement("span");
  span.className = "grade grade-" + letter;
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
    const data = await searchProducts(q, page);
    renderResults(data);
  } catch (err) {
    setStatus(err.message, true);            // API failure state
  }
}

function renderResults(data) {
  resultsEl.innerHTML = "";
  if (data.results.length === 0) {
    setStatus('No products found for "' + data.query + '". Try a different name, or a barcode.');
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
  setStatus("Showing " + data.results.length + " products for \"" + data.query + "\" (page " + data.page + ").");
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

document.getElementById("barcode-form").addEventListener("submit", function (e) {
  e.preventDefault();
  const code = document.getElementById("barcode").value.trim();
  if (!/^\d{8,14}$/.test(code)) { setStatus("A barcode is 8 to 14 digits, numbers only.", true); return; }
  window.location.href = "product.html?barcode=" + encodeURIComponent(code);
});

setStatus("Search for a product above to see results.");
