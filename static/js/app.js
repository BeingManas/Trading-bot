// ===== STATE =====
let currentSymbol = 'BTCUSDT';
let currentSide = 'BUY';
let currentType = 'MARKET';
let currentInterval = '1h';
let previousPrices = {};
let chart = null;
let candleSeries = null;
let volumeSeries = null;

const SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT'];
const SYMBOL_LABELS = { BTCUSDT: 'BTC/USDT', ETHUSDT: 'ETH/USDT', BNBUSDT: 'BNB/USDT', SOLUSDT: 'SOL/USDT', XRPUSDT: 'XRP/USDT' };
const INTERVALS = ['1m', '5m', '15m', '1h', '4h', '1d'];

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchAllTickers();
    loadChart(currentSymbol, currentInterval);
    fetchOrderBook();
    setInterval(fetchAllTickers, 5000);
    setInterval(fetchOrderBook, 3000);
    setInterval(() => loadChartUpdate(), 10000);
});

// ===== TICKER =====
async function fetchAllTickers() {
    for (const sym of SYMBOLS) {
        try {
            const res = await fetch(`/api/ticker/${sym}`);
            const data = await res.json();
            if (data.success) updateTickerItem(sym, data);
        } catch (e) { /* silent */ }
    }
}

function updateTickerItem(symbol, data) {
    const el = document.getElementById(`ticker-${symbol}`);
    if (!el) return;

    const price = parseFloat(data.lastPrice);
    const change = parseFloat(data.priceChangePercent);
    const vol = parseFloat(data.quoteVolume);
    const isUp = change >= 0;

    const priceEl = el.querySelector('.ticker-price');
    const changeEl = el.querySelector('.ticker-change');
    const volEl = el.querySelector('.ticker-vol');

    // Flash animation on price change
    const prev = previousPrices[symbol];
    if (prev && prev !== price) {
        priceEl.classList.remove('flash-up', 'flash-down');
        void priceEl.offsetWidth; // reflow
        priceEl.classList.add(price > prev ? 'flash-up' : 'flash-down');
    }
    previousPrices[symbol] = price;

    priceEl.textContent = formatPrice(price);
    priceEl.style.color = isUp ? 'var(--green)' : 'var(--red)';
    changeEl.textContent = `${isUp ? '+' : ''}${change.toFixed(2)}%`;
    changeEl.className = `ticker-change ${isUp ? 'up' : 'down'}`;
    if (volEl) volEl.textContent = `Vol ${formatVolume(vol)}`;

    // Update chart header if active symbol
    if (symbol === currentSymbol) {
        updateChartHeader(data);
    }
}

function updateChartHeader(data) {
    const price = parseFloat(data.lastPrice);
    const change = parseFloat(data.priceChangePercent);
    const isUp = change >= 0;

    const lp = document.getElementById('chart-live-price');
    const cp = document.getElementById('chart-price-change');
    const h = document.getElementById('stat-high');
    const l = document.getElementById('stat-low');
    const v = document.getElementById('stat-vol');

    if (lp) {
        lp.textContent = formatPrice(price);
        lp.style.color = isUp ? 'var(--green)' : 'var(--red)';
    }
    if (cp) {
        cp.textContent = `${isUp ? '+' : ''}${change.toFixed(2)}%`;
        cp.style.color = isUp ? 'var(--green)' : 'var(--red)';
        cp.style.background = isUp ? 'var(--green-dim)' : 'var(--red-dim)';
    }
    if (h) h.textContent = formatPrice(parseFloat(data.highPrice));
    if (l) l.textContent = formatPrice(parseFloat(data.lowPrice));
    if (v) v.textContent = formatVolume(parseFloat(data.quoteVolume));
}

// ===== CHART (Lightweight Charts) =====
function initChart() {
    const container = document.getElementById('chart-container');
    if (!container || typeof LightweightCharts === 'undefined') return;

    chart = LightweightCharts.createChart(container, {
        layout: {
            background: { type: 'solid', color: '#0a0e17' },
            textColor: '#8492a6',
            fontSize: 11,
        },
        grid: {
            vertLines: { color: 'rgba(30, 42, 58, 0.5)' },
            horzLines: { color: 'rgba(30, 42, 58, 0.5)' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
            vertLine: { color: 'rgba(240, 185, 11, 0.3)', width: 1, style: 2 },
            horzLine: { color: 'rgba(240, 185, 11, 0.3)', width: 1, style: 2 },
        },
        rightPriceScale: {
            borderColor: '#1e2a3a',
            scaleMargins: { top: 0.1, bottom: 0.2 },
        },
        timeScale: {
            borderColor: '#1e2a3a',
            timeVisible: true,
            secondsVisible: false,
        },
        handleScroll: { vertTouchDrag: false },
    });

    candleSeries = chart.addCandlestickSeries({
        upColor: '#0ecb81',
        downColor: '#f6465d',
        borderDownColor: '#f6465d',
        borderUpColor: '#0ecb81',
        wickDownColor: '#f6465d',
        wickUpColor: '#0ecb81',
    });

    volumeSeries = chart.addHistogramSeries({
        priceFormat: { type: 'volume' },
        priceScaleId: '',
    });
    volumeSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.85, bottom: 0 },
    });

    // Auto-resize
    const ro = new ResizeObserver(() => {
        chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    });
    ro.observe(container);
}

async function loadChart(symbol, interval) {
    if (!candleSeries) return;
    try {
        const res = await fetch(`/api/klines/${symbol}?interval=${interval}&limit=200`);
        const data = await res.json();
        if (data.success && data.klines.length) {
            candleSeries.setData(data.klines);
            volumeSeries.setData(data.klines.map(k => ({
                time: k.time,
                value: k.volume,
                color: k.close >= k.open ? 'rgba(14, 203, 129, 0.3)' : 'rgba(246, 70, 93, 0.3)',
            })));
            chart.timeScale().fitContent();
        }
    } catch (e) { console.error('Chart load error:', e); }
}

async function loadChartUpdate() {
    if (!candleSeries) return;
    try {
        const res = await fetch(`/api/klines/${currentSymbol}?interval=${currentInterval}&limit=2`);
        const data = await res.json();
        if (data.success && data.klines.length) {
            const last = data.klines[data.klines.length - 1];
            candleSeries.update(last);
            volumeSeries.update({
                time: last.time,
                value: last.volume,
                color: last.close >= last.open ? 'rgba(14, 203, 129, 0.3)' : 'rgba(246, 70, 93, 0.3)',
            });
        }
    } catch (e) { /* silent */ }
}

// ===== ORDER BOOK =====
async function fetchOrderBook() {
    try {
        const res = await fetch(`/api/depth/${currentSymbol}`);
        const data = await res.json();
        if (data.success) renderOrderBook(data.bids, data.asks);
    } catch (e) { /* silent */ }
}

function renderOrderBook(bids, asks) {
    const asksContainer = document.getElementById('ob-asks');
    const bidsContainer = document.getElementById('ob-bids');
    const spreadEl = document.getElementById('ob-spread');
    if (!asksContainer || !bidsContainer) return;

    // Calculate max total for depth bars
    const allSizes = [...asks, ...bids].map(o => parseFloat(o[1]));
    const maxSize = Math.max(...allSizes, 0.001);

    // Asks (reversed - lowest at bottom)
    const sortedAsks = asks.slice(0, 8).reverse();
    asksContainer.innerHTML = sortedAsks.map(a => {
        const pct = (parseFloat(a[1]) / maxSize * 100).toFixed(0);
        return `<div class="ob-row">
            <div class="depth-bar ask-bar" style="width:${pct}%"></div>
            <span class="price ask">${formatPrice(parseFloat(a[0]))}</span>
            <span class="size">${parseFloat(a[1]).toFixed(4)}</span>
            <span class="total">${(parseFloat(a[0]) * parseFloat(a[1])).toFixed(2)}</span>
        </div>`;
    }).join('');

    // Bids
    bidsContainer.innerHTML = bids.slice(0, 8).map(b => {
        const pct = (parseFloat(b[1]) / maxSize * 100).toFixed(0);
        return `<div class="ob-row">
            <div class="depth-bar bid-bar" style="width:${pct}%"></div>
            <span class="price bid">${formatPrice(parseFloat(b[0]))}</span>
            <span class="size">${parseFloat(b[1]).toFixed(4)}</span>
            <span class="total">${(parseFloat(b[0]) * parseFloat(b[1])).toFixed(2)}</span>
        </div>`;
    }).join('');

    // Spread
    if (asks.length && bids.length) {
        const spread = parseFloat(asks[0][0]) - parseFloat(bids[0][0]);
        spreadEl.textContent = `Spread: ${formatPrice(spread)}`;
    }
}

// ===== SYMBOL SELECTION =====
function selectSymbol(symbol) {
    currentSymbol = symbol;
    document.querySelectorAll('.ticker-item').forEach(el => el.classList.remove('active'));
    const el = document.getElementById(`ticker-${symbol}`);
    if (el) el.classList.add('active');

    document.getElementById('chart-symbol-name').textContent = SYMBOL_LABELS[symbol] || symbol;
    document.getElementById('symbol-select').value = symbol;

    loadChart(symbol, currentInterval);
    fetchOrderBook();
}

function setInterval_(interval) {
    currentInterval = interval;
    document.querySelectorAll('.interval-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    loadChart(currentSymbol, interval);
}

// ===== ORDER FORM =====
function setSide(side) {
    currentSide = side;
    document.querySelectorAll('.side-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`.side-btn.${side.toLowerCase()}`).classList.add('active');
    const btn = document.getElementById('submitBtn');
    btn.className = `submit-btn ${side.toLowerCase()}`;
    btn.textContent = side === 'BUY' ? 'BUY / LONG' : 'SELL / SHORT';
}

function setType(type) {
    currentType = type;
    document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('priceGroup').style.display = type === 'LIMIT' ? 'block' : 'none';
}

function setQtyPercent(pct) {
    // Simple helper - sets quantity based on percentage
    const baseQty = { BTCUSDT: 0.01, ETHUSDT: 0.1, BNBUSDT: 1, SOLUSDT: 1, XRPUSDT: 100 };
    const base = baseQty[currentSymbol] || 0.01;
    document.getElementById('quantity').value = (base * pct / 100).toFixed(4);
}

// Submit order
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('orderForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('submitBtn');
        const origText = btn.textContent;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>Placing...';

        const body = {
            symbol: document.getElementById('symbol-select').value,
            side: currentSide,
            type: currentType,
            quantity: document.getElementById('quantity').value,
        };

        if (currentType === 'LIMIT') {
            const price = document.getElementById('price').value;
            if (!price) {
                showToast('Price required for LIMIT orders', 'error');
                btn.disabled = false;
                btn.textContent = origText;
                return;
            }
            body.price = price;
        }

        if (!body.quantity || parseFloat(body.quantity) <= 0) {
            showToast('Enter a valid quantity', 'error');
            btn.disabled = false;
            btn.textContent = origText;
            return;
        }

        try {
            const res = await fetch('/api/place-order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Order filled! ID: ${data.data.orderId}`, 'success');
                addToHistory(data.data);
            } else {
                showToast(data.error, 'error');
            }
        } catch (err) {
            showToast('Connection failed', 'error');
        }

        btn.disabled = false;
        btn.textContent = origText;
    });
});

// ===== ORDER HISTORY =====
function addToHistory(order) {
    const tbody = document.getElementById('historyBody');
    const empty = document.getElementById('emptyState');
    const table = document.getElementById('historyTable');
    const countEl = document.getElementById('orderCount');

    if (empty) empty.style.display = 'none';
    if (table) table.style.display = 'table';

    const row = document.createElement('tr');
    row.style.animation = 'toastIn 0.3s ease';
    const sideClass = order.side?.toLowerCase() || '';
    const statusClass = order.status?.toLowerCase() || '';

    row.innerHTML = `
        <td style="font-family:monospace;font-size:11px;color:var(--text-muted)">${order.orderId}</td>
        <td><strong>${order.symbol}</strong></td>
        <td><span class="side-label ${sideClass}">${order.side}</span></td>
        <td>${order.type}</td>
        <td>${order.quantity || order.origQty}</td>
        <td>${formatPrice(parseFloat(order.avgPrice || order.price || 0))}</td>
        <td><span class="status-badge ${statusClass}">${order.status}</span></td>
    `;
    tbody.insertBefore(row, tbody.firstChild);

    const count = tbody.querySelectorAll('tr').length;
    if (countEl) countEl.textContent = count;
}

// ===== TOAST =====
function showToast(message, type) {
    const container = document.getElementById('toasts');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? '✓' : '✕';
    toast.innerHTML = `<span class="toast-icon">${icon}</span>${message}`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ===== HELPERS =====
function formatPrice(p) {
    if (p >= 1000) return p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (p >= 1) return p.toFixed(2);
    return p.toFixed(4);
}

function formatVolume(v) {
    if (v >= 1e9) return (v / 1e9).toFixed(2) + 'B';
    if (v >= 1e6) return (v / 1e6).toFixed(2) + 'M';
    if (v >= 1e3) return (v / 1e3).toFixed(1) + 'K';
    return v.toFixed(0);
}

// ===== PANEL TABS =====
function showPanel(panel) {
    document.querySelectorAll('.panel-tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('order-form-panel').style.display = panel === 'trade' ? 'block' : 'none';
    document.getElementById('order-book-panel').style.display = panel === 'book' ? 'block' : 'none';
}
