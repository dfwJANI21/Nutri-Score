// Product page: loads the analysis and fills the page.

const statusEl = document.getElementById("status");
const barcode = new URLSearchParams(window.location.search).get("barcode");

const NUTRIENTS = [
  ["Energy", "energy_kj", "kJ"], ["Energy", "energy_kcal", "kcal"], ["Fat", "fat_g", "g"],
  ["Saturated fat", "saturated_fat_g", "g"], ["Carbohydrates", "carbohydrates_g", "g"],
  ["Sugars", "sugars_g", "g"], ["Fibre", "fiber_g", "g"], ["Protein", "proteins_g", "g"],
  ["Salt", "salt_g", "g"], ["Fruit, vegetables and legumes", "fruits_veg_legumes_pct", "%"],
];

function setStatus(text, isError) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", Boolean(isError));
}

function gradeBadge(letter) {
  const span = document.createElement("span");
  span.className = "grade grade-" + letter.toLowerCase();
  span.textContent = letter.toUpperCase();
  span.setAttribute("aria-label", "Grade " + letter.toUpperCase());
  return span;
}

async function load() {
  if (!barcode) { setStatus("No barcode given. Go back and search for a product.", true); return; }
  setStatus("Loading...");
  try {
    renderProduct(await getAnalysis(barcode));
    setStatus("");
  } catch (err) {
    setStatus(err.message, true);            // not found / API failure state
  }
}

function setText(id, text) { document.getElementById(id).textContent = text || ""; }

function renderProduct(data) {
  const p = data.product;
  document.title = (p.name || "Product") + " - NutriScore";
  setText("product-name", p.name || "Unnamed product");
  setText("product-brand", p.brand ? "Brand: " + p.brand : "");
  setText("product-category", p.category ? "Category: " + p.category : "");
  setText("product-barcode", p.barcode);

  const img = document.getElementById("product-image");
  if (p.image_url) { img.src = p.image_url; img.alt = p.name || "Product photo"; img.hidden = false; }

  // Nutrition table: a missing value is shown as "not provided", never as 0
  const body = document.getElementById("nutrition-body");
  body.innerHTML = "";
  NUTRIENTS.forEach(function (row) {
    const value = p.nutrition[row[1]];
    const tr = document.createElement("tr");
    const th = document.createElement("th");
    th.scope = "row"; th.textContent = row[0];
    const td = document.createElement("td");
    if (value === null || value === undefined) { td.textContent = "not provided"; td.className = "na"; }
    else { td.textContent = Math.round(value * 100) / 100 + " " + row[2]; }
    tr.append(th, td);
    body.appendChild(tr);
  });
  setText("completeness", p.missing_nutrients.length
    ? "Not provided by the source: " + p.missing_nutrients.join(", ") + "."
    : "All the nutrients needed for the score were provided.");

  setText("ingredients", p.ingredients_text || "Ingredients not provided.");
  document.getElementById("source-link").href = p.source_url;

  // Score 1: the grade stored by Open Food Facts (source data, not ours)
  const srcEl = document.querySelector("#source-grade .value");
  srcEl.textContent = "";
  if (data.source_grade) {
    srcEl.append(gradeBadge(data.source_grade));
    const note = document.createElement("p");
    note.className = "source-note";
    note.textContent = "Grade stored in Open Food Facts. It was not calculated by this site.";
    srcEl.after(note);
  } else {
    srcEl.textContent = "Not provided";
  }

  // Score 2: calculated by OUR scoring engine
  const calc = data.calculated;
  const calcEl = document.querySelector("#calculated-grade .value");
  const reasonEl = document.querySelector("#calculated-grade .reason");
  const breakdown = document.getElementById("breakdown");
  if (calc.status === "calculated") {
    calcEl.textContent = "";
    calcEl.appendChild(gradeBadge(calc.grade));
    reasonEl.textContent = calc.algorithm + ".";
    breakdown.innerHTML = "";
    const d = calc.details;
    const lines = [];
    Object.keys(d.negative_points).forEach(function (k) { lines.push("Unfavourable, " + k + ": " + d.negative_points[k] + " points"); });
    Object.keys(d.positive_points).forEach(function (k) { lines.push("Favourable, " + k + ": " + d.positive_points[k] + " points"); });
    if (!d.protein_counted) lines.push("Protein is not counted because the unfavourable points are 11 or more.");
    lines.push("Score = " + d.N + " \u2212 " + d.P + " = " + d.score);
    lines.forEach(function (text) { const li = document.createElement("li"); li.textContent = text; breakdown.appendChild(li); });
    breakdown.hidden = false;
  } else {
    calcEl.textContent = "Score unavailable";
    reasonEl.textContent = calc.reason || "";
    breakdown.hidden = true;
  }

  document.getElementById("product").hidden = false;
}

load();
