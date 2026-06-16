// ExcelFlow Frontend Application Logic

// Global chart variables to allow destroying/re-creating instances
let productChart = null;
let regionChart = null;
let monthlyChart = null;
let currentReportId = null;

// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const loadMockBtn = document.getElementById('load-mock-btn');
const loader = document.getElementById('loader');
const resultsContainer = document.getElementById('results-container');
const pipelineAlert = document.getElementById('pipeline-alert');
const pipelineDetails = document.getElementById('pipeline-details');
const downloadXlsxBtn = document.getElementById('download-xlsx-btn');
const cacheBadge = document.getElementById('cache-badge');
const clearCacheBtn = document.getElementById('clear-cache-btn');

// KPIs
const kpiRevenue = document.getElementById('kpi-revenue');
const kpiOrders = document.getElementById('kpi-orders');
const kpiAov = document.getElementById('kpi-aov');
const kpiEfficiency = document.getElementById('kpi-efficiency');

// Tables
const tableProductsBody = document.querySelector('#table-products tbody');
const tableRegionsBody = document.querySelector('#table-regions tbody');
const tableMonthlyBody = document.querySelector('#table-monthly tbody');

// Tabs
const tabButtons = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');

// Page Load initialization
document.addEventListener('DOMContentLoaded', () => {
    // 1. Check browser-based cache (localStorage)
    const cachedData = localStorage.getItem('excelflow_cached_data');
    if (cachedData) {
        try {
            const parsedData = JSON.parse(cachedData);
            logger("Loaded cached analysis data from browser storage");
            displayResults(parsedData, true);
        } catch (e) {
            console.error("Failed to parse cached data", e);
            localStorage.removeItem('excelflow_cached_data');
        }
    }

    // 2. Setup File Upload events
    dropZone.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Drag and Drop
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0 && files[0].name.endsWith('.csv')) {
            handleFileUpload(files[0]);
        } else {
            alert("Please drop a valid CSV sales file.");
        }
    });

    // 3. Mock Data trigger
    loadMockBtn.addEventListener('click', generateMockData);

    // 4. Download Excel Report trigger
    downloadXlsxBtn.addEventListener('click', () => {
        if (currentReportId) {
            window.open(`/api/download/${currentReportId}`, '_blank');
        }
    });

    // 5. Clear Cache trigger
    clearCacheBtn.addEventListener('click', clearBrowserCache);

    // 6. Tabs switching
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            tabPanes.forEach(pane => {
                pane.classList.remove('active');
                if (pane.id === targetTab) {
                    pane.classList.add('active');
                }
            });
        });
    });
});

// Helper for logger styling
function logger(msg) {
    console.log(`[ExcelFlow] ${msg}`);
}

// Upload CSV file to backend API
async function handleFileUpload(file) {
    showLoader(true);
    resultsContainer.classList.add('hidden');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Error cleaning and analyzing data.");
        }

        const data = await response.json();
        logger("Successful file upload & process");
        
        // Cache to browser localStorage
        localStorage.setItem('excelflow_cached_data', JSON.stringify(data));
        
        displayResults(data, false);
    } catch (err) {
        alert(`Failed to process CSV file: ${err.message}`);
        showLoader(false);
    }
}

// Generate Mock Data on Backend
async function generateMockData() {
    showLoader(true);
    resultsContainer.classList.add('hidden');

    try {
        const response = await fetch('/api/generate-from-mock', {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error("Failed to generate and process mock data.");
        }

        const data = await response.json();
        logger("Successfully generated & loaded mock data");
        
        // Cache to browser localStorage
        localStorage.setItem('excelflow_cached_data', JSON.stringify(data));
        
        displayResults(data, false);
    } catch (err) {
        alert(err.message);
        showLoader(false);
    }
}

// Show/Hide loader spinner
function showLoader(show) {
    if (show) {
        loader.classList.remove('hidden');
    } else {
        loader.classList.add('hidden');
    }
}

// Display processed dashboard results
function displayResults(data, isFromCache = false) {
    showLoader(false);
    resultsContainer.classList.remove('hidden');

    // Update report id
    currentReportId = data.report_id;
    
    // Update cache badge
    if (isFromCache) {
        cacheBadge.className = "badge badge-active";
        cacheBadge.innerHTML = '<i class="fa-solid fa-database"></i> Data Loaded from Cache';
        clearCacheBtn.classList.remove('hidden');
    } else {
        cacheBadge.className = "badge badge-active";
        cacheBadge.innerHTML = '<i class="fa-solid fa-database"></i> Session Synced';
        clearCacheBtn.classList.remove('hidden');
    }

    // Update Alert description
    const raw = data.metrics.raw_rows;
    const clean = data.metrics.cleaned_rows;
    const nulls = data.metrics.nulls_removed;
    const dupes = data.metrics.duplicates_removed;
    pipelineDetails.textContent = `Raw records: ${raw.toLocaleString()} | Cleaned: ${clean.toLocaleString()} (Dropped ${nulls.toLocaleString()} empty fields, ${dupes.toLocaleString()} duplicate Order IDs)`;

    // Update KPIs
    kpiRevenue.textContent = formatCurrency(data.kpis.total_revenue);
    kpiOrders.textContent = data.kpis.total_orders.toLocaleString();
    kpiAov.textContent = formatCurrency(data.kpis.average_order_value);
    
    const efficiency = raw > 0 ? ((clean / raw) * 100).toFixed(1) : 100;
    kpiEfficiency.textContent = `${efficiency}%`;

    // Populate Tables
    populateTables(data);

    // Render Browser-based Charts
    renderCharts(data);
}

// Clear browser cache & reset dashboard view
function clearBrowserCache() {
    localStorage.removeItem('excelflow_cached_data');
    currentReportId = null;
    
    // Reset cache indicators
    cacheBadge.className = "badge badge-inactive";
    cacheBadge.innerHTML = '<i class="fa-solid fa-database"></i> No Cached Data';
    clearCacheBtn.classList.add('hidden');
    resultsContainer.classList.add('hidden');
    
    // Destroy charts
    destroyCharts();
    
    fileInput.value = '';
    logger("Browser cache cleared and dashboard reset");
}

// Format number to USD Currency
function formatCurrency(val) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(val);
}

// Populate HTML summary tables
function populateTables(data) {
    // 1. Top 10 Products table
    tableProductsBody.innerHTML = '';
    data.top_products.forEach(p => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${p.Product}</strong></td>
            <td class="text-right">${formatCurrency(p.Revenue)}</td>
            <td class="text-right">${p.Quantity_Sold.toLocaleString()}</td>
            <td class="text-right">${p.Orders.toLocaleString()}</td>
        `;
        tableProductsBody.appendChild(row);
    });

    // 2. Regional Breakdown table
    tableRegionsBody.innerHTML = '';
    data.regional_sales.forEach(r => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${r.Region}</strong></td>
            <td class="text-right">${formatCurrency(r.Revenue)}</td>
            <td class="text-right">${r.Orders.toLocaleString()}</td>
            <td class="text-right"><span class="badge badge-active">${r['Revenue Share %']}%</span></td>
        `;
        tableRegionsBody.appendChild(row);
    });

    // 3. Monthly Trend table
    tableMonthlyBody.innerHTML = '';
    data.monthly_trends.forEach(m => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${m.Month}</strong></td>
            <td class="text-right">${formatCurrency(m.Revenue)}</td>
            <td class="text-right">${m.Orders.toLocaleString()}</td>
            <td class="text-right">${m.Quantity_Sold.toLocaleString()}</td>
        `;
        tableMonthlyBody.appendChild(row);
    });
}

// Destroy all charts
function destroyCharts() {
    if (productChart) productChart.destroy();
    if (regionChart) regionChart.destroy();
    if (monthlyChart) monthlyChart.destroy();
}

// Render dynamic animated charts using Chart.js
function renderCharts(data) {
    destroyCharts();

    // Chart.js styling variables
    const textFamily = "'Inter', sans-serif";
    const textCol = "#9ca3af";
    const borderCol = "rgba(255, 255, 255, 0.08)";
    
    const colors = [
        '#3b82f6', // blue
        '#8b5cf6', // purple
        '#06b6d4', // teal
        '#10b981', // green
        '#f59e0b', // amber
        '#ec4899', // pink
        '#f43f5e', // rose
        '#6b7280'  // gray
    ];

    // 1. Top Products Bar Chart (take top 5)
    const top5 = data.top_products.slice(0, 5);
    const ctxProd = document.getElementById('js-chart-products').getContext('2d');
    productChart = new Chart(ctxProd, {
        type: 'bar',
        data: {
            labels: top5.map(p => p.Product),
            datasets: [{
                label: 'Revenue ($)',
                data: top5.map(p => p.Revenue),
                backgroundColor: colors.slice(0, 5),
                borderRadius: 6,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Revenue: ${formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: textCol, font: { family: textFamily } }
                },
                y: {
                    grid: { color: borderCol },
                    ticks: {
                        color: textCol,
                        font: { family: textFamily },
                        callback: function(value) {
                            return '$' + (value / 1000) + 'k';
                        }
                    }
                }
            }
        }
    });

    // 2. Regional Sales Share Doughnut
    const ctxReg = document.getElementById('js-chart-regions').getContext('2d');
    regionChart = new Chart(ctxReg, {
        type: 'doughnut',
        data: {
            labels: data.regional_sales.map(r => r.Region),
            datasets: [{
                data: data.regional_sales.map(r => r.Revenue),
                backgroundColor: colors.slice(0, data.regional_sales.length),
                borderWidth: 1,
                borderColor: '#111827'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: textCol,
                        font: { family: textFamily, size: 11 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const sum = context.dataset.data.reduce((a, b) => a + b, 0);
                            const val = context.raw;
                            const pct = ((val / sum) * 100).toFixed(1);
                            return ` ${context.label}: ${formatCurrency(val)} (${pct}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });

    // 3. Monthly Trends Line Chart
    const ctxMonth = document.getElementById('js-chart-monthly').getContext('2d');
    
    // Create a beautiful blue gradient for line fill
    const gradient = ctxMonth.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.35)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0.00)');

    monthlyChart = new Chart(ctxMonth, {
        type: 'line',
        data: {
            labels: data.monthly_trends.map(m => m.Month),
            datasets: [{
                label: 'Monthly Revenue',
                data: data.monthly_trends.map(m => m.Revenue),
                borderColor: '#3b82f6',
                borderWidth: 3,
                pointBackgroundColor: '#60a5fa',
                pointBorderColor: '#111827',
                pointHoverRadius: 6,
                fill: true,
                backgroundColor: gradient,
                tension: 0.35
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Revenue: ${formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: borderCol },
                    ticks: { color: textCol, font: { family: textFamily } }
                },
                y: {
                    grid: { color: borderCol },
                    ticks: {
                        color: textCol,
                        font: { family: textFamily },
                        callback: function(value) {
                            return '$' + (value / 1000) + 'k';
                        }
                    }
                }
            }
        }
    });
}
