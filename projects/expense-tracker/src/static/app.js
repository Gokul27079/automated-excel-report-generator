// SpendWise Front-end Logic (INR Version with Exchange Rates)

// State management
let expenses = [];
let summary = {};
let monthlyBudget = 40000; // Default budget in INR
let filteredExpenses = [];
let currentPage = 1;
const rowsPerPage = 10;

// Currency Rates State
let exchangeRates = {
    "INR": 1.0,
    "USD": 0.012,
    "EUR": 0.011,
    "GBP": 0.0095,
    "AED": 0.044,
    "SGD": 0.016,
    "JPY": 1.88,
    "CAD": 0.016
}; // Realistic fallback baseline rates

// Chart references
let categoryChartInstance = null;
let trendChartInstance = null;

// DOM Elements
const expenseForm = document.getElementById('expense-form');
const expenseIdInput = document.getElementById('expense-id');
const amountInput = document.getElementById('amount');
const dateInput = document.getElementById('date');
const categorySelect = document.getElementById('category');
const descriptionInput = document.getElementById('description');
const formTitle = document.getElementById('form-title');
const saveBtn = document.getElementById('save-btn');
const cancelBtn = document.getElementById('cancel-btn');

const budgetInput = document.getElementById('budget-input');
const budgetProgressBar = document.getElementById('budget-progress-bar');
const budgetPercentText = document.getElementById('budget-percent');
const budgetSpentText = document.getElementById('budget-spent');
const budgetRemainingText = document.getElementById('budget-remaining');

const kpiTotal = document.getElementById('kpi-total');
const kpiDailyAvg = document.getElementById('kpi-daily-avg');
const kpiHighestCat = document.getElementById('kpi-highest-cat');
const kpiCount = document.getElementById('kpi-count');

const searchInput = document.getElementById('search-input');
const filterCategory = document.getElementById('filter-category');
const expensesTableBody = document.querySelector('#expenses-table tbody');
const pageIndicator = document.getElementById('page-indicator');
const prevPageBtn = document.getElementById('prev-page-btn');
const nextPageBtn = document.getElementById('next-page-btn');

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const resetMockBtn = document.getElementById('reset-mock-btn');

// Currency Converter Elements
const convAmountInput = document.getElementById('conv-amount');
const convFromSelect = document.getElementById('conv-from');
const convToSelect = document.getElementById('conv-to');
const convResultDiv = document.getElementById('conv-result');
const ratesGridDiv = document.getElementById('rates-grid');
const refreshRatesBtn = document.getElementById('refresh-rates-btn');

// Page Startup
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Date input to today's date
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;

    // 2. Load settings from cache (Budget)
    const cachedBudget = localStorage.getItem('spendwise_budget');
    if (cachedBudget) {
        monthlyBudget = parseFloat(cachedBudget);
        budgetInput.value = monthlyBudget;
    }

    // 3. Load database data from cache first for instant load
    const cachedExpenses = localStorage.getItem('spendwise_expenses');
    const cachedSummary = localStorage.getItem('spendwise_summary');
    if (cachedExpenses && cachedSummary) {
        expenses = JSON.parse(cachedExpenses);
        summary = JSON.parse(cachedSummary);
        logger("Loaded cached expense data");
        updateUI();
    }

    // 4. Load cached exchange rates
    const cachedRates = localStorage.getItem('spendwise_rates');
    if (cachedRates) {
        exchangeRates = JSON.parse(cachedRates);
        logger("Loaded cached exchange rates");
    }

    // 5. Fetch live data & exchange rates
    fetchExpenses();
    fetchExchangeRates();

    // 6. Form submissions
    expenseForm.addEventListener('submit', handleFormSubmit);
    cancelBtn.addEventListener('click', resetForm);

    // 7. Budget input change
    budgetInput.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        if (val && val > 0) {
            monthlyBudget = val;
            localStorage.setItem('spendwise_budget', monthlyBudget);
            updateBudgetProgress();
        }
    });

    // 8. Table filters, searches, pagination
    searchInput.addEventListener('input', applyFilters);
    filterCategory.addEventListener('change', applyFilters);
    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderTable();
        }
    });
    nextPageBtn.addEventListener('click', () => {
        const maxPage = Math.ceil(filteredExpenses.length / rowsPerPage);
        if (currentPage < maxPage) {
            currentPage++;
            renderTable();
        }
    });

    // 9. Seeding Mock Data
    resetMockBtn.addEventListener('click', triggerMockSeeding);

    // 10. Bulk CSV Upload
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadCSVFile(e.target.files[0]);
        }
    });

    // Drag-Drop
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
            uploadCSVFile(files[0]);
        } else {
            alert("Please drop a valid CSV file.");
        }
    });

    // 11. Currency Converter Change Listeners
    convAmountInput.addEventListener('input', calculateConversion);
    convFromSelect.addEventListener('change', calculateConversion);
    convToSelect.addEventListener('change', calculateConversion);
    refreshRatesBtn.addEventListener('click', () => {
        fetchExchangeRates(true);
    });
});

function logger(msg) {
    console.log(`[SpendWise] ${msg}`);
}

// Fetch Expenses and Summary from API
async function fetchExpenses() {
    try {
        const resExpenses = await fetch('/api/expenses');
        const resSummary = await fetch('/api/expenses/summary');
        
        if (resExpenses.ok && resSummary.ok) {
            expenses = await resExpenses.json();
            summary = await resSummary.json();
            
            // Cache state
            localStorage.setItem('spendwise_expenses', JSON.stringify(expenses));
            localStorage.setItem('spendwise_summary', JSON.stringify(summary));
            
            logger("Successfully fetched latest ledger data from API");
            updateUI();
        }
    } catch (err) {
        console.error("Failed to load live data from API server", err);
    }
}

// Fetch exchange rates from free open api relative to INR
async function fetchExchangeRates(isManual = false) {
    if (isManual) {
        refreshRatesBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Refreshing...';
    }
    
    try {
        // Free open access API for rates
        const response = await fetch('https://open.er-api.com/v6/latest/INR');
        if (response.ok) {
            const data = await response.json();
            if (data && data.rates) {
                // Filter currencies we care about
                const targetCurrencies = ["INR", "USD", "EUR", "GBP", "AED", "SGD", "JPY", "CAD"];
                targetCurrencies.forEach(curr => {
                    if (data.rates[curr]) {
                        exchangeRates[curr] = data.rates[curr];
                    }
                });
                
                // Cache exchange rates
                localStorage.setItem('spendwise_rates', JSON.stringify(exchangeRates));
                logger("Successfully updated exchange rates from open api");
            }
        }
    } catch (err) {
        console.error("Exchange rate fetch failed, relying on cache/fallback baseline", err);
    } finally {
        if (isManual) {
            refreshRatesBtn.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Refresh Rates';
        }
        calculateConversion();
        renderRatesGrid();
    }
}

// Perform conversion rate comparison
function calculateConversion() {
    const amount = parseFloat(convAmountInput.value);
    if (isNaN(amount) || amount <= 0) {
        convResultDiv.textContent = "Enter valid amount";
        return;
    }
    
    const fromCurr = convFromSelect.value;
    const toCurr = convToSelect.value;
    
    // Convert to base INR first, then convert to target
    // rate = target / base => rate relative to INR
    const rateFrom = exchangeRates[fromCurr];
    const rateTo = exchangeRates[toCurr];
    
    // Amount in INR = amount / rateFrom
    const amountInINR = amount / rateFrom;
    const convertedAmount = amountInINR * rateTo;
    
    convResultDiv.textContent = formatCurrencySpecific(convertedAmount, toCurr);
}

// Render Comparison Matrix rates
function renderRatesGrid() {
    ratesGridDiv.innerHTML = '';
    
    const displayCurrencies = [
        { code: "USD", name: "US Dollar", symbol: "$" },
        { code: "EUR", name: "Euro", symbol: "€" },
        { code: "GBP", name: "Pound", symbol: "£" },
        { code: "AED", name: "Dirham", symbol: "Dh" },
        { code: "SGD", name: "Singapore Dollar", symbol: "S$" },
        { code: "JPY", name: "Yen", symbol: "¥" },
        { code: "CAD", name: "Canadian Dollar", symbol: "C$" }
    ];
    
    displayCurrencies.forEach(curr => {
        // Rate from INR: exchangeRates[curr.code] / exchangeRates["INR"]
        const rate = exchangeRates[curr.code];
        const val = 100 * rate;
        
        const card = document.createElement('div');
        card.className = 'rate-pill';
        card.innerHTML = `
            <span class="rate-code">${curr.code} (${curr.symbol})</span>
            <span class="rate-val">${formatCurrencySpecific(val, curr.code)}</span>
        `;
        ratesGridDiv.appendChild(card);
    });
}

// Update UI components
function updateUI() {
    // 1. KPI cards in INR
    kpiTotal.textContent = formatCurrency(summary.total || 0);
    kpiDailyAvg.textContent = formatCurrency(summary.daily_avg || 0);
    kpiHighestCat.textContent = summary.highest_category || '-';
    kpiCount.textContent = summary.count || 0;

    // 2. Budget progress
    updateBudgetProgress();

    // 3. Populate Table filter
    applyFilters();

    // 4. Render charts
    renderCharts();
}

// Render dynamic charts in INR
function renderCharts() {
    if (categoryChartInstance) categoryChartInstance.destroy();
    if (trendChartInstance) trendChartInstance.destroy();

    const chartTextFamily = "'Inter', sans-serif";
    const chartTextCol = "#94a3b8";
    const gridBorderCol = "rgba(255, 255, 255, 0.05)";

    const colors = [
        '#10b981', // green
        '#0ea5e9', // blue
        '#f59e0b', // amber
        '#8b5cf6', // purple
        '#ef4444', // red
        '#ec4899', // pink
        '#14b8a6', // teal
        '#64748b'  // gray
    ];

    // Doughnut category chart
    const catLabels = (summary.breakdown || []).map(b => b.category);
    const catData = (summary.breakdown || []).map(b => b.total_spent);
    
    const ctxCat = document.getElementById('chart-category').getContext('2d');
    categoryChartInstance = new Chart(ctxCat, {
        type: 'doughnut',
        data: {
            labels: catLabels,
            datasets: [{
                data: catData,
                backgroundColor: colors.slice(0, catLabels.length),
                borderWidth: 1,
                borderColor: '#0f172a'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: chartTextCol, font: { family: chartTextFamily, size: 10 } }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const val = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((val / total) * 100).toFixed(1);
                            return ` ${context.label}: ${formatCurrency(val)} (${pct}%)`;
                        }
                    }
                }
            },
            cutout: '65%'
        }
    });

    // Daily Line chart (Sort chronological first)
    const trendData = summary.trends || [];
    const ctxTrend = document.getElementById('chart-trend').getContext('2d');
    
    const blueGradient = ctxTrend.createLinearGradient(0, 0, 0, 200);
    blueGradient.addColorStop(0, 'rgba(14, 165, 233, 0.3)');
    blueGradient.addColorStop(1, 'rgba(14, 165, 233, 0.0)');

    trendChartInstance = new Chart(ctxTrend, {
        type: 'line',
        data: {
            labels: trendData.map(t => t.date_str),
            datasets: [{
                label: 'Spent (₹)',
                data: trendData.map(t => t.amount),
                borderColor: '#0ea5e9',
                borderWidth: 2,
                pointBackgroundColor: '#38bdf8',
                pointBorderColor: '#060913',
                fill: true,
                backgroundColor: blueGradient,
                tension: 0.3
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
                            return `Amount: ${formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: chartTextCol, font: { family: chartTextFamily, size: 9 } }
                },
                y: {
                    grid: { color: gridBorderCol },
                    ticks: {
                        color: chartTextCol,
                        font: { family: chartTextFamily, size: 9 },
                        callback: function(value) {
                            return '₹' + value;
                        }
                    }
                }
            }
        }
    });
}

// Calculate and show budget status progress bar (INR)
function updateBudgetProgress() {
    const totalSpent = summary.total || 0;
    const remaining = Math.max(0, monthlyBudget - totalSpent);
    const percent = Math.min(100, (totalSpent / monthlyBudget) * 100);
    
    budgetPercentText.textContent = `${percent.toFixed(1)}% Spent`;
    budgetSpentText.textContent = formatCurrency(totalSpent);
    budgetRemainingText.textContent = formatCurrency(remaining);
    
    budgetProgressBar.style.width = `${percent}%`;
    
    // Progress bar alerts based on thresholds
    budgetProgressBar.className = "progress-bar";
    if (percent >= 95) {
        budgetProgressBar.classList.add('danger');
    } else if (percent >= 75) {
        budgetProgressBar.classList.add('warning');
    }
}

// Search and Filter expenses
function applyFilters() {
    const searchVal = searchInput.value.toLowerCase().trim();
    const catVal = filterCategory.value;
    
    filteredExpenses = expenses.filter(e => {
        const matchesSearch = (e.description || '').toLowerCase().includes(searchVal) || e.category.toLowerCase().includes(searchVal);
        const matchesCategory = catVal === 'all' || e.category === catVal;
        return matchesSearch && matchesCategory;
    });
    
    currentPage = 1;
    renderTable();
}

// Render paginated expenses table
function renderTable() {
    expensesTableBody.innerHTML = '';
    
    if (filteredExpenses.length === 0) {
        expensesTableBody.innerHTML = `<tr><td colspan="5" class="text-center" style="color: var(--text-muted);">No transactions found.</td></tr>`;
        pageIndicator.textContent = "Showing 0 of 0";
        prevPageBtn.disabled = true;
        nextPageBtn.disabled = true;
        return;
    }
    
    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = Math.min(startIndex + rowsPerPage, filteredExpenses.length);
    const pageSlice = filteredExpenses.slice(startIndex, endIndex);
    
    pageSlice.forEach(e => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${e.date}</strong></td>
            <td><span class="kpi-label">${e.category}</span></td>
            <td>${e.description || '<span style="color: var(--text-muted); font-style: italic;">No description</span>'}</td>
            <td class="text-right" style="color: white; font-weight: 500;">${formatCurrency(e.amount)}</td>
            <td class="text-center">
                <div class="table-actions">
                    <button class="action-btn action-btn-edit" onclick="triggerEditExpense(${e.id})" title="Edit expense">
                        <i class="fa-solid fa-pen-to-square"></i>
                    </button>
                    <button class="action-btn action-btn-delete" onclick="triggerDeleteExpense(${e.id})" title="Delete expense">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            </td>
        `;
        expensesTableBody.appendChild(tr);
    });
    
    pageIndicator.textContent = `Showing ${startIndex + 1}-${endIndex} of ${filteredExpenses.length}`;
    
    prevPageBtn.disabled = currentPage === 1;
    nextPageBtn.disabled = endIndex === filteredExpenses.length;
}

// Handle Add/Edit Form submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const id = expenseIdInput.value;
    const payload = {
        amount: parseFloat(amountInput.value),
        date: dateInput.value,
        category: categorySelect.value,
        description: descriptionInput.value
    };
    
    try {
        let response;
        if (id) {
            // Update mode
            response = await fetch(`/api/expenses/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            // Create mode
            response = await fetch('/api/expenses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }
        
        if (response.ok) {
            resetForm();
            fetchExpenses();
        } else {
            const err = await response.json();
            alert(`Error: ${err.detail}`);
        }
    } catch (err) {
        console.error("Form submit failed", err);
    }
}

// Populate fields for editing
window.triggerEditExpense = function(id) {
    const expense = expenses.find(e => e.id === id);
    if (!expense) return;
    
    expenseIdInput.value = expense.id;
    amountInput.value = expense.amount;
    dateInput.value = expense.date;
    categorySelect.value = expense.category;
    descriptionInput.value = expense.description || '';
    
    formTitle.innerHTML = `<i class="fa-solid fa-pen-to-square"></i> Edit Expense #${id}`;
    saveBtn.innerHTML = `<i class="fa-solid fa-save"></i> Save Changes`;
    cancelBtn.classList.remove('hidden');
    
    expenseForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
};

// Reset form to Add state
function resetForm() {
    expenseIdInput.value = '';
    expenseForm.reset();
    
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;
    
    formTitle.innerHTML = `<i class="fa-solid fa-plus-minus"></i> Add New Expense`;
    saveBtn.innerHTML = `<i class="fa-solid fa-save"></i> Save Transaction`;
    cancelBtn.classList.add('hidden');
}

// Delete confirmation
window.triggerDeleteExpense = async function(id) {
    if (confirm("Are you sure you want to delete this expense record?")) {
        try {
            const response = await fetch(`/api/expenses/${id}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                fetchExpenses();
            } else {
                alert("Failed to delete expense.");
            }
        } catch (err) {
            console.error("Delete call failed", err);
        }
    }
};

// Upload CSV file
async function uploadCSVFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/expenses/upload-csv', {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            const result = await response.json();
            alert(result.message);
            fetchExpenses();
        } else {
            const err = await response.json();
            alert(`CSV Import failed: ${err.detail}`);
        }
    } catch (err) {
        console.error("CSV upload request failed", err);
    }
}

// Seeding realistic expenses database
async function triggerMockSeeding() {
    if (confirm("This will clear your current entries and seed 30 realistic expense records in Indian Rupees (INR). Proceed?")) {
        try {
            const response = await fetch('/api/expenses/reset-mock', {
                method: 'POST'
            });
            if (response.ok) {
                fetchExpenses();
            }
        } catch (err) {
            console.error("Mock seeding failed", err);
        }
    }
}

// Format number to INR currency (Lakhs/Crores grouping)
function formatCurrency(val) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(val);
}

// Format specific target currencies for the converter results
function formatCurrencySpecific(val, currencyCode) {
    const localesMap = {
        "INR": "en-IN",
        "USD": "en-US",
        "EUR": "de-DE",
        "GBP": "en-GB",
        "AED": "ar-AE",
        "SGD": "en-SG",
        "JPY": "ja-JP",
        "CAD": "en-CA"
    };
    
    const locale = localesMap[currencyCode] || "en-US";
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currencyCode,
        minimumFractionDigits: currencyCode === "JPY" ? 0 : 2,
        maximumFractionDigits: currencyCode === "JPY" ? 0 : 2
    }).format(val);
}
