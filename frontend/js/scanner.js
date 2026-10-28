// Barcode lookup: scan with the camera, scan a photo, or type the number.
// When a barcode is read, we open its product page.
// Scanning is done by the html5-qrcode library (js/lib/html5-qrcode.min.js).

const scanStatusEl = document.getElementById("scan-status");
const scanToggle = document.getElementById("scan-toggle");
const photoBtn = document.getElementById("scan-photo-btn");
const photoInput = document.getElementById("scan-photo");

let scanner = null;     // the library object, created the first time it is needed
let cameraOn = false;

function setScanStatus(text, isError) {
  scanStatusEl.textContent = text;
  scanStatusEl.classList.toggle("error", Boolean(isError));
}

// Product barcodes (EAN-8, UPC-E, UPC-A, EAN-13) are 8 to 14 digits.
function isBarcode(text) { return /^\d{8,14}$/.test(text); }

function goToProduct(code) {
  window.location.href = "product.html?barcode=" + encodeURIComponent(code);
}

function getScanner() {
  if (!scanner) {
    scanner = new Html5Qrcode("reader", {
      formatsToSupport: [
        Html5QrcodeSupportedFormats.EAN_13, Html5QrcodeSupportedFormats.EAN_8,
        Html5QrcodeSupportedFormats.UPC_A, Html5QrcodeSupportedFormats.UPC_E,
      ],
      experimentalFeatures: { useBarCodeDetectorIfSupported: true },   // faster where the browser supports it
    });
  }
  return scanner;
}

// Prefer the back camera on phones; on a laptop there is usually just one.
async function pickCamera() {
  const cameras = await Html5Qrcode.getCameras();         // asks for camera permission
  if (!cameras.length) throw new Error("NotFoundError");
  const back = cameras.find(function (c) { return /back|rear|environment/i.test(c.label); });
  return (back || cameras[cameras.length - 1]).id;
}

function cameraErrorText(err) {
  const msg = [err && err.name, err && err.message, String(err)].join(" ");   // check name AND message
  if (/NotAllowed|Permission/i.test(msg)) return "Camera permission is blocked. Allow it in the address bar, or scan a photo, or type the number.";
  if (/NotFound/i.test(msg)) return "No camera found. Scan a photo or type the number instead.";
  if (!window.isSecureContext) return "The camera only works on localhost or https. Scan a photo or type the number instead.";
  return "Could not start the camera. Scan a photo or type the number instead.";
}

async function startCamera() {
  if (typeof Html5Qrcode === "undefined") { setScanStatus("The scanner library did not load. Type the number instead.", true); return; }
  setScanStatus("Starting camera...");
  try {
    const cameraId = await pickCamera();
    await getScanner().start(
      cameraId,
      { fps: 10, qrbox: function (w, h) { return { width: Math.min(w - 20, 320), height: Math.min(h - 20, 140) }; } },
      onScanSuccess,
      function () { /* runs for every frame without a barcode: ignore */ }
    );
    cameraOn = true;
    scanToggle.textContent = "Stop camera";
    setScanStatus("Hold the barcode steady inside the box.");
  } catch (err) {
    setScanStatus(cameraErrorText(err), true);
  }
}

async function stopCamera() {
  if (!cameraOn) return;
  cameraOn = false;
  try { await scanner.stop(); scanner.clear(); } catch (err) { /* already stopped */ }
  scanToggle.textContent = "Start camera";
}

async function onScanSuccess(text) {
  if (!isBarcode(text)) return;                   // ignore anything that is not a product barcode
  await stopCamera();
  setScanStatus("Found " + text + ". Opening the product...");
  goToProduct(text);
}

scanToggle.addEventListener("click", function () {
  if (cameraOn) { stopCamera(); setScanStatus(""); } else { startCamera(); }
});

// Scan a photo of a barcode (useful on a laptop, or when the camera cannot focus)
photoBtn.addEventListener("click", function () { photoInput.click(); });
photoInput.addEventListener("change", async function () {
  const file = photoInput.files[0];
  if (!file) return;
  if (typeof Html5Qrcode === "undefined") { setScanStatus("The scanner library did not load. Type the number instead.", true); return; }
  await stopCamera();
  setScanStatus("Reading the photo...");
  try {
    const text = await getScanner().scanFile(file, false);
    if (isBarcode(text)) { goToProduct(text); }
    else { setScanStatus("That code is not a product barcode.", true); }
  } catch (err) {
    setScanStatus("No barcode found in that photo. Try a sharper, closer picture.", true);
  }
  photoInput.value = "";
});

// Typed barcode
document.getElementById("barcode-form").addEventListener("submit", function (e) {
  e.preventDefault();
  const code = document.getElementById("barcode").value.trim();
  if (!isBarcode(code)) { setScanStatus("A barcode is 8 to 14 digits, numbers only.", true); return; }
  goToProduct(code);
});
