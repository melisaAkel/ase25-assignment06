function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

async function jsonFetch(url, options = {}) {
  const res = await fetch(url, options);
  let data = null;
  try { data = await res.json(); } catch { data = null; }
  return { ok: res.ok, status: res.status, data };
}

function setCurrentEmail(email) { localStorage.setItem("currentEmail", email); }
function getCurrentEmail() { return localStorage.getItem("currentEmail") || ""; }
function setCurrentRole(role) { localStorage.setItem("currentRole", role || ""); }
function getCurrentRole() { return localStorage.getItem("currentRole") || ""; }

function openOverlay(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = "flex";
}
function closeOverlay(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = "none";
}

function isPast(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return false;
  return d.getTime() < Date.now();
}

// -------------------------
// Auth APIs
// -------------------------
async function apiLogin(email, password) {
  return await jsonFetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

async function apiRegister(email, password) {
  return await jsonFetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

async function apiVerify(email, code) {
  return await jsonFetch("/api/auth/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code }),
  });
}

// -------------------------
// Rooms
// -------------------------
async function apiRooms() { return await jsonFetch("/api/rooms"); }
async function apiMeRoom(email) { return await jsonFetch(`/api/me/room?email=${encodeURIComponent(email)}`); }
async function apiJoinRoom(roomId, email) {
  return await jsonFetch(`/api/rooms/${roomId}/join`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}
async function apiLeaveRoom(email) {
  return await jsonFetch("/api/rooms/leave", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}
async function apiRoomsOpen() { return await jsonFetch("/api/settings/rooms_open"); }


// -------------------------
// Events
// -------------------------
async function apiEvents(page, pageSize) {
  return await jsonFetch(`/api/events?page=${page}&page_size=${pageSize}`);
}
async function apiRegisterEvent(eventId, email) {
  return await jsonFetch(`/api/events/${eventId}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}
async function apiLeaveEvent(eventId, email) {
  return await jsonFetch(`/api/events/${eventId}/leave`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}
async function apiMyRegisteredEvents(email) {
  return await jsonFetch(`/api/me/events?email=${encodeURIComponent(email)}`);
}

// -------------------------
// Event Requests
// -------------------------
async function apiMyEventRequests(email) {
  return await jsonFetch(`/api/event-requests?email=${encodeURIComponent(email)}`);
}
async function apiCreateEventRequest(payload) {
  return await jsonFetch("/api/event-requests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
async function apiHideEventRequest(id, email) {
  return await jsonFetch(`/api/event-requests/${id}/hide`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}

// -------------------------
// Admin APIs
// -------------------------
async function apiAdminEventRequests(adminEmail, status) {
  return await jsonFetch(`/api/admin/event-requests?admin_email=${encodeURIComponent(adminEmail)}&status=${encodeURIComponent(status)}`);
}
async function apiAdminDecision(adminEmail, reqId, action, comment) {
  return await jsonFetch(`/api/admin/event-requests/${reqId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ admin_email: adminEmail, action, comment }),
  });
}
async function apiAdminRooms(adminEmail) {
  return await jsonFetch(`/api/admin/rooms?admin_email=${encodeURIComponent(adminEmail)}`);
}
async function apiAdminRoomStudents(adminEmail, roomId) {
  return await jsonFetch(`/api/admin/rooms/${roomId}/students?admin_email=${encodeURIComponent(adminEmail)}`);
}
async function apiAdminEvents(adminEmail) {
  return await jsonFetch(`/api/admin/events?admin_email=${encodeURIComponent(adminEmail)}`);
}
async function apiAdminEventStudents(adminEmail, eventId) {
  return await jsonFetch(`/api/admin/events/${eventId}/students?admin_email=${encodeURIComponent(adminEmail)}`);
}
async function doLogout() {
  await apiLogout();
  localStorage.removeItem("currentEmail");
  localStorage.removeItem("currentRole");
  window.location.href = "/login";
}
async function apiLogout() {
  return await jsonFetch("/api/auth/logout", { method: "POST" });
}


// -------------------------
// Info
// -------------------------
async function apiInfo(slug) {
  return await jsonFetch("/api/info/" + encodeURIComponent(slug));
}

// -------------------------
// Login page
// -------------------------
function initLoginPage() {
  const loginBtn = document.getElementById("loginBtn");
  if (!loginBtn) return;

  loginBtn.addEventListener("click", async () => {
    setText("loginMsg", "Logging in...");
    const email = (document.getElementById("loginEmail").value || "").trim().toLowerCase();
    const password = (document.getElementById("loginPassword").value || "").trim();

    const r = await apiLogin(email, password);
    if (r.ok) {
      setCurrentEmail(r.data.email || email);
      setCurrentRole(r.data.role || "");

      // IMPORTANT: role based redirect
      if ((r.data.role || "") === "admin") {
        setText("loginMsg", "Login successful. Redirecting to Admin...");
        window.location.href = "/admin";
      } else {
        setText("loginMsg", "Login successful. Redirecting to Rooms...");
        window.location.href = "/rooms";
      }
    } else {
      setText("loginMsg", (r.data && r.data.error) ? r.data.error : "Login failed.");
    }
  });
}
function initNavAdminButton() {
  const adminBtn = document.getElementById("adminBtn");
  if (!adminBtn) return; // if the current page doesn't have the button

  const email = getCurrentEmail();
  const role = getCurrentRole();

  // only show for admins
  adminBtn.style.display = (role === "admin") ? "inline-block" : "none";

  adminBtn.onclick = () => {
    if (!email || role !== "admin") {
      window.location.href = "/login";
      return;
    }
    window.location.href = "/admin";
  };
}


// -------------------------
// Register page
// -------------------------


// -------------------------
// Verify page
// -------------------------
function initVerifyPage() {
  const btn = document.getElementById("verifyBtn");
  if (!btn) return;

  const saved = getCurrentEmail();
  const emailEl = document.getElementById("verEmail");
  if (emailEl && saved) emailEl.value = saved;

  btn.addEventListener("click", async () => {
    const email = (document.getElementById("verEmail").value || "").trim().toLowerCase();
    const code = (document.getElementById("verCode").value || "").trim();

    setText("verifyMsg", "Verifying...");
    const r = await apiVerify(email, code);

    if (r.ok) {
      setText("verifyMsg", "Verified. You can login now.");
      window.location.href = "/login";
    } else {
      setText("verifyMsg", (r.data && r.data.error) ? r.data.error : "Verification failed.");
    }
  });
}

// -------------------------
// Rooms page
// -------------------------
async function initRoomsPage() {

  const roomsContainer = document.getElementById("roomsContainer");
  if (!roomsContainer) return;

  const email = getCurrentEmail();
if (!email) { window.location.href = "/login"; return; }


  const lockMsgEl = document.getElementById("roomsLockMsg");
  if (lockMsgEl) {
    const ro = await apiRoomsOpen();
    if (ro.ok && ro.data && typeof ro.data.open === "boolean") {
      lockMsgEl.textContent = ro.data.open
        ? "Room selection is currently OPEN."
        : "Room selection is currently CLOSED by admin.";
    } else {
      lockMsgEl.textContent = "";
    }
  }

  const myRoomCard = document.getElementById("myRoomCard");
  const myRoomDetails = document.getElementById("myRoomDetails");
  const leaveBtn = document.getElementById("leaveRoomBtn");

  if (myRoomCard && myRoomDetails && leaveBtn) {
    const mr = await apiMeRoom(email);
    if (mr.ok && mr.data && mr.data.room) {
      myRoomCard.style.display = "block";
      myRoomDetails.innerHTML =
        `<strong>${mr.data.room.title}</strong><br>` +
        `Type: ${mr.data.room.type}<br>` +
        `Price: €${mr.data.room.price_eur}<br>` +
        `Capacity: ${mr.data.room.capacity}`;
    } else {
      myRoomCard.style.display = "none";
    }

    leaveBtn.onclick = async () => {
      setText("leaveRoomMsg", "Leaving room...");
      const lr = await apiLeaveRoom(email);
      if (lr.ok) {
        setText("leaveRoomMsg", "Left room.");
        await initRoomsPage();
      } else {
        setText("leaveRoomMsg", (lr.data && lr.data.error) ? lr.data.error : "Failed to leave.");
      }
    };
  }

  roomsContainer.textContent = "Loading rooms...";
  const r = await apiRooms();
  if (!r.ok) {
    roomsContainer.textContent = (r.data && r.data.error) ? r.data.error : "Failed to load rooms.";
    return;
  }

  const rooms = [...r.data];
  rooms.sort((a, b) => (a.is_full ? 1 : 0) - (b.is_full ? 1 : 0) || (a.id - b.id));

  roomsContainer.innerHTML = "";
  for (const room of rooms) {
    const card = document.createElement("div");
    card.className = "card";
    if (room.is_full) card.classList.add("is-full");

    card.innerHTML = `
      <h3>${room.title}</h3>
      <p><strong>Type:</strong> ${room.type}</p>
      <p><strong>Price:</strong> €${room.price_eur}</p>
      <p><strong>Quota:</strong> ${room.booked_count}/${room.capacity} booked (remaining: ${room.remaining})</p>
      <p>${room.description}</p>
      <button class="join-room-btn" data-room-id="${room.id}" ${room.is_full ? "disabled" : ""}>
        ${room.is_full ? "Full" : "Join room"}
      </button>
      <p class="msg" id="roomMsg-${room.id}"></p>
    `;
    roomsContainer.appendChild(card);
  }

  roomsContainer.querySelectorAll(".join-room-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const roomId = btn.getAttribute("data-room-id");
      const msgId = `roomMsg-${roomId}`;

      setText(msgId, "Joining...");
      const jr = await apiJoinRoom(roomId, email);
      if (jr.ok) {
        setText(msgId, "Joined successfully.");
        await initRoomsPage();
      } else {
        setText(msgId, (jr.data && jr.data.error) ? jr.data.error : "Failed to join.");
      }
    });
  });
}

// -------------------------
// Events page
// -------------------------
const EVENTS_PAGE_SIZE = 4;
let currentEventsPage = 1;

async function renderMyRegisteredEvents() {
  const container = document.getElementById("myRegisteredEventsContainer");
  if (!container) return;

  const email = getCurrentEmail();
  if (!email) {
    container.textContent = "No logged-in email found.";
    return;
  }

  container.textContent = "Loading your registered events...";
  const r = await apiMyRegisteredEvents(email);
  if (!r.ok) {
    container.textContent = (r.data && r.data.error) ? r.data.error : "Failed to load your registered events.";
    return;
  }

  const items = r.data || [];
  container.innerHTML = "";

  if (items.length === 0) {
    container.innerHTML = `<div class="card"><p class="small">You have not registered for any events yet.</p></div>`;
    return;
  }

  for (const ev of items) {
    const card = document.createElement("div");
    card.className = "card";
    if (ev.is_full) card.classList.add("is-full");
    if (isPast(ev.date_time)) card.classList.add("is-past");

    const quotaText = (ev.quota === null)
      ? `${ev.registered_count} registered (unlimited)`
      : `${ev.registered_count}/${ev.quota} registered (remaining: ${ev.remaining})`;

    card.innerHTML = `
      <h3>${ev.title}</h3>
      <p><strong>Date/Time:</strong> ${ev.date_time}</p>
      <p><strong>Location:</strong> ${ev.location}</p>
      <p><strong>Quota:</strong> ${quotaText}</p>
      <div class="btn-row">
        <button class="secondary leave-event-btn" data-event-id="${ev.id}">Leave event</button>
      </div>
      <p class="msg" id="myEvMsg-${ev.id}"></p>
    `;
    container.appendChild(card);
  }

  container.querySelectorAll(".leave-event-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const eventId = btn.getAttribute("data-event-id");
      setText(`myEvMsg-${eventId}`, "Leaving...");
      const lr = await apiLeaveEvent(eventId, getCurrentEmail());
      if (lr.ok) {
        setText(`myEvMsg-${eventId}`, "Left.");
        await renderMyRegisteredEvents();
        await renderEventsPage();
      } else {
        setText(`myEvMsg-${eventId}`, (lr.data && lr.data.error) ? lr.data.error : "Failed to leave.");
      }
    });
  });
}

async function renderEventsPage() {
  const container = document.getElementById("eventsContainer");
  if (!container) return;

  const email = getCurrentEmail();

  container.textContent = "Loading events...";
  const r = await apiEvents(currentEventsPage, EVENTS_PAGE_SIZE);

  if (!r.ok) {
    container.textContent = (r.data && r.data.error) ? r.data.error : "Failed to load events.";
    return;
  }

  const items = (r.data && r.data.items) ? r.data.items : [];
  const hasNext = !!(r.data && r.data.has_next);
  const hasPrev = !!(r.data && r.data.has_prev);

  items.sort((a, b) => {
    const ap = isPast(a.date_time) ? 1 : 0;
    const bp = isPast(b.date_time) ? 1 : 0;
    if (ap !== bp) return ap - bp;
    const af = a.is_full ? 1 : 0;
    const bf = b.is_full ? 1 : 0;
    if (af !== bf) return af - bf;
    return a.id - b.id;
  });

  container.innerHTML = "";
  for (const ev of items) {
    const card = document.createElement("div");
    card.className = "card";
    if (ev.is_full) card.classList.add("is-full");
    if (isPast(ev.date_time)) card.classList.add("is-past");

    const quotaText = (ev.quota === null)
      ? `${ev.registered_count} registered (unlimited)`
      : `${ev.registered_count}/${ev.quota} registered (remaining: ${ev.remaining})`;

    const registerDisabled = ev.is_full || isPast(ev.date_time) || !email;

    card.innerHTML = `
      <h3>${ev.title}</h3>
      <p><strong>Category:</strong> ${ev.category}</p>
      <p><strong>Date/Time:</strong> ${ev.date_time}</p>
      <p><strong>Location:</strong> ${ev.location}</p>
      <p><strong>Quota:</strong> ${quotaText}</p>
      <p>${ev.description}</p>
      <div class="btn-row">
        <button class="register-event-btn" data-event-id="${ev.id}" ${registerDisabled ? "disabled" : ""}>
          ${registerDisabled ? "Register unavailable" : "Register"}
        </button>
      </div>
      <p class="msg" id="eventMsg-${ev.id}"></p>
    `;
    container.appendChild(card);
  }

  container.querySelectorAll(".register-event-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const eventId = btn.getAttribute("data-event-id");
      setText(`eventMsg-${eventId}`, "Registering...");
      const rr = await apiRegisterEvent(eventId, getCurrentEmail());
      if (rr.ok) {
        setText(`eventMsg-${eventId}`, "Registered.");
        await renderMyRegisteredEvents();
        await renderEventsPage();
      } else {
        setText(`eventMsg-${eventId}`, (rr.data && rr.data.error) ? rr.data.error : "Failed to register.");
      }
    });
  });

  const prevBtn = document.getElementById("prevEventsBtn");
  const nextBtn = document.getElementById("nextEventsBtn");
  const info = document.getElementById("eventsPageInfo");
  if (prevBtn) prevBtn.disabled = !hasPrev;
  if (nextBtn) nextBtn.disabled = !hasNext;
  if (info) info.textContent = `Page ${currentEventsPage}`;

  if (prevBtn) prevBtn.onclick = async () => { if (currentEventsPage > 1) currentEventsPage -= 1; await renderEventsPage(); };
  if (nextBtn) nextBtn.onclick = async () => { currentEventsPage += 1; await renderEventsPage(); };
}

async function renderMyRequests() {
  const container = document.getElementById("myRequestsContainer");
  if (!container) return;

  const email = getCurrentEmail();
  if (!email) {
    container.textContent = "No logged-in email found. Please login first.";
    return;
  }

  container.textContent = "Loading your requests...";
  const r = await apiMyEventRequests(email);
  if (!r.ok) {
    container.textContent = (r.data && r.data.error) ? r.data.error : "Failed to load your requests.";
    return;
  }

  const items = r.data || [];
  container.innerHTML = "";

  for (const req of items) {
    const card = document.createElement("div");
    card.className = "card";

    const status = req.status;
    const canHide = (status === "accepted" || status === "rejected");

    const commentBlock = (status === "rejected" && req.admin_comment)
      ? `<p class="small"><strong>Admin comment:</strong> ${req.admin_comment}</p>`
      : "";

    const hideBtn = canHide
      ? `<button class="icon-btn hide-req-btn" data-req-id="${req.id}" title="Hide from my list">✕</button>`
      : `<span class="small">Pending (cannot remove)</span>`;

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; gap:10px; align-items:flex-start;">
        <div>
          <h3 style="margin-top:0;">${req.title}</h3>
          <p class="small"><strong>Status:</strong> ${status}</p>
          <p class="small"><strong>Last modified:</strong> ${req.updated_at}</p>
        </div>
        <div>${hideBtn}</div>
      </div>
      <p><strong>Date/Time:</strong> ${req.date_time}</p>
      <p><strong>Location:</strong> ${req.location}</p>
      <p><strong>Category:</strong> ${req.category}</p>
      <p>${req.description}</p>
      ${commentBlock}
      <p class="msg" id="reqMsg-${req.id}"></p>
    `;
    container.appendChild(card);
  }

  container.querySelectorAll(".hide-req-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-req-id");
      const email = getCurrentEmail();
      setText(`reqMsg-${id}`, "Hiding...");
      const hr = await apiHideEventRequest(id, email);
      if (hr.ok) {
        setText(`reqMsg-${id}`, "Hidden.");
        await renderMyRequests();
      } else {
        setText(`reqMsg-${id}`, (hr.data && hr.data.error) ? hr.data.error : "Failed to hide.");
      }
    });
  });
}

function initEventsPage() {
  const openBtn = document.getElementById("openRequestModalBtn");
  const closeBtn = document.getElementById("closeRequestModalBtn");
  const overlay = document.getElementById("requestModalOverlay");
  const submitBtn = document.getElementById("submitRequestBtn");


  if (!openBtn || !closeBtn || !overlay || !submitBtn) return;

  openBtn.onclick = () => { setText("requestModalMsg", ""); openOverlay("requestModalOverlay"); };
  closeBtn.onclick = () => closeOverlay("requestModalOverlay");
  overlay.addEventListener("click", (e) => { if (e.target === overlay) closeOverlay("requestModalOverlay"); });

  submitBtn.onclick = async () => {
    const email = getCurrentEmail();
  if (!email) { window.location.href = "/login"; return; }

    const title = (document.getElementById("reqTitle").value || "").trim();
    const category = (document.getElementById("reqCategory").value || "").trim();
    const date_time = (document.getElementById("reqDateTime").value || "").trim();
    const location = (document.getElementById("reqLocation").value || "").trim();
    const description = (document.getElementById("reqDescription").value || "").trim();
    const quotaRaw = (document.getElementById("reqQuota").value || "").trim();
    const quota = quotaRaw === "" ? null : Number(quotaRaw);

    if (!title || !category || !date_time || !location || !description) {
      setText("requestModalMsg", "Please fill all fields (quota optional).");
      return;
    }
    if (quota !== null && (Number.isNaN(quota) || quota < 0)) {
      setText("requestModalMsg", "Quota must be empty (unlimited) or a non-negative number.");
      return;
    }

    setText("requestModalMsg", "Submitting request...");
    const cr = await apiCreateEventRequest({ email, title, category, date_time, location, description, quota });
    if (cr.ok) {
      setText("requestModalMsg", "Request submitted (pending).");
      await renderMyRequests();
      closeOverlay("requestModalOverlay");
    } else {
      setText("requestModalMsg", (cr.data && cr.data.error) ? cr.data.error : "Failed to submit request.");
    }
  };

  renderEventsPage();
  renderMyRegisteredEvents();
  renderMyRequests();
}

// -------------------------
// Admin page (unchanged logic)
// -------------------------
let adminFilterStatus = "pending";

function setActiveChip(status) {
  const ids = { pending: "chipPending", accepted: "chipAccepted", rejected: "chipRejected" };
  Object.keys(ids).forEach((k) => {
    const el = document.getElementById(ids[k]);
    if (el) el.classList.toggle("active", k === status);
  });
}

async function renderAdminRequests() {
  const container = document.getElementById("adminRequestsContainer");
  if (!container) return;

  const adminEmail = getCurrentEmail();
  const role = getCurrentRole();

  if (role !== "admin") {
    setText("adminGuardMsg", "Admin access required. Login with admin account.");
    container.innerHTML = "";
    return;
  }

  setText("adminGuardMsg", `Logged in as admin: ${adminEmail}`);
  container.textContent = "Loading...";
  const r = await apiAdminEventRequests(adminEmail, adminFilterStatus);

  if (!r.ok) {
    container.textContent = (r.data && r.data.error) ? r.data.error : "Failed to load requests.";
    return;
  }

  const items = r.data || [];
  container.innerHTML = "";

  if (items.length === 0) {
    container.innerHTML = `<div class="card"><p class="small">No ${adminFilterStatus} requests.</p></div>`;
    return;
  }

  for (const req of items) {
    const card = document.createElement("div");
    card.className = "card";

    const quotaText = (req.quota === null) ? "unlimited" : String(req.quota);

    let actionsHtml = "";
    if (req.status === "pending") {
      actionsHtml = `
        <div class="btn-row">
          <button class="admin-accept-btn" data-id="${req.id}">Accept</button>
        </div>
        <label>Reject comment (required)</label>
        <textarea id="rejComment-${req.id}" placeholder="Reason for rejection..."></textarea>
        <div class="btn-row">
          <button class="secondary admin-reject-btn" data-id="${req.id}">Reject</button>
        </div>
      `;
    } else if (req.status === "rejected") {
      actionsHtml = `<p class="small"><strong>Admin comment:</strong> ${req.admin_comment || ""}</p>`;
    } else {
      actionsHtml = `<p class="small">Accepted and published.</p>`;
    }

    card.innerHTML = `
      <h3 style="margin-top:0;">${req.title}</h3>
      <p class="small"><strong>Status:</strong> ${req.status}</p>
      <p class="small"><strong>Last modified:</strong> ${req.updated_at}</p>
      <p class="small"><strong>Requested by:</strong> ${req.requested_by_email}</p>
      <p><strong>Date/Time:</strong> ${req.date_time}</p>
      <p><strong>Location:</strong> ${req.location}</p>
      <p><strong>Category:</strong> ${req.category}</p>
      <p><strong>Quota:</strong> ${quotaText}</p>
      <p>${req.description}</p>
      ${actionsHtml}
      <p class="msg" id="adminReqMsg-${req.id}"></p>
    `;
    container.appendChild(card);
  }

  container.querySelectorAll(".admin-accept-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-id");
      setText(`adminReqMsg-${id}`, "Accepting...");
      const rr = await apiAdminDecision(getCurrentEmail(), id, "accept", "");
      if (rr.ok) {
        setText(`adminReqMsg-${id}`, "Accepted.");
        await renderAdminRequests();
      } else {
        setText(`adminReqMsg-${id}`, (rr.data && rr.data.error) ? rr.data.error : "Failed.");
      }
    });
  });

  container.querySelectorAll(".admin-reject-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-id");
      const comment = (document.getElementById(`rejComment-${id}`).value || "").trim();
      setText(`adminReqMsg-${id}`, "Rejecting...");
      const rr = await apiAdminDecision(getCurrentEmail(), id, "reject", comment);
      if (rr.ok) {
        setText(`adminReqMsg-${id}`, "Rejected.");
        await renderAdminRequests();
      } else {
        setText(`adminReqMsg-${id}`, (rr.data && rr.data.error) ? rr.data.error : "Failed.");
      }
    });
  });
}

function initAdminPage() {
  const container = document.getElementById("adminRequestsContainer");
  if (!container) return;

  const pending = document.getElementById("chipPending");
  const accepted = document.getElementById("chipAccepted");
  const rejected = document.getElementById("chipRejected");
  if (!pending || !accepted || !rejected) return;

  const setStatus = async (s) => {
    adminFilterStatus = s;
    setActiveChip(s);
    await renderAdminRequests();
  };

  pending.onclick = () => setStatus("pending");
  accepted.onclick = () => setStatus("accepted");
  rejected.onclick = () => setStatus("rejected");

  setActiveChip("pending");
  renderAdminRequests();
}

// -------------------------
// Info page
// -------------------------
async function initInfoPage() {
  const container = document.getElementById("infoContainer");
  if (!container) return;

  // If page is /info/<slug>, slug will be set.
  // If page is /info, we set INFO_SLUG="all" and load everything.
  const slug = (window.INFO_SLUG || "all").trim();

  // Load ALL sections
  if (slug === "all") {
    container.textContent = "Loading info...";
    const r = await jsonFetch("/api/info");
    if (!r.ok) {
      container.textContent = (r.data && r.data.error) ? r.data.error : "Failed to load info.";
      return;
    }

    const items = r.data || [];
    if (items.length === 0) {
      container.innerHTML = `<p>No info pages found.</p>`;
      return;
    }

    // Render as sections
    container.innerHTML = items.map(it => {
      const content = String(it.content || "").replace(/\n/g, "<br>");
      return `
        <section class="card" style="margin-bottom:16px;">
          <h2 id="${it.slug}">${it.title}</h2>
          <p>${content}</p>
        </section>
      `;
    }).join("");

    return;
  }

  // Load single section (old behavior)
  container.textContent = "Loading info...";
  const r = await apiInfo(slug);

  if (!r.ok) {
    container.textContent = (r.data && r.data.error) ? r.data.error : "Failed to load info.";
    return;
  }

  const content = (r.data.content || "").replace(/\n/g, "<br>");
  container.innerHTML = `
    <h2>${r.data.title}</h2>
    <p>${content}</p>
  `;
}


// -------------------------
// Demo Inbox page
// -------------------------
function initDemoInboxPage() {
  const fetchBtn = document.getElementById("demoFetchBtn");
  const verifyBtn = document.getElementById("demoVerifyBtn");
  if (!fetchBtn || !verifyBtn) return;

  const getEmail = () => (document.getElementById("demoEmail").value || "").trim().toLowerCase();

  fetchBtn.onclick = async () => {
    const email = getEmail();
    if (!email) { setText("demoMsg", "Enter an email."); return; }

    setText("demoMsg", "Loading...");
    const r = await jsonFetch(`/api/demo/verification-status?email=${encodeURIComponent(email)}`);

    const box = document.getElementById("demoCodeBox");
    if (!r.ok) {
      setText("demoMsg", (r.data && r.data.error) ? r.data.error : "Failed.");
      if (box) box.style.display = "none";
      return;
    }

    setText("demoMsg", "Pending verification found.");
    document.getElementById("demoCreatedAt").textContent = "Created at: " + r.data.created_at;
    document.getElementById("demoLastSentAt").textContent = "Last sent at: " + r.data.last_sent_at;
    if (box) box.style.display = "block";
  };

  verifyBtn.onclick = async () => {
    const email = getEmail();
    if (!email) { setText("demoMsg", "Enter an email."); return; }

    setText("demoMsg", "Verifying...");
    const r = await jsonFetch("/api/demo/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });

    if (!r.ok) {
      setText("demoMsg", (r.data && r.data.error) ? r.data.error : "Verify failed.");
      return;
    }

    setText("demoMsg", "Verified. You can now login.");
    // Optional: auto redirect
    // window.location.href = "/login";
  };
}


function initRegisterPage() {
  const btn = document.getElementById("registerBtn");
  if (!btn) return;

  btn.onclick = async () => {
    const email = (document.getElementById("regEmail").value || "").trim().toLowerCase();
    const password = (document.getElementById("regPassword").value || "").trim();

    setText("registerMsg", "Registering...");
    const r = await apiRegister(email, password);

    if (!r.ok) {
      setText("registerMsg", (r.data && r.data.error) ? r.data.error : "Registration failed.");
      return;
    }

    setText("registerMsg", "Created. Redirecting to Demo Inbox...");
    window.location.href = "/demo-inbox";
  };
}


// -------------------------
// Boot
// -------------------------
document.addEventListener("DOMContentLoaded", () => {
  initNavAdminButton();   // <-- ADD THIS LINE
  initLoginPage();
  initRegisterPage();
  initRoomsPage();
  initEventsPage();
  initAdminPage();
  initInfoPage();
  initDemoInboxPage();
});


