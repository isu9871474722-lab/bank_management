// Application State
let currentSession = {
    role: null,         // 'admin' or 'customer'
    username: null,     // admin username
    accountNumber: null, // customer account number
    name: null          // user full name
};

// API Base URL (empty since backend is self-serving)
const API_BASE = "";

// Initialize application on page load
document.addEventListener("DOMContentLoaded", () => {
    checkSystemStatus();
    setupFormListeners();
});

// Check database connection status
async function checkSystemStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();
        
        if (data.status === "setup_required") {
            switchView("setup-view");
            showToast("Database setup is required.", "info");
        } else {
            switchView("portal-view");
        }
    } catch (err) {
        showToast("Cannot connect to server. Ensure Flask backend is running.", "error");
    }
}

// Router: Switch Main View Containers
function switchView(viewId) {
    document.querySelectorAll(".view").forEach(view => {
        view.classList.add("hidden");
    });
    const target = document.getElementById(viewId);
    if (target) {
        target.classList.remove("hidden");
    }
}

// Sidebar Tab Routers (Admin)
function switchAdminTab(tabName) {
    document.querySelectorAll("#admin-dashboard-view .dashboard-tab").forEach(tab => {
        tab.classList.remove("active-tab");
    });
    document.querySelectorAll("#admin-dashboard-view .nav-item").forEach(item => {
        item.classList.remove("active");
    });
    
    // Activate target tab
    const targetTab = document.getElementById(`tab-${tabName}`);
    if (targetTab) targetTab.classList.add("active-tab");
    
    // Activate nav button
    const navBtn = document.querySelector(`#admin-dashboard-view nav button[onclick="switchAdminTab('${tabName}')"]`);
    if (navBtn) navBtn.classList.add("active");
    
    // Trigger data fetch if required
    if (tabName === "view-accounts") {
        loadAdminAccounts();
    } else if (tabName === "global-ledger") {
        loadAdminLedger();
    }
}

// Sidebar Tab Routers (Customer)
function switchCustomerTab(tabName) {
    document.querySelectorAll("#customer-dashboard-view .dashboard-tab").forEach(tab => {
        tab.classList.remove("active-tab");
    });
    document.querySelectorAll("#customer-dashboard-view .nav-item").forEach(item => {
        item.classList.remove("active");
    });
    
    const targetTab = document.getElementById(`tab-cust-${tabName}`);
    if (targetTab) targetTab.classList.add("active-tab");
    
    const navBtn = document.querySelector(`#customer-dashboard-view nav button[onclick="switchCustomerTab('${tabName}')"]`);
    if (navBtn) navBtn.classList.add("active");
    
    // Refresh content
    if (tabName === "overview") {
        loadCustomerOverview();
    } else if (tabName === "statement") {
        loadCustomerStatement();
    }
}

// Form Handlers
function setupFormListeners() {
    // 1. Setup Wizard Form
    document.getElementById("setup-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const host = document.getElementById("setup-host").value || "localhost";
        const user = document.getElementById("setup-user").value || "root";
        const password = document.getElementById("setup-password").value;
        const port = document.getElementById("setup-port").value || "3306";
        
        try {
            const response = await fetch(`${API_BASE}/api/setup`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ host, user, password, port })
            });
            const data = await response.json();
            if (response.ok) {
                showToast(data.message, "success");
                switchView("portal-view");
            } else {
                showToast(data.message || "Setup failed.", "error");
            }
        } catch (err) {
            showToast("Server error during setup.", "error");
        }
    });

    // 2. Admin Login Form
    document.getElementById("admin-login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("admin-user").value;
        const password = document.getElementById("admin-pass").value;
        
        try {
            const response = await fetch(`${API_BASE}/api/auth/admin/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();
            if (response.ok) {
                currentSession.role = 'admin';
                currentSession.username = data.user.username;
                currentSession.name = data.user.name;
                
                document.getElementById("admin-profile-name").textContent = data.user.name;
                showToast(data.message, "success");
                switchView("admin-dashboard-view");
                switchAdminTab("view-accounts");
            } else {
                showToast(data.message, "error");
            }
        } catch (err) {
            showToast("Login server failed.", "error");
        }
    });

    // 3. Customer Login Form
    document.getElementById("customer-login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const account_number = document.getElementById("cust-acc").value;
        const pin = document.getElementById("cust-pin").value;
        
        try {
            const response = await fetch(`${API_BASE}/api/auth/customer/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ account_number, pin })
            });
            const data = await response.json();
            if (response.ok) {
                currentSession.role = 'customer';
                currentSession.accountNumber = data.user.account_number;
                currentSession.name = `${data.user.first_name} ${data.user.last_name}`;
                
                document.getElementById("cust-profile-name").textContent = currentSession.name;
                document.getElementById("cust-profile-acc").textContent = `Acc: ${data.user.account_number}`;
                showToast(data.message, "success");
                switchView("customer-dashboard-view");
                switchCustomerTab("overview");
            } else {
                showToast(data.message, "error");
            }
        } catch (err) {
            showToast("Login server failed.", "error");
        }
    });

    // 4. Admin: Open Account Form
    document.getElementById("open-account-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            first_name: document.getElementById("open-first-name").value,
            last_name: document.getElementById("open-last-name").value,
            pin: document.getElementById("open-pin").value,
            account_type: document.getElementById("open-type").value,
            initial_balance: parseFloat(document.getElementById("open-balance").value) || 0,
            email: document.getElementById("open-email").value || null,
            phone: document.getElementById("open-phone").value || null,
            address: document.getElementById("open-address").value || null
        };
        
        try {
            const response = await fetch(`${API_BASE}/api/admin/accounts`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (response.ok) {
                showToast(`Account successfully opened: Number ${data.account_number}!`, "success");
                document.getElementById("open-account-form").reset();
                switchAdminTab("view-accounts");
            } else {
                showToast(data.message, "error");
            }
        } catch (err) {
            showToast("Failed to create customer account.", "error");
        }
    });

    // 5. Admin: Edit Form Submit
    document.getElementById("edit-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const accNum = document.getElementById("edit-acc-num").value;
        const payload = {
            email: document.getElementById("edit-email").value || null,
            phone: document.getElementById("edit-phone").value || null,
            address: document.getElementById("edit-address").value || null
        };
        
        try {
            const response = await fetch(`${API_BASE}/api/admin/accounts/${accNum}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (response.ok) {
                showToast("Account details updated successfully!", "success");
                closeModal("edit-modal");
                loadAdminAccounts();
            } else {
                showToast(data.message, "error");
            }
        } catch (err) {
            showToast("Update failed.", "error");
        }
    });

    // 6. Admin: Change Status Submit
    document.getElementById("status-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const accNum = document.getElementById("status-acc-num").value;
        const status = document.getElementById("status-select").value;
        
        try {
            const response = await fetch(`${API_BASE}/api/admin/accounts/${accNum}/status`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status })
            });
            const data = await response.json();
            if (response.ok) {
                showToast(data.message, "success");
                closeModal("status-modal");
                loadAdminAccounts();
            } else {
                showToast(data.message, "error");
            }
        } catch (err) {
            showToast("Failed to update status.", "error");
        }
    });

    // 7. Customer: Deposit Submit
    document.getElementById("cust-deposit-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const amount = parseFloat(document.getElementById("deposit-amount").value);
        if (isNaN(amount) || amount <= 0) return;
        
        try {
            const response = await fetch(`${API_BASE}/api/customer/accounts/${currentSession.accountNumber}/deposit`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ amount })
            });
            const data = await response.json();
            if (response.ok) {
                showToast(data.message, "success");
                document.getElementById("cust-deposit-form").reset();
                switchCustomerTab("overview");
            } else {
                showToast(data.message, "error");
            }
        } catch (err) {
            showToast("Deposit transaction failed.", "error");
        }
    });

    // 8. Customer: Withdraw Submit
    document.getElementById("cust-withdraw-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const amount = parseFloat(document.getElementById("withdraw-amount").value);
        if (isNaN(amount) || amount <= 0) return;
        
        try {
            const response = await fetch(`${API_BASE}/api/customer/accounts/${currentSession.accountNumber}/withdraw`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ amount })
            });
            const data = await response.json();
            if (response.ok) {
                showToast(data.message, "success");
                document.getElementById("cust-withdraw-form").reset();
                switchCustomerTab("overview");
            } else {
                showToast(data.message, "error");
            }
        } catch (err) {
            showToast("Withdrawal transaction failed.", "error");
        }
    });

    // 9. Customer: Transfer Submit
    document.getElementById("cust-transfer-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const receiver_account = document.getElementById("transfer-recipient").value;
        const amount = parseFloat(document.getElementById("transfer-amount").value);
        
        try {
            const response = await fetch(`${API_BASE}/api/customer/accounts/${currentSession.accountNumber}/transfer`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ receiver_account, amount })
            });
            const data = await response.json();
            if (response.ok) {
                showToast(data.message, "success");
                document.getElementById("cust-transfer-form").reset();
                switchCustomerTab("overview");
            } else {
                showToast(data.message, "error");
            }
        } catch (err) {
            showToast("Transfer failed.", "error");
        }
    });

    // 10. Customer: Change PIN Submit
    document.getElementById("cust-pin-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const old_pin = document.getElementById("pin-old").value;
        const new_pin = document.getElementById("pin-new").value;
        
        try {
            const response = await fetch(`${API_BASE}/api/customer/accounts/${currentSession.accountNumber}/pin`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ old_pin, new_pin })
            });
            const data = await response.json();
            if (response.ok) {
                showToast(data.message, "success");
                document.getElementById("cust-pin-form").reset();
                switchCustomerTab("overview");
            } else {
                showToast(data.message, "error");
            }
        } catch (err) {
            showToast("PIN change failed.", "error");
        }
    });
}

// Log out user session
function logout() {
    currentSession = { role: null, username: null, accountNumber: null, name: null };
    document.getElementById("admin-login-form").reset();
    document.getElementById("customer-login-form").reset();
    switchView("portal-view");
    showToast("Logged out successfully.", "success");
}

// --- ADMIN SIDE PANEL ACTIONS ---

async function loadAdminAccounts() {
    const tbody = document.getElementById("admin-accounts-tbody");
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center"><i class="fa-solid fa-spinner fa-spin"></i> Loading accounts registry...</td></tr>`;
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/accounts`);
        const data = await response.json();
        renderAccountsTable(data.accounts);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--danger)">Failed to load accounts.</td></tr>`;
    }
}

async function handleAdminSearch(val) {
    const tbody = document.getElementById("admin-accounts-tbody");
    try {
        const response = await fetch(`${API_BASE}/api/admin/accounts/search?q=${encodeURIComponent(val)}`);
        const data = await response.json();
        renderAccountsTable(data.accounts);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--danger)">Search error.</td></tr>`;
    }
}

function renderAccountsTable(accounts) {
    const tbody = document.getElementById("admin-accounts-tbody");
    if (!accounts || accounts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-secondary)">No accounts found.</td></tr>`;
        return;
    }
    
    tbody.innerHTML = "";
    accounts.forEach(acc => {
        let statusBadge = `<span class="badge active-badge">Active</span>`;
        if (acc.status === "Suspended") statusBadge = `<span class="badge suspended-badge">Suspended</span>`;
        if (acc.status === "Closed") statusBadge = `<span class="badge closed-badge">Closed</span>`;
        
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${acc.account_number}</strong></td>
            <td>${acc.first_name} ${acc.last_name}</td>
            <td>${acc.account_type}</td>
            <td><strong>$${parseFloat(acc.balance).toFixed(2)}</strong></td>
            <td>${statusBadge}</td>
            <td>${acc.created_at}</td>
            <td>
                <div class="action-btn-group">
                    <button class="action-btn edit" onclick="openEditModal('${acc.account_number}')" title="Edit Profile"><i class="fa-solid fa-pen-to-square"></i></button>
                    <button class="action-btn status" onclick="openStatusModal('${acc.account_number}', '${acc.status}')" title="Modify Status"><i class="fa-solid fa-toggle-on"></i></button>
                    <button class="action-btn close-acc" onclick="openCloseModal('${acc.account_number}')" title="Close Account"><i class="fa-solid fa-user-slash"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Modal open/close utilities
function openModal(id) {
    document.getElementById(id).classList.remove("hidden");
}
function closeModal(id) {
    document.getElementById(id).classList.add("hidden");
}

// Open modals callbacks
async function openEditModal(accountNumber) {
    try {
        const response = await fetch(`${API_BASE}/api/customer/accounts/${accountNumber}`);
        const data = await response.json();
        
        if (data.success) {
            // Pull specific fields
            const responseAll = await fetch(`${API_BASE}/api/admin/accounts/search?q=${accountNumber}`);
            const dataAll = await responseAll.json();
            // In search response, details are parsed. Wait, we can fetch email/phone/address from full database row
            // The customer accounts endpoint fetches email details if we query. Let's make it fetch details from search.
            const fullAcc = dataAll.accounts.find(a => a.account_number === accountNumber);
            
            document.getElementById("edit-acc-num").value = accountNumber;
            document.getElementById("edit-email").value = fullAcc.email || "";
            document.getElementById("edit-phone").value = fullAcc.phone || "";
            document.getElementById("edit-address").value = fullAcc.address || "";
            openModal("edit-modal");
        }
    } catch (e) {
        showToast("Failed to fetch details for edit.", "error");
    }
}

function openStatusModal(accountNumber, currentStatus) {
    document.getElementById("status-acc-num").value = accountNumber;
    document.getElementById("status-select").value = currentStatus;
    openModal("status-modal");
}

function openCloseModal(accountNumber) {
    document.getElementById("close-acc-num").value = accountNumber;
    document.getElementById("close-acc-num-label").textContent = accountNumber;
    openModal("close-modal");
}

// Execute closure calls
async function confirmAccountClosure(type) {
    const accNum = document.getElementById("close-acc-num").value;
    try {
        const response = await fetch(`${API_BASE}/api/admin/accounts/${accNum}?type=${type}`, {
            method: "DELETE"
        });
        const data = await response.json();
        if (response.ok) {
            showToast(data.message, "success");
            closeModal("close-modal");
            loadAdminAccounts();
        } else {
            showToast(data.message, "error");
        }
    } catch (err) {
        showToast("Error closing account.", "error");
    }
}

// Load Global Ledger Logs
async function loadAdminLedger() {
    const tbody = document.getElementById("admin-ledger-tbody");
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center"><i class="fa-solid fa-spinner fa-spin"></i> Fetching transaction records...</td></tr>`;
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/ledger`);
        const data = await response.json();
        
        if (!data.ledger || data.ledger.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-secondary)">No transaction logs present.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = "";
        data.ledger.forEach(tx => {
            let typeColor = "";
            if (tx.transaction_type === "Deposit" || tx.transaction_type === "Transfer In") {
                typeColor = "tx-credit";
            } else {
                typeColor = "tx-debit";
            }
            
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${tx.transaction_id}</strong></td>
                <td>${tx.account_number}</td>
                <td><span class="${typeColor}">${tx.transaction_type}</span></td>
                <td><strong>$${parseFloat(tx.amount).toFixed(2)}</strong></td>
                <td>${tx.target_account || "N/A"}</td>
                <td>${tx.description || ""}</td>
                <td>${tx.created_at}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--danger)">Failed to load transaction ledger.</td></tr>`;
    }
}

// --- CUSTOMER PORTAL ACTIONS ---

async function loadCustomerOverview() {
    const accNum = currentSession.accountNumber;
    try {
        const response = await fetch(`${API_BASE}/api/customer/accounts/${accNum}`);
        const data = await response.json();
        
        if (data.success) {
            const acc = data.account;
            document.getElementById("cust-balance-display").textContent = `$${parseFloat(acc.balance).toFixed(2)}`;
            
            const badge = document.getElementById("cust-status-badge");
            badge.textContent = acc.status;
            badge.className = "badge";
            if (acc.status === "Active") badge.classList.add("active-badge");
            if (acc.status === "Suspended") badge.classList.add("suspended-badge");
            if (acc.status === "Closed") badge.classList.add("closed-badge");
            
            document.getElementById("cust-type-display").textContent = acc.account_type;
            
            // Load recent activities
            loadCustomerRecentActivity();
        }
    } catch (err) {
        showToast("Failed to refresh balance.", "error");
    }
}

async function loadCustomerRecentActivity() {
    const accNum = currentSession.accountNumber;
    const tbody = document.getElementById("cust-recent-tbody");
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center"><i class="fa-solid fa-spinner fa-spin"></i> Refreshing activity...</td></tr>`;
    
    try {
        const response = await fetch(`${API_BASE}/api/customer/accounts/${accNum}/statement`);
        const data = await response.json();
        
        if (!data.statement || data.statement.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-secondary)">No activity recorded.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = "";
        // Show up to 5 elements
        const recent = data.statement.slice(0, 5);
        recent.forEach(tx => {
            let typeColor = "";
            let targetLabel = tx.target_account || "Self";
            if (tx.transaction_type === "Deposit" || tx.transaction_type === "Transfer In") {
                typeColor = "tx-credit";
            } else {
                typeColor = "tx-debit";
            }
            
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${tx.transaction_id}</strong></td>
                <td><span class="${typeColor}">${tx.transaction_type}</span></td>
                <td><strong>$${parseFloat(tx.amount).toFixed(2)}</strong></td>
                <td>${targetLabel}</td>
                <td>${tx.description || ""}</td>
                <td>${tx.created_at}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--danger)">Failed to retrieve activity.</td></tr>`;
    }
}

async function loadCustomerStatement() {
    const accNum = currentSession.accountNumber;
    const tbody = document.getElementById("cust-statement-tbody");
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center"><i class="fa-solid fa-spinner fa-spin"></i> Retreiving transaction statement...</td></tr>`;
    
    try {
        const response = await fetch(`${API_BASE}/api/customer/accounts/${accNum}/statement`);
        const data = await response.json();
        
        if (!data.statement || data.statement.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-secondary)">No transaction history found.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = "";
        data.statement.forEach(tx => {
            let typeColor = "";
            let targetLabel = tx.target_account || "Self";
            if (tx.transaction_type === "Deposit" || tx.transaction_type === "Transfer In") {
                typeColor = "tx-credit";
            } else {
                typeColor = "tx-debit";
            }
            
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${tx.transaction_id}</strong></td>
                <td><span class="${typeColor}">${tx.transaction_type}</span></td>
                <td><strong>$${parseFloat(tx.amount).toFixed(2)}</strong></td>
                <td>${targetLabel}</td>
                <td>${tx.description || ""}</td>
                <td>${tx.created_at}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--danger)">Failed to load transaction statement.</td></tr>`;
    }
}

// Toast Notifications Functionality
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let icon = "fa-circle-info";
    if (type === "success") icon = "fa-circle-check";
    if (type === "error") icon = "fa-triangle-exclamation";
    
    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto remove toast
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}
