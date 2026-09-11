"use strict";

/* =========================================================
   MARKET TOOLS - SMC OB + MACD
   FRONTEND
========================================================= */

const DATA_FILES = {
    ob: "results.json",
    macd: "macd_results.json",
    status: "scan_status.json",
    history: "history.json",
    sector: "sector_map.json"
};

let APP_DATA = {
    ob: null,
    macd: null,
    status: null,
    history: null,
    sector: { map: {} }
};

let historyFilter = "ALL";

/* =========================================================
   DOM
========================================================= */

function $(id) {
    return document.getElementById(id);
}

/* =========================================================
   FETCH JSON
========================================================= */

async function getJSON(file) {

    const url = `${file}?t=${Date.now()}`;

    const response = await fetch(url, {
        cache: "no-store",
        headers: {
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
    });

    if (!response.ok) {
        throw new Error(`${file}: HTTP ${response.status}`);
    }

    return await response.json();
}

/* =========================================================
   LOAD ALL DATA
========================================================= */

async function loadData() {

    setText("dashboardStatus", "Memuat data...");

    const results = await Promise.allSettled([
        getJSON(DATA_FILES.ob),
        getJSON(DATA_FILES.macd),
        getJSON(DATA_FILES.status),
        getJSON(DATA_FILES.history),
        getJSON(DATA_FILES.sector)
    ]);

    APP_DATA.ob =
        results[0].status === "fulfilled"
            ? results[0].value
            : null;

    APP_DATA.macd =
        results[1].status === "fulfilled"
            ? results[1].value
            : null;

    APP_DATA.status =
        results[2].status === "fulfilled"
            ? results[2].value
            : null;

    APP_DATA.history =
        results[3].status === "fulfilled"
            ? results[3].value
            : null;

    APP_DATA.sector =
        results[4].status === "fulfilled"
            ? results[4].value
            : { map: {} };

    renderAll();
}

/* =========================================================
   RENDER ALL
========================================================= */

function renderAll() {

    renderDashboard();
    renderOBPage();
    renderMACDPage();
    renderStatus();
    renderHistory();

    const statusText = getStatusText();

    setText("dashboardStatus", statusText);
    setHeaderStatus(statusText);
}

/* =========================================================
   HEADER STATUS PILL
========================================================= */

function setHeaderStatus(statusText) {

    const text = $("headerStatusText");
    const dot = $("headerStatusDot");

    if (text) {
        text.textContent = statusText || "-";
    }

    if (dot) {

        const normalized =
            String(statusText || "").toUpperCase();

        dot.style.background =
            normalized === "SUCCESS" || normalized === "READY"
                ? "var(--up)"
                : normalized === "FAILURE" || normalized === "ERROR"
                    ? "var(--down)"
                    : "var(--amber)";
    }
}

/* =========================================================
   DASHBOARD
========================================================= */

function renderDashboard() {

    const ob = APP_DATA.ob || {};
    const macd = APP_DATA.macd || {};

    const obData = getCandidateArray(ob);
    const macdData = getCandidateArray(macd);

    setText(
        "dashboardObCount",
        obData.length
    );

    setText(
        "dashboardMacdCount",
        macdData.length
    );

    setText(
        "dashboardObTime",
        getDuration(ob)
    );

    setText(
        "dashboardMacdTime",
        getDuration(macd)
    );

    renderCandidateList(
        "dashboardObList",
        obData
    );

    renderCandidateList(
        "dashboardMacdList",
        macdData
    );

    const slot =
        getValue(APP_DATA.status, [
            "slot",
            "current_slot",
            "schedule_slot"
        ]) ||
        getValue(ob, [
            "slot"
        ]) ||
        "-";

    const finished =
        getValue(APP_DATA.status, [
            "finished_at",
            "completed_at"
        ]) ||
        getValue(ob, [
            "finished_at",
            "generated_at"
        ]) ||
        "-";

    setText("dashboardSlot", slot);
    setText("dashboardFinished", formatDateTime(finished));
}

/* =========================================================
   CANDIDATE LIST
========================================================= */

function renderCandidateList(id, data) {

    const el = $(id);

    if (!el) return;

    if (!Array.isArray(data) || data.length === 0) {
        el.innerHTML = `<div class="empty">Tidak ada kandidat</div>`;
        return;
    }

    el.innerHTML = data.map(item => {

        const ticker = getTicker(item);
        const sector = getSector(ticker);

        return `
            <div class="candidate-row">
                <div class="candidate-main">
                    <strong>${escapeHTML(ticker)}</strong>
                    <span>${escapeHTML(shortSector(sector))}</span>
                </div>
            </div>
        `;

    }).join("");
}

/* =========================================================
   SMC OB PAGE
========================================================= */

function renderOBPage() {

    const data = APP_DATA.ob || {};
    const candidates = getCandidateArray(data);

    setText(
        "obCandidateCount",
        candidates.length
    );

    setText(
        "obTotalTickers",
        getValue(data, [
            "total_tickers",
            "total"
        ]) || "-"
    );

    setText(
        "obDuration",
        getDuration(data)
    );

    setText(
        "obErrors",
        getValue(data, [
            "errors",
            "error_count"
        ]) ?? "-"
    );

    setText(
        "obLastScan",
        formatDateTime(
            getValue(data, [
                "finished_at",
                "generated_at"
            ])
        )
    );

    setText(
        "obGeneratedAt",
        formatDateTime(
            getValue(data, [
                "generated_at",
                "finished_at"
            ])
        )
    );

    const progress =
        getProgress(data);

    setProgress(
        "obProgressFill",
        "obProgress",
        progress
    );

    renderResultTable(
        "obResultBody",
        candidates,
        "SMC OB"
    );
}

/* =========================================================
   MACD PAGE
========================================================= */

function renderMACDPage() {

    const data = APP_DATA.macd || {};
    const candidates = getCandidateArray(data);

    setText(
        "macdCandidateCount",
        candidates.length
    );

    setText(
        "macdTotalTickers",
        getValue(data, [
            "total_tickers",
            "total"
        ]) || "-"
    );

    setText(
        "macdDuration",
        getDuration(data)
    );

    setText(
        "macdErrors",
        getValue(data, [
            "errors",
            "error_count"
        ]) ?? "-"
    );

    setText(
        "macdLastScan",
        formatDateTime(
            getValue(data, [
                "finished_at",
                "generated_at"
            ])
        )
    );

    setText(
        "macdGeneratedAt",
        formatDateTime(
            getValue(data, [
                "generated_at",
                "finished_at"
            ])
        )
    );

    const progress =
        getProgress(data);

    setProgress(
        "macdProgressFill",
        "macdProgress",
        progress
    );

    renderResultTable(
        "macdResultBody",
        candidates,
        "MACD"
    );
}

/* =========================================================
   RESULT TABLE
========================================================= */

function renderResultTable(id, data, scanner) {

    const el = $(id);

    if (!el) return;

    if (!Array.isArray(data) || data.length === 0) {
        el.innerHTML = `
            <tr>
                <td colspan="20" class="empty">
                    Tidak ada kandidat
                </td>
            </tr>
        `;
        return;
    }

    el.innerHTML = data.map(item => {

        const ticker = getTicker(item);
        const sector = getSector(ticker);

        if (scanner === "MACD") {

            const price = valueToString(item, ["price", "Price"]);
            const spike = valueToString(item, ["spike_ratio", "Spike_Ratio"]);
            const hist = valueToString(item, ["macd_hist", "MACD_Hist"]);
            const value = valueToString(item, ["value", "Value_Str"]);
            const quality = valueToString(item, ["quality", "Quality"]);
            const histNum = Number(getValue(item, ["macd_hist", "MACD_Hist"]));

            return `
                <tr>
                    <td><strong>${escapeHTML(ticker)}</strong></td>
                    <td>${escapeHTML(shortSector(sector))}</td>
                    <td>${escapeHTML(price)}</td>
                    <td>${qualityBadge(quality)}</td>
                    <td>${escapeHTML(spike)}x</td>
                    <td class="${Number.isFinite(histNum) && histNum < 0 ? "neg" : "pos"}">${escapeHTML(hist)}</td>
                    <td>${escapeHTML(value)}</td>
                </tr>
            `;

        }

        const rr = valueToString(item, ["rr", "RR"]);
        const score = valueToString(item, ["score", "Score"]);

        return `
            <tr>
                <td><strong>${escapeHTML(ticker)}</strong></td>
                <td>${escapeHTML(shortSector(sector))}</td>
                <td>${escapeHTML(
                    valueToString(item, [
                        "ob_range",
                        "range",
                        "zone",
                        "order_block"
                    ])
                )}</td>
                <td>${escapeHTML(
                    valueToString(item, [
                        "sl",
                        "stop_loss",
                        "Stop Loss"
                    ])
                )}</td>
                <td>${escapeHTML(
                    valueToString(item, [
                        "tp",
                        "take_profit",
                        "Take Profit"
                    ])
                )}</td>
                <td>${escapeHTML(rr)}</td>
                <td><strong>${escapeHTML(score)}</strong></td>
            </tr>
        `;

    }).join("");
}

/* =========================================================
   QUALITY BADGE
========================================================= */

function qualityBadge(quality) {

    const text = String(quality || "-").toUpperCase();

    const cls =
        text === "HIGH" ? "badge-high" :
        text === "MED" ? "badge-med" :
        "badge-low";

    if (text === "-" || text === "") {
        return "-";
    }

    return `<span class="badge ${cls}">${escapeHTML(text)}</span>`;
}

/* =========================================================
   STATUS
========================================================= */

function renderStatus() {

    const status = APP_DATA.status || {};
    const ob = APP_DATA.ob || {};
    const macd = APP_DATA.macd || {};

    const statusText =
        getValue(status, ["status"]) ||
        getValue(ob, ["status"]) ||
        "unknown";

    setText(
        "dashboardStatus",
        statusText
    );

    setHeaderStatus(statusText);

    setText(
        "dashboardSlot",
        getValue(status, [
            "slot",
            "current_slot"
        ]) || "-"
    );

    setText(
        "dashboardFinished",
        formatDateTime(
            getValue(status, [
                "finished_at",
                "completed_at"
            ]) ||
            getValue(ob, [
                "finished_at"
            ])
        )
    );
}

/* =========================================================
   HISTORY
========================================================= */

function renderHistory() {

    const historyRoot = APP_DATA.history;

    if (!historyRoot) return;

    let history =
        Array.isArray(historyRoot)
            ? historyRoot
            : historyRoot.history;

    if (!Array.isArray(history)) {
        history = [];
    }

    if (historyFilter !== "ALL") {
        history = history.filter(
            item =>
                normalizeScanner(item.scanner) ===
                historyFilter
        );
    }

    renderHeatmap(history);
    renderRecap(history);
}

/* =========================================================
   HEATMAP
========================================================= */

function renderHeatmap(history) {

    const head = $("heatmapHead");
    const body = $("heatmapBody");

    if (!head || !body) return;

    const sectors = [
        "BASIC MATERIALS",
        "ENERGY",
        "FINANCIALS",
        "INDUSTRIALS",
        "CONSUMER NON-CYCLICALS",
        "CONSUMER CYCLICALS",
        "HEALTHCARE",
        "PROPERTIES & REAL ESTATE",
        "TECHNOLOGY",
        "INFRASTRUCTURES",
        "TRANSPORTATION & LOGISTIC"
    ];

    // Kolom = tanggal 1-31 (akumulasi kemunculan sektor pada tanggal itu,
    // digabung dari semua slot jam di hari yang sama)
    const days = Array.from({ length: 31 }, (_, i) => i + 1);

    head.innerHTML = `
        <tr>
            <th>Sektor</th>
            ${days.map(d => `<th>${d}</th>`).join("")}
        </tr>
    `;

    const grouped = {};

    sectors.forEach(sector => {
        grouped[sector] = {};
        days.forEach(d => {
            grouped[sector][d] = 0;
        });
    });

    history.forEach(snapshot => {

        const generated =
            snapshot.generated_at ||
            snapshot.date ||
            "";

        const date = extractDate(generated);

        if (!date) return;

        const day = parseInt(date.split("-")[2], 10);

        if (!Number.isFinite(day) || day < 1 || day > 31) {
            return;
        }

        const data =
            Array.isArray(snapshot.data)
                ? snapshot.data
                : [];

        data.forEach(item => {

            const ticker = getTicker(item);
            const sector = getSector(ticker);

            if (!grouped[sector]) return;

            grouped[sector][day] += 1;
        });
    });

    body.innerHTML = sectors.map(sector => {

        return `
            <tr>
                <td>${escapeHTML(sector)}</td>
                ${days.map(d => {

                    const count = grouped[sector][d];

                    return `
                        <td
                            class="heat-cell${count ? " has-value" : ""}"
                            title="${count} kemunculan pada tanggal ${d}"
                        >
                            ${count || ""}
                        </td>
                    `;

                }).join("")}
            </tr>
        `;

    }).join("");
}

/* =========================================================
   RECAP
========================================================= */

function renderRecap(history) {

    const body = $("recapBody");

    if (!body) return;

    const dates = {};

    history.forEach(snapshot => {

        const generated =
            snapshot.generated_at ||
            snapshot.date ||
            "";

        const date =
            extractDate(generated);

        if (!date) return;

        if (!dates[date]) {
            dates[date] = {
                ob: [],
                macd: []
            };
        }

        const scanner =
            normalizeScanner(snapshot.scanner);

        const tickers =
            Array.isArray(snapshot.data)
                ? snapshot.data.map(getTicker).filter(Boolean)
                : [];

        if (scanner === "SMC OB") {
            dates[date].ob.push({
                slot: snapshot.slot,
                tickers
            });
        }

        if (scanner === "MACD") {
            dates[date].macd.push({
                slot: snapshot.slot,
                tickers
            });
        }
    });

    const sortedDates =
        Object.keys(dates).sort().reverse();

    if (sortedDates.length === 0) {

        body.innerHTML = `
            <tr>
                <td colspan="3">Belum ada history</td>
            </tr>
        `;

        return;
    }

    body.innerHTML =
        sortedDates.map(date => {

            return `
                <tr>
                    <td>
                        <strong>${formatDateOnly(date)}</strong>
                    </td>

                    <td>
                        ${renderRecapScanner(
                            dates[date].ob
                        )}
                    </td>

                    <td>
                        ${renderRecapScanner(
                            dates[date].macd
                        )}
                    </td>
                </tr>
            `;

        }).join("");
}

function renderRecapScanner(items) {

    if (!items.length) return "-";

    return items.map(item => {

        const tickerText =
            item.tickers.length
                ? item.tickers.map(
                    x => `<strong>${escapeHTML(x)}</strong>`
                ).join(" ")
                : "-";

        return `
            <div class="recap-line">
                <span class="time-badge">
                    ${escapeHTML(item.slot || "-")}
                </span>
                ${tickerText}
            </div>
        `;

    }).join("");
}

/* =========================================================
   NAVIGATION
========================================================= */

function switchPage(page) {

    document
        .querySelectorAll(".page")
        .forEach(el => {
            el.classList.remove("active");
        });

    document
        .querySelectorAll("[data-page]")
        .forEach(el => {
            el.classList.remove("active");
        });

    const target = $(`page-${page}`);

    if (target) {
        target.classList.add("active");
    }

    const nav =
        document.querySelector(
            `[data-page="${page}"]`
        );

    if (nav) {
        nav.classList.add("active");
    }

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}

/* =========================================================
   HISTORY FILTER
========================================================= */

function setHistoryFilter(filter) {

    historyFilter =
        String(filter || "ALL").toUpperCase();

    document
        .querySelectorAll("[data-filter]")
        .forEach(button => {

            button.classList.toggle(
                "active",
                String(
                    button.dataset.filter || ""
                ).toUpperCase() === historyFilter
            );

        });

    renderHistory();
}

/* =========================================================
   REFRESH
========================================================= */

async function refreshAll() {

    const buttons =
        document.querySelectorAll(
            "[data-refresh], #refreshButton"
        );

    buttons.forEach(button => {
        button.disabled = true;
    });

    try {
        await loadData();
    }
    catch (error) {
        console.error(error);

        setText(
            "dashboardStatus",
            "Gagal memuat data"
        );
    }

    buttons.forEach(button => {
        button.disabled = false;
    });
}

/* =========================================================
   INIT NAV
========================================================= */

function setupNavigation() {

    document
        .querySelectorAll("[data-page]")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    const page =
                        button.dataset.page;

                    if (page) {
                        switchPage(page);
                    }

                }
            );

        });
}

/* =========================================================
   INIT FILTER
========================================================= */

function setupFilters() {

    document
        .querySelectorAll("[data-filter]")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    setHistoryFilter(
                        button.dataset.filter
                    );

                }
            );

        });
}

/* =========================================================
   AUTO REFRESH
========================================================= */

function setupAutoRefresh() {

    setInterval(
        () => {
            loadData().catch(
                error =>
                    console.error(
                        "Auto refresh:",
                        error
                    )
            );
        },
        60000
    );
}

/* =========================================================
   HELPERS
========================================================= */

function setText(id, value) {

    const el = $(id);

    if (!el) return;

    el.textContent =
        value === null ||
        value === undefined ||
        value === ""
            ? "-"
            : String(value);
}

function setProgress(fillId, textId, value) {

    const fill = $(fillId);
    const text = $(textId);

    const number =
        Math.max(
            0,
            Math.min(
                100,
                Number(value) || 0
            )
        );

    if (fill) {
        fill.style.width = `${number}%`;
    }

    if (text) {
        text.textContent = `${number}%`;
    }
}

function getProgress(data) {

    const processed =
        Number(
            getValue(data, [
                "processed",
                "progress"
            ])
        );

    const total =
        Number(
            getValue(data, [
                "total_tickers",
                "total"
            ])
        );

    if (
        Number.isFinite(processed) &&
        Number.isFinite(total) &&
        total > 0
    ) {
        return Math.round(
            processed / total * 100
        );
    }

    const direct =
        Number(
            getValue(data, [
                "progress_percent"
            ])
        );

    return Number.isFinite(direct)
        ? direct
        : 100;
}

function getDuration(data) {

    return (
        getValue(data, [
            "duration_text"
        ]) ||
        formatDuration(
            getValue(data, [
                "duration_seconds",
                "duration"
            ])
        ) ||
        "-"
    );
}

function formatDuration(value) {

    const seconds = Number(value);

    if (!Number.isFinite(seconds)) {
        return "";
    }

    if (seconds < 60) {
        return `${Math.round(seconds)} detik`;
    }

    const minutes =
        Math.floor(seconds / 60);

    const sec =
        Math.round(seconds % 60);

    return `${minutes}m ${sec}d`;
}

/* =========================================================
   GET CANDIDATES
========================================================= */

function getCandidateArray(data) {

    if (!data) return [];

    if (Array.isArray(data)) {
        return data;
    }

    if (Array.isArray(data.data)) {
        return data.data;
    }

    if (Array.isArray(data.candidates_data)) {
        return data.candidates_data;
    }

    if (Array.isArray(data.results)) {
        return data.results;
    }

    if (Array.isArray(data.candidates_list)) {
        return data.candidates_list;
    }

    return [];
}

/* =========================================================
   GET TICKER
========================================================= */

function getTicker(item) {

    if (typeof item === "string") {
        return item;
    }

    if (!item || typeof item !== "object") {
        return "-";
    }

    const value =
        getValue(item, [
            "ticker",
            "symbol",
            "code",
            "kode",
            "Ticker",
            "Symbol"
        ]);

    return value
        ? String(value).replace(
            /\.JK$/i,
            ""
        )
        : "-";
}

/* =========================================================
   GET SECTOR
========================================================= */

function getSector(ticker) {

    if (!ticker) {
        return "UNKNOWN";
    }

    const map =
        APP_DATA.sector &&
        APP_DATA.sector.map
            ? APP_DATA.sector.map
            : {};

    const full =
        ticker.endsWith(".JK")
            ? ticker
            : `${ticker}.JK`;

    return (
        map[full] ||
        map[ticker] ||
        "UNKNOWN"
    );
}

function shortSector(sector) {

    if (!sector) return "-";

    const replacements = {
        "CONSUMER NON-CYCLICALS": "NON-CYCLICAL",
        "CONSUMER CYCLICALS": "CYCLICAL",
        "PROPERTIES & REAL ESTATE": "PROPERTY",
        "TRANSPORTATION & LOGISTIC": "TRANSPORT",
        "BASIC MATERIALS": "BASIC MAT",
        "INFRASTRUCTURES": "INFRA"
    };

    return replacements[sector] || sector;
}

/* =========================================================
   GENERIC VALUE
========================================================= */

function getValue(object, keys) {

    if (!object || typeof object !== "object") {
        return null;
    }

    for (const key of keys) {

        if (
            Object.prototype.hasOwnProperty.call(
                object,
                key
            )
        ) {
            const value = object[key];

            if (
                value !== null &&
                value !== undefined &&
                value !== ""
            ) {
                return value;
            }
        }
    }

    return null;
}

function valueToString(item, keys) {

    const value =
        getValue(item, keys);

    if (
        value === null ||
        value === undefined
    ) {
        return "-";
    }

    if (typeof value === "object") {
        return JSON.stringify(value);
    }

    return String(value);
}

/* =========================================================
   STATUS TEXT
========================================================= */

function getStatusText() {

    const status =
        getValue(
            APP_DATA.status,
            ["status"]
        );

    if (status) {
        return String(status).toUpperCase();
    }

    const obStatus =
        getValue(
            APP_DATA.ob,
            ["status"]
        );

    if (obStatus) {
        return String(obStatus).toUpperCase();
    }

    return "READY";
}

/* =========================================================
   SCANNER NORMALIZATION
========================================================= */

function normalizeScanner(value) {

    const text =
        String(value || "")
            .trim()
            .toUpperCase();

    if (
        text.includes("MACD")
    ) {
        return "MACD";
    }

    if (
        text.includes("OB")
    ) {
        return "SMC OB";
    }

    return text;
}

/* =========================================================
   DATE
========================================================= */

function extractDate(value) {

    if (!value) return "";

    const match =
        String(value).match(
            /^(\d{4}-\d{2}-\d{2})/
        );

    return match
        ? match[1]
        : "";
}

function formatDateOnly(value) {

    if (!value) return "-";

    const parts =
        String(value).split("-");

    if (parts.length !== 3) {
        return value;
    }

    return `${parts[2]} ${monthName(parts[1])}`;
}

function monthName(month) {

    const names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "Mei",
        "Jun",
        "Jul",
        "Agu",
        "Sep",
        "Okt",
        "Nov",
        "Des"
    ];

    return names[
        Number(month) - 1
    ] || month;
}

function formatDateTime(value) {

    if (!value) return "-";

    const text = String(value);

    if (
        /^\d{4}-\d{2}-\d{2}/.test(text)
    ) {

        const date =
            text.substring(0, 10);

        const time =
            text.substring(11, 16);

        return `${formatDateOnly(date)} ${time}`;
    }

    return text;
}

/* =========================================================
   HTML ESCAPE
========================================================= */

function escapeHTML(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/* =========================================================
   START
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        setupNavigation();
        setupFilters();

        const refresh =
            $("refreshButton");

        if (refresh) {
            refresh.addEventListener(
                "click",
                refreshAll
            );
        }

        await loadData();

        switchPage("dashboard");

        setupAutoRefresh();
    }
);
