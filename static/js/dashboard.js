/**
 * Python Error Logger - Vanilla JavaScript Application Logic
 * ==========================================================
 * Implements real-time log polling, responsive navigation, dynamic search & filtering,
 * secure DOM rendering (XSS prevention), traceback modal inspection, and scenario simulation.
 */

(function () {
    'use strict';

    // Application State
    let logEntries = [];
    let summaryData = null;
    let selectedLogIndex = null;
    let isFetching = false;
    let pollingIntervalId = null;
    const POLLING_INTERVAL_MS = 1500;

    // DOM Elements Cache
    const elements = {
        // Navigation & Layout
        sidebar: document.getElementById('sidebar'),
        sidebarToggleBtn: document.getElementById('sidebar-toggle-btn'),
        sidebarCloseBtn: document.getElementById('sidebar-close-btn'),
        navDashboard: document.getElementById('nav-dashboard'),
        navLogs: document.getElementById('nav-logs'),
        navAbout: document.getElementById('nav-about'),
        navLogsBadge: document.getElementById('nav-logs-badge'),
        currentSectionTitle: document.getElementById('current-section-title'),
        dashboardSection: document.getElementById('dashboard-section'),
        logsSection: document.getElementById('logs-section'),
        aboutSection: document.getElementById('about-section'),

        // Topbar Controls
        refreshBtn: document.getElementById('refresh-btn'),
        refreshSpin: document.getElementById('refresh-spin'),
        livePollingToggle: document.getElementById('live-polling-toggle'),

        // Summary Metric Cards
        cardTotal: document.getElementById('card-total'),
        cardErrors: document.getElementById('card-errors'),
        cardCritical: document.getElementById('card-critical'),
        cardWarnings: document.getElementById('card-warnings'),
        cardInfo: document.getElementById('card-info'),
        dashboardExceptionPills: document.getElementById('dashboard-exception-pills'),

        // Recent Errors Table
        recentErrorsTbody: document.getElementById('recent-errors-tbody'),

        // Search & Filters
        logSearchInput: document.getElementById('log-search-input'),
        clearSearchBtn: document.getElementById('clear-search-btn'),
        filterLevelSelect: document.getElementById('filter-level-select'),
        filterTypeSelect: document.getElementById('filter-type-select'),
        filteredCounterBadge: document.getElementById('filtered-counter-badge'),

        // Main Log Table & States
        mainLogTable: document.getElementById('main-log-table'),
        mainLogTbody: document.getElementById('main-log-tbody'),
        logLoadingState: document.getElementById('log-loading-state'),
        logEmptyState: document.getElementById('log-empty-state'),
        emptyStateDesc: document.getElementById('empty-state-desc'),
        logErrorState: document.getElementById('log-error-state'),
        logErrorMessage: document.getElementById('log-error-message'),

        // Modal Dialog
        logDetailModal: document.getElementById('log-detail-modal'),
        modalBadge: document.getElementById('modal-badge'),
        modalTitle: document.getElementById('modal-title'),
        modalTimestamp: document.getElementById('modal-timestamp'),
        modalSource: document.getElementById('modal-source'),
        modalMessage: document.getElementById('modal-message'),
        modalTracebackSection: document.getElementById('modal-traceback-section'),
        modalTraceback: document.getElementById('modal-traceback'),
        copyTracebackBtn: document.getElementById('copy-traceback-btn'),

        // Status & Toast
        logFileIndicator: document.getElementById('log-file-indicator'),
        toastBanner: document.getElementById('toast-banner'),
    };

    /**
     * Display a floating toast notification
     */
    function showToast(message, type = 'info') {
        const toast = elements.toastBanner;
        if (!toast) return;

        toast.textContent = message;
        toast.className = 'toast-banner';
        if (type === 'error') {
            toast.classList.add('toast-error');
        } else if (type === 'success') {
            toast.classList.add('toast-success');
        }

        clearTimeout(toast._timeout);
        toast._timeout = setTimeout(() => {
            toast.classList.add('hidden');
        }, 3200);
    }

    /**
     * Safe text escaping helper for extra security
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Navigate between sections: dashboard-section, logs-section, about-section
     */
    window.navigateToSection = function (sectionId) {
        const sections = [elements.dashboardSection, elements.logsSection, elements.aboutSection];
        const navItems = [elements.navDashboard, elements.navLogs, elements.navAbout];

        sections.forEach(sec => {
            if (sec) sec.classList.remove('active');
        });
        navItems.forEach(nav => {
            if (nav) nav.classList.remove('active');
        });

        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.add('active');
        }

        let sectionName = 'Dashboard';
        if (sectionId === 'logs-section') {
            sectionName = 'Error Logs';
            if (elements.navLogs) elements.navLogs.classList.add('active');
            window.location.hash = '#logs';
        } else if (sectionId === 'about-section') {
            sectionName = 'About System';
            if (elements.navAbout) elements.navAbout.classList.add('active');
            window.location.hash = '#about';
        } else {
            if (elements.navDashboard) elements.navDashboard.classList.add('active');
            window.location.hash = '#dashboard';
        }

        if (elements.currentSectionTitle) {
            elements.currentSectionTitle.textContent = sectionName;
        }

        // Close mobile drawer if opened
        if (elements.sidebar) {
            elements.sidebar.classList.remove('open');
        }
    };

    /**
     * Fetch structured logs & summary metrics from Flask backend
     */
    window.fetchData = async function (isManual = false) {
        if (isFetching) return;
        isFetching = true;

        if (isManual && elements.refreshSpin) {
            elements.refreshSpin.classList.add('spinning');
        }

        try {
            const [logsResponse, summaryResponse] = await Promise.all([
                fetch('/api/logs', { cache: 'no-store' }),
                fetch('/api/summary', { cache: 'no-store' })
            ]);

            if (!logsResponse.ok || !summaryResponse.ok) {
                throw new Error(`Server returned HTTP ${logsResponse.status} / ${summaryResponse.status}`);
            }

            const logsJson = await logsResponse.json();
            const summaryJson = await summaryResponse.json();

            // Check if log file is available
            if (elements.logFileIndicator) {
                if (logsJson.status === 'error') {
                    elements.logFileIndicator.className = 'status-indicator offline';
                } else {
                    elements.logFileIndicator.className = 'status-indicator online';
                }
            }

            logEntries = logsJson.logs || [];
            summaryData = summaryJson;

            // Update UI elements
            updateSummaryCards(summaryJson, logEntries);
            updateExceptionPills(summaryJson.error_types || {});
            populateExceptionFilterOptions(summaryJson.error_types || {}, logEntries);
            renderRecentErrors(logEntries);
            applyFilters();

            // Hide error state if previously shown
            if (elements.logErrorState) {
                elements.logErrorState.classList.add('hidden');
            }

            if (isManual) {
                showToast('Refreshed logs and metrics.', 'success');
            }
        } catch (err) {
            console.error('Failed to fetch data from backend:', err);
            if (elements.logFileIndicator) {
                elements.logFileIndicator.className = 'status-indicator offline';
            }
            if (logEntries.length === 0 && elements.logErrorState) {
                elements.logErrorState.classList.remove('hidden');
                if (elements.logErrorMessage) {
                    elements.logErrorMessage.textContent = `Backend connection error: ${err.message}`;
                }
                if (elements.mainLogTable) elements.mainLogTable.classList.add('hidden');
            }
            if (isManual) {
                showToast(`Failed to load logs: ${err.message}`, 'error');
            }
        } finally {
            isFetching = false;
            if (elements.refreshSpin) {
                elements.refreshSpin.classList.remove('spinning');
            }
            if (elements.logLoadingState) {
                elements.logLoadingState.classList.add('hidden');
            }
        }
    };

    /**
     * Update summary metrics cards
     */
    function updateSummaryCards(summary, logs) {
        const levels = summary.levels || {};
        const totalEntries = summary.total_entries !== undefined ? summary.total_entries : logs.length;
        const totalErrors = summary.total_errors !== undefined ? summary.total_errors : (levels.ERROR || 0) + (levels.CRITICAL || 0);

        if (elements.cardTotal) elements.cardTotal.textContent = totalEntries.toLocaleString();
        if (elements.cardErrors) elements.cardErrors.textContent = totalErrors.toLocaleString();
        if (elements.cardCritical) elements.cardCritical.textContent = (levels.CRITICAL || 0).toLocaleString();
        if (elements.cardWarnings) elements.cardWarnings.textContent = (levels.WARNING || 0).toLocaleString();
        if (elements.cardInfo) elements.cardInfo.textContent = (levels.INFO || 0).toLocaleString();

        if (elements.navLogsBadge) {
            elements.navLogsBadge.textContent = totalEntries;
            elements.navLogsBadge.style.display = totalEntries > 0 ? 'inline-block' : 'none';
        }
    }

    /**
     * Update detected exception type pills in dashboard
     */
    function updateExceptionPills(errorTypes) {
        const container = elements.dashboardExceptionPills;
        if (!container) return;

        // Clear existing children safely
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }

        const keys = Object.keys(errorTypes);
        if (keys.length === 0) {
            const span = document.createElement('span');
            span.className = 'placeholder-text';
            span.textContent = 'No exceptions captured yet.';
            container.appendChild(span);
            return;
        }

        keys.forEach(excType => {
            const count = errorTypes[excType];
            const pill = document.createElement('button');
            pill.className = 'exception-pill';
            pill.type = 'button';
            pill.title = `Filter logs by ${excType}`;

            const labelSpan = document.createElement('span');
            labelSpan.textContent = excType;

            const countBadge = document.createElement('span');
            countBadge.className = 'exception-pill-count';
            countBadge.textContent = count;

            pill.appendChild(labelSpan);
            pill.appendChild(countBadge);

            pill.addEventListener('click', () => {
                navigateToSection('logs-section');
                if (elements.filterTypeSelect) {
                    elements.filterTypeSelect.value = excType;
                }
                applyFilters();
            });

            container.appendChild(pill);
        });
    }

    /**
     * Populate Exception Type dropdown options
     */
    function populateExceptionFilterOptions(errorTypes, logs) {
        const select = elements.filterTypeSelect;
        if (!select) return;

        const currentVal = select.value;
        const typesSet = new Set(Object.keys(errorTypes));

        // Scan logs for any additional exceptions parsed in tracebacks
        logs.forEach(entry => {
            if (entry.traceback) {
                const match = entry.traceback.match(/([a-zA-Z_][a-zA-Z0-9_]*Error|[a-zA-Z_][a-zA-Z0-9_]*Exception):/);
                if (match) {
                    typesSet.add(match[1]);
                }
            }
        });

        // Rebuild options
        select.innerHTML = '<option value="ALL">All Exceptions</option>';
        Array.from(typesSet).sort().forEach(type => {
            const opt = document.createElement('option');
            opt.value = type;
            opt.textContent = type;
            select.appendChild(opt);
        });

        if (Array.from(select.options).some(o => o.value === currentVal)) {
            select.value = currentVal;
        }
    }

    /**
     * Render the 5 most recent error entries on the Dashboard section
     */
    function renderRecentErrors(logs) {
        const tbody = elements.recentErrorsTbody;
        if (!tbody) return;

        while (tbody.firstChild) {
            tbody.removeChild(tbody.firstChild);
        }

        const errorEntries = logs.filter(e => {
            const lvl = (e.level || '').toUpperCase();
            return lvl === 'ERROR' || lvl === 'CRITICAL' || !!e.traceback;
        }).slice(-5).reverse();

        if (errorEntries.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 5;
            td.className = 'table-empty-cell';
            td.textContent = 'No error events recorded yet.';
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }

        errorEntries.forEach(entry => {
            const tr = document.createElement('tr');

            // Timestamp
            const tdTime = document.createElement('td');
            tdTime.className = 'cell-timestamp';
            tdTime.textContent = entry.timestamp || 'N/A';
            tr.appendChild(tdTime);

            // Level Badge
            const tdLevel = document.createElement('td');
            const badge = document.createElement('span');
            const lvl = (entry.level || 'UNKNOWN').toUpperCase();
            badge.className = `badge-level badge-${lvl.toLowerCase()}`;
            badge.textContent = lvl;
            tdLevel.appendChild(badge);
            tr.appendChild(tdLevel);

            // Source
            const tdSource = document.createElement('td');
            tdSource.className = 'cell-source';
            tdSource.title = entry.source || '';
            tdSource.textContent = entry.source || '-';
            tr.appendChild(tdSource);

            // Message
            const tdMsg = document.createElement('td');
            tdMsg.className = 'cell-message';
            tdMsg.title = entry.message || '';
            tdMsg.textContent = entry.message || '';
            tr.appendChild(tdMsg);

            // Action
            const tdAction = document.createElement('td');
            tdAction.style.textAlign = 'center';
            const viewBtn = document.createElement('button');
            viewBtn.className = 'btn btn-sm btn-outline';
            viewBtn.type = 'button';
            viewBtn.textContent = 'Inspect';
            viewBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                openLogModal(entry);
            });
            tdAction.appendChild(viewBtn);
            tr.appendChild(tdAction);

            tr.addEventListener('click', () => openLogModal(entry));
            tr.style.cursor = 'pointer';

            tbody.appendChild(tr);
        });
    }

    /**
     * Filter and render main log table
     */
    window.applyFilters = function () {
        const searchInput = elements.logSearchInput;
        const clearBtn = elements.clearSearchBtn;
        const levelSelect = elements.filterLevelSelect;
        const typeSelect = elements.filterTypeSelect;
        const tbody = elements.mainLogTbody;
        const emptyState = elements.logEmptyState;
        const mainTable = elements.mainLogTable;
        const counterBadge = elements.filteredCounterBadge;

        if (!tbody) return;

        const searchTerm = (searchInput ? searchInput.value.trim().toLowerCase() : '');
        if (clearBtn) {
            clearBtn.style.display = searchTerm.length > 0 ? 'inline-block' : 'none';
        }

        const selectedLevel = levelSelect ? levelSelect.value : 'ALL';
        const selectedType = typeSelect ? typeSelect.value : 'ALL';

        // Filter log entries
        const filtered = logEntries.filter(entry => {
            const level = (entry.level || 'UNKNOWN').toUpperCase();
            if (selectedLevel !== 'ALL' && level !== selectedLevel) {
                return false;
            }

            if (selectedType !== 'ALL') {
                const hasType = (entry.traceback && entry.traceback.includes(selectedType)) ||
                    (entry.message && entry.message.includes(selectedType));
                if (!hasType) return false;
            }

            if (searchTerm) {
                const timeMatch = (entry.timestamp || '').toLowerCase().includes(searchTerm);
                const sourceMatch = (entry.source || '').toLowerCase().includes(searchTerm);
                const messageMatch = (entry.message || '').toLowerCase().includes(searchTerm);
                const tracebackMatch = (entry.traceback || '').toLowerCase().includes(searchTerm);
                if (!timeMatch && !sourceMatch && !messageMatch && !tracebackMatch) {
                    return false;
                }
            }

            return true;
        });

        // Update counter
        if (counterBadge) {
            counterBadge.textContent = `Showing ${filtered.length} of ${logEntries.length} entries`;
        }

        // Handle empty table states
        if (logEntries.length === 0) {
            if (mainTable) mainTable.classList.add('hidden');
            if (emptyState) {
                emptyState.classList.remove('hidden');
                if (elements.emptyStateDesc) {
                    elements.emptyStateDesc.textContent = 'No log entries found. The log file is empty. Execute a scenario to record events.';
                }
            }
            return;
        }

        if (filtered.length === 0) {
            if (mainTable) mainTable.classList.add('hidden');
            if (emptyState) {
                emptyState.classList.remove('hidden');
                if (elements.emptyStateDesc) {
                    elements.emptyStateDesc.textContent = 'No log entries match your current search and filter criteria.';
                }
            }
            return;
        }

        // Show table
        if (emptyState) emptyState.classList.add('hidden');
        if (mainTable) mainTable.classList.remove('hidden');

        // Clear existing rows safely
        while (tbody.firstChild) {
            tbody.removeChild(tbody.firstChild);
        }

        // Render filtered entries (newest on top)
        const reversedList = [...filtered].reverse();
        reversedList.forEach(entry => {
            const tr = document.createElement('tr');

            // Timestamp
            const tdTime = document.createElement('td');
            tdTime.className = 'cell-timestamp';
            tdTime.textContent = entry.timestamp || 'N/A';
            tr.appendChild(tdTime);

            // Severity Badge
            const tdLevel = document.createElement('td');
            const badge = document.createElement('span');
            const lvl = (entry.level || 'UNKNOWN').toUpperCase();
            badge.className = `badge-level badge-${lvl.toLowerCase()}`;
            badge.textContent = lvl;
            tdLevel.appendChild(badge);
            tr.appendChild(tdLevel);

            // Source
            const tdSource = document.createElement('td');
            tdSource.className = 'cell-source';
            tdSource.title = entry.source || '';
            tdSource.textContent = entry.source || '-';
            tr.appendChild(tdSource);

            // Message with optional traceback indicator
            const tdMsg = document.createElement('td');
            tdMsg.className = 'cell-message';
            tdMsg.title = entry.message || '';

            const msgSpan = document.createElement('span');
            msgSpan.textContent = entry.message || '';
            tdMsg.appendChild(msgSpan);

            if (entry.traceback) {
                const tbTag = document.createElement('span');
                tbTag.className = 'traceback-indicator';
                tbTag.textContent = '⚡ Traceback';
                tbTag.title = 'Click row or View Details to inspect stack trace';
                tdMsg.appendChild(tbTag);
            }
            tr.appendChild(tdMsg);

            // Action: View Details button
            const tdAction = document.createElement('td');
            tdAction.style.textAlign = 'center';
            const viewBtn = document.createElement('button');
            viewBtn.className = 'btn btn-sm btn-outline';
            viewBtn.type = 'button';
            viewBtn.textContent = 'View';
            viewBtn.title = 'Inspect log entry details';
            viewBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                openLogModal(entry);
            });
            tdAction.appendChild(viewBtn);
            tr.appendChild(tdAction);

            tr.addEventListener('click', () => openLogModal(entry));
            tr.style.cursor = 'pointer';

            tbody.appendChild(tr);
        });
    };

    /**
     * Clear search input
     */
    window.clearSearch = function () {
        if (elements.logSearchInput) {
            elements.logSearchInput.value = '';
        }
        applyFilters();
    };

    /**
     * Open Log Details Modal with safe content injection
     */
    function openLogModal(entry) {
        if (!elements.logDetailModal) return;

        const lvl = (entry.level || 'UNKNOWN').toUpperCase();
        if (elements.modalBadge) {
            elements.modalBadge.className = `badge-level badge-${lvl.toLowerCase()}`;
            elements.modalBadge.textContent = lvl;
        }

        if (elements.modalTitle) {
            elements.modalTitle.textContent = `${lvl} Log Details`;
        }

        if (elements.modalTimestamp) {
            elements.modalTimestamp.textContent = entry.timestamp || 'N/A';
        }

        if (elements.modalSource) {
            elements.modalSource.textContent = entry.source || 'Unknown Source Location';
        }

        if (elements.modalMessage) {
            elements.modalMessage.textContent = entry.message || '(No message content)';
        }

        if (elements.modalTracebackSection && elements.modalTraceback) {
            if (entry.traceback && entry.traceback.trim()) {
                elements.modalTracebackSection.style.display = 'block';
                elements.modalTraceback.textContent = entry.traceback;
                if (elements.copyTracebackBtn) elements.copyTracebackBtn.style.display = 'inline-flex';
            } else {
                elements.modalTracebackSection.style.display = 'none';
                elements.modalTraceback.textContent = '';
                if (elements.copyTracebackBtn) elements.copyTracebackBtn.style.display = 'none';
            }
        }

        elements.logDetailModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';

        // Focus trap helper
        const closeBtn = document.getElementById('modal-close-btn');
        if (closeBtn) closeBtn.focus();
    }

    /**
     * Close Log Details Modal
     */
    window.closeLogModal = function () {
        if (!elements.logDetailModal) return;
        elements.logDetailModal.classList.add('hidden');
        document.body.style.overflow = '';
    };

    /**
     * Copy traceback text to clipboard
     */
    window.copyTracebackText = function () {
        const text = elements.modalTraceback ? elements.modalTraceback.textContent : '';
        if (!text) return;

        navigator.clipboard.writeText(text).then(() => {
            const btn = elements.copyTracebackBtn;
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✓ Copied!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            }
            showToast('Stack traceback copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Copy failed:', err);
            showToast('Failed to copy traceback to clipboard.', 'error');
        });
    };

    /**
     * Trigger realistic error scenarios via Flask POST endpoint
     */
    window.triggerScenario = async function (scenarioName) {
        try {
            showToast(`Triggering scenario: ${scenarioName}...`, 'info');
            const res = await fetch(`/api/trigger/${scenarioName}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await res.json();

            if (data.success) {
                showToast(`Success: ${data.message}`, 'success');
            } else {
                showToast(`Simulation failed: ${data.message}`, 'error');
            }

            // Immediately refresh data
            await fetchData();
        } catch (err) {
            console.error('Trigger error:', err);
            showToast(`Failed to trigger scenario: ${err.message}`, 'error');
        }
    };

    /**
     * Clear log file with confirmation prompt
     */
    window.clearLogsPrompt = async function () {
        const confirmed = window.confirm('Are you sure you want to clear all contents of logs/app.log? This operation cannot be undone.');
        if (!confirmed) return;

        try {
            const res = await fetch('/api/clear', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                showToast('Log file cleared successfully.', 'success');
                await fetchData();
            } else {
                showToast(`Clear failed: ${data.message}`, 'error');
            }
        } catch (err) {
            console.error('Clear log error:', err);
            showToast(`Error clearing log: ${err.message}`, 'error');
        }
    };

    /**
     * Polling manager
     */
    function setupPolling() {
        const toggle = elements.livePollingToggle;
        if (!toggle) return;

        const updatePollingState = () => {
            if (toggle.checked) {
                if (!pollingIntervalId) {
                    pollingIntervalId = setInterval(() => {
                        // Avoid fetching when page is hidden to save bandwidth
                        if (!document.hidden) {
                            fetchData();
                        }
                    }, POLLING_INTERVAL_MS);
                }
            } else {
                if (pollingIntervalId) {
                    clearInterval(pollingIntervalId);
                    pollingIntervalId = null;
                }
            }
        };

        toggle.addEventListener('change', updatePollingState);
        updatePollingState();
    }

    /**
     * Setup keyboard shortcuts & modal backdrop clicks
     */
    function setupEventListeners() {
        // Modal backdrop click
        if (elements.logDetailModal) {
            elements.logDetailModal.addEventListener('click', (e) => {
                if (e.target === elements.logDetailModal) {
                    closeLogModal();
                }
            });
        }

        // ESC key to close modal
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeLogModal();
                if (elements.sidebar) {
                    elements.sidebar.classList.remove('open');
                }
            }
        });

        // Mobile drawer toggling
        if (elements.sidebarToggleBtn && elements.sidebar) {
            elements.sidebarToggleBtn.addEventListener('click', () => {
                elements.sidebar.classList.toggle('open');
            });
        }

        if (elements.sidebarCloseBtn && elements.sidebar) {
            elements.sidebarCloseBtn.addEventListener('click', () => {
                elements.sidebar.classList.remove('open');
            });
        }

        // Section navigation clicks
        const navLinks = [
            { el: elements.navDashboard, target: 'dashboard-section' },
            { el: elements.navLogs, target: 'logs-section' },
            { el: elements.navAbout, target: 'about-section' }
        ];

        navLinks.forEach(({ el, target }) => {
            if (el) {
                el.addEventListener('click', (e) => {
                    e.preventDefault();
                    navigateToSection(target);
                });
            }
        });

        // Handle URL hash on initial load
        const hash = window.location.hash;
        if (hash === '#logs') {
            navigateToSection('logs-section');
        } else if (hash === '#about') {
            navigateToSection('about-section');
        } else {
            navigateToSection('dashboard-section');
        }
    }

    // Initialize application
    document.addEventListener('DOMContentLoaded', () => {
        setupEventListeners();
        setupPolling();
        fetchData();
    });

})();
