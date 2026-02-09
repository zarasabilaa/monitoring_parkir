/* ================= ANTI DOUBLE SCAN ================= */
let lastScan = 0;

/* ================= QR SCAN ================= */
function onScanSuccess(decodedText) {
    const now = Date.now();
    if (now - lastScan < 3000) return; // anti double scan 3 detik
    lastScan = now;

    fetch("/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ npm: decodedText })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("result").innerText =
            `${data.nama} - ${data.type}`;
        document.getElementById("beep").play();
        setTimeout(() => location.reload(), 1000);
    });
}

new Html5QrcodeScanner("reader", {
    fps: 10,
    qrbox: 250
}).render(onScanSuccess);

/* ================= AMBIL DATA DARI HTML ================= */
const chartJSON = document.getElementById("chart-data").textContent;
const chartDataParsed = JSON.parse(chartJSON);

/* ================= CHART ================= */
const ctx = document.getElementById("parkingChart").getContext("2d");

new Chart(ctx, {
    type: "bar",
    data: {
        labels: chartDataParsed.labels,
        datasets: [{
            label: "Durasi Parkir (Menit)",
            data: chartDataParsed.data,
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: { beginAtZero: true }
        }
    }
});

/* ================= EXPORT PDF ================= */
function exportPDF() {
    const image = document.getElementById("parkingChart").toDataURL();

    fetch("/export_pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image })
    })
    .then(res => res.blob())
    .then(blob => {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "Laporan_Parkir.pdf";
        a.click();
    });
}
