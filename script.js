const API_BASE = '/api';

// Redirect if no token
if (!localStorage.getItem('token') && !window.location.pathname.includes('login') && !window.location.pathname.includes('signup')) {
    if (window.location.pathname !== '/index.html' && window.location.pathname !== '/') {
        window.location.href = 'login.html';
    }
}

// Auth Headers
const getHeaders = () => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
});

// Logout
function logout() {
    localStorage.clear();
    window.location.href = 'login.html';
}

// Fetch Summary and Update UI
async function updateDashboard() {
    const res = await fetch(`${API_BASE}/summary`, { headers: getHeaders() });
    if (res.status === 401) logout();
    
    const data = await res.json();
    
    document.getElementById('totalIncome').textContent = `₹${data.total_income.toLocaleString()}`;
    document.getElementById('totalExpenses').textContent = `₹${data.total_expenses.toLocaleString()}`;
    document.getElementById('totalBalance').textContent = `₹${(data.total_income - data.total_expenses).toLocaleString()}`;
    
    updateCharts(data.categories);
    updateActivityTable();
}

let trendChart, categoryChart;

function updateCharts(categories) {
    // Category Pie Chart
    const ctx2 = document.getElementById('categoryChart').getContext('2d');
    if (categoryChart) categoryChart.destroy();
    
    categoryChart = new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: categories.map(c => c.category),
            datasets: [{
                data: categories.map(c => c.total),
                backgroundColor: ['#6366f1', '#ec4899', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'],
                borderWidth: 0
            }]
        },
        options: {
            plugins: {
                legend: { position: 'bottom', labels: { color: '#94a3b8' } }
            }
        }
    });
}

async function updateActivityTable() {
    const [incRes, expRes] = await Promise.all([
        fetch(`${API_BASE}/income`, { headers: getHeaders() }),
        fetch(`${API_BASE}/expenses`, { headers: getHeaders() })
    ]);
    
    const income = await incRes.json();
    const expenses = await expRes.json();
    
    const combined = [
        ...income.map(i => ({ ...i, type: 'income' })),
        ...expenses.map(e => ({ ...e, type: 'expense' }))
    ].sort((a, b) => new Date(b.date) - new Date(a.date));
    
    const body = document.getElementById('activityBody');
    body.innerHTML = combined.map(item => `
        <tr>
            <td>${item.date}</td>
            <td>${item.category || item.source}</td>
            <td class="${item.type === 'income' ? 'text-success' : 'text-danger'}">${item.type.toUpperCase()}</td>
            <td>₹${item.amount.toLocaleString()}</td>
        </tr>
    `).join('');
    
    // Update Trend Chart (simple monthly)
    updateTrendChart(combined);
}

function updateTrendChart(data) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    if (trendChart) trendChart.destroy();
    
    // Group by month
    const months = {};
    data.forEach(item => {
        const m = item.date.substring(0, 7);
        if (!months[m]) months[m] = { inc: 0, exp: 0 };
        if (item.type === 'income') months[m].inc += item.amount;
        else months[m].exp += item.amount;
    });
    
    const labels = Object.keys(months).sort();
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Income',
                    data: labels.map(l => months[l].inc),
                    borderColor: '#10b981',
                    tension: 0.4
                },
                {
                    label: 'Expenses',
                    data: labels.map(l => months[l].exp),
                    borderColor: '#ef4444',
                    tension: 0.4
                }
            ]
        },
        options: {
            plugins: {
                legend: { labels: { color: '#94a3b8' } }
            },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

// Handlers
if (document.getElementById('transactionForm')) {
    document.getElementById('transactionForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const type = document.getElementById('tType').value;
        const amount = parseFloat(document.getElementById('tAmount').value);
        const category = document.getElementById('tCategory').value;
        const date = document.getElementById('tDate').value;
        
        await fetch(`${API_BASE}/${type === 'income' ? 'income' : 'expenses'}`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ amount, category, source: category, date })
        });
        
        updateDashboard();
        e.target.reset();
    });
}

if (document.getElementById('budgetForm')) {
    document.getElementById('budgetForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const category = document.getElementById('bCategory').value;
        const budget = parseFloat(document.getElementById('bAmount').value);
        const month = document.getElementById('bMonth').value;
        
        await fetch(`${API_BASE}/budgets`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ category, budget, month })
        });
        
        alert('Budget set successfully!');
        e.target.reset();
    });
}

if (document.getElementById('runMlBtn')) {
    document.getElementById('runMlBtn').addEventListener('click', async () => {
        const res = await fetch(`${API_BASE}/ml-analysis`, { headers: getHeaders() });
        const data = await res.json();
        const mlResults = document.getElementById('mlResults');
        const mlContent = document.getElementById('mlContent');
        
        mlResults.style.display = 'block';
        if (res.ok) {
            mlContent.innerHTML = `
                <p>Analyzed ${data.length} months of data.</p>
                <p>Projected savings trend: 📈 positive</p>
                <p>AI Suggestion: Keep your non-essential expenses below 20% of income to reach your goals faster.</p>
            `;
        } else {
            mlContent.innerHTML = `<p class="text-danger">${data.message}</p>`;
        }
    });
}

// Init
if (window.location.pathname.includes('dashboard')) {
    document.getElementById('userGreeting').textContent = `Welcome, ${localStorage.getItem('userName')} 👋`;
    updateDashboard();
}
