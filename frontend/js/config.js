const CONFIG = {
  API_URL: "https://smart-cafe-api.onrender.com",

  SUPABASE_URL:      "https://efgaigfrisamqzdwhdfe.supabase.co",
  SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVmZ2FpZ2ZyaXNhbXF6ZHdoZGZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0MjA3ODUsImV4cCI6MjA4ODk5Njc4NX0.0EFkmdBd-ibWutD-2whdtwd7XoYwwLb9d-j0px0TVbM",

  ADMIN_TOKEN: "cafe-admin-9X3kP2Lm74SecureToken",

  CLOUDINARY_CLOUD_NAME:    "dufeizdnb",
  CLOUDINARY_UPLOAD_PRESET: "cafe_menu_images",

  TAX_RATE:        0.09,
  CURRENCY_SYMBOL: "₹",
  CAFE_NAME:       "Smart Cafe",
  CAFE_PHONE:      "+91 98765 43210",
};

// ── Realtime helpers (Supabase JS CDN) ───────────────────────────
// Call this in any page that needs live updates:
//   const channel = subscribeToOrders(orderId, (payload) => { ... });
//   channel.unsubscribe();  // cleanup on page leave

function getSupabaseClient() {
  if (typeof window.supabase !== "undefined") {
    return window.supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);
  }
  return null;
}

function subscribeToOrders(orderId, onChange) {
  const client = getSupabaseClient();
  if (!client) return null;
  return client
    .channel(`order-${orderId}`)
    .on("postgres_changes", {
      event:  "UPDATE",
      schema: "public",
      table:  "orders",
      filter: `id=eq.${orderId}`,
    }, onChange)
    .subscribe();
}

function subscribeToKitchenOrders(onChange) {
  const client = getSupabaseClient();
  if (!client) return null;
  return client
    .channel("kitchen-orders")
    .on("postgres_changes", {
      event:  "*",
      schema: "public",
      table:  "orders",
    }, onChange)
    .subscribe();
}

function subscribeToTables(onChange) {
  const client = getSupabaseClient();
  if (!client) return null;
  return client
    .channel("tables-status")
    .on("postgres_changes", {
      event:  "UPDATE",
      schema: "public",
      table:  "tables",
    }, onChange)
    .subscribe();
}

// ── API helper with auth ──────────────────────────────────────────
async function apiCall(path, options = {}) {
  const token = sessionStorage.getItem("adminToken") || CONFIG.ADMIN_TOKEN;
  const defaults = {
    headers: {
      "Content-Type": "application/json",
      "x-admin-token": token,
      ...options.headers,
    },
  };
  const response = await fetch(`${CONFIG.API_URL}${path}`, { ...defaults, ...options });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || `API error ${response.status}`);
  }
  return response.json();
}

// ── Toast notifications ───────────────────────────────────────────
function showToast(message, type = "") {
  let container = document.getElementById("toastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastContainer";
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── Format currency ───────────────────────────────────────────────
function formatCurrency(amount) {
  return `${CONFIG.CURRENCY_SYMBOL}${parseFloat(amount || 0).toFixed(2)}`;
}

// ── Format date ───────────────────────────────────────────────────
function formatDate(dateStr) {
  return new Date(dateStr).toLocaleString("en-IN", {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}