// Talks to our FastAPI backend (same address as the page, so no CORS).
// AI-assisted file: read it so you can explain it. It only fetches data.

async function apiGet(path) {
  let res;
  try {
    res = await fetch(path, { headers: { Accept: "application/json" } });
  } catch (err) {
    throw new Error("Could not reach the NutriScore server. Is the backend running?");
  }
  let body = null;
  try { body = await res.json(); } catch (err) { /* response was not JSON */ }
  if (!res.ok) {
    // our backend always sends { error: { code, message } }
    throw new Error((body && body.error && body.error.message) || "Request failed (" + res.status + ").");
  }
  return body;
}

function searchProducts(q, page) { return apiGet("/api/search?q=" + encodeURIComponent(q) + "&page=" + (page || 1)); }
function getProduct(barcode)     { return apiGet("/api/product/" + encodeURIComponent(barcode)); }
function getAnalysis(barcode)    { return apiGet("/api/analysis/" + encodeURIComponent(barcode)); }
