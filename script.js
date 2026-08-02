const API_BASE = "";

let currentMode = "ask";
let uploadedFilename = null;
let currentAuthTab = "login";

const authScreen = document.getElementById("authScreen");
const mainApp = document.getElementById("mainApp");
const authUsername = document.getElementById("authUsername");
const authPassword = document.getElementById("authPassword");
const authSubmitBtn = document.getElementById("authSubmitBtn");
const authStatus = document.getElementById("authStatus");
const authTabs = document.querySelectorAll(".auth-tab");
const welcomeUser = document.getElementById("welcomeUser");
const logoutBtn = document.getElementById("logoutBtn");

const pdfInput = document.getElementById("pdfInput");
const uploadBtn = document.getElementById("uploadBtn");
const uploadStatus = document.getElementById("uploadStatus");
const chatWindow = document.getElementById("chatWindow");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const docList = document.getElementById("docList");
const newChatBtn = document.getElementById("newChatBtn");

authTabs.forEach(tab => {
  tab.addEventListener("click", () => {
    authTabs.forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    currentAuthTab = tab.dataset.tab;
    authSubmitBtn.textContent = currentAuthTab === "login" ? "Log In" : "Sign Up";
    authStatus.textContent = "";
  });
});

authSubmitBtn.addEventListener("click", async () => {
  const username = authUsername.value.trim();
  const password = authPassword.value;

  if (!username || !password) {
    authStatus.textContent = "Please enter a username and password.";
    return;
  }

  const endpoint = currentAuthTab === "login" ? "/api/login" : "/api/signup";
  authStatus.textContent = currentAuthTab === "login" ? "Logging in..." : "Creating account...";

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (!res.ok) {
      authStatus.textContent = data.error || "Something went wrong.";
      return;
    }

    showMainApp(data.username);
  } catch (err) {
    authStatus.textContent = `Error: ${err.message}`;
  }
});

logoutBtn.addEventListener("click", async () => {
  await fetch(`${API_BASE}/api/logout`, { method: "POST", credentials: "include" });
  location.reload();
});

function showMainApp(username) {
  authScreen.style.display = "none";
  mainApp.style.display = "flex";
  welcomeUser.textContent = username;
  loadDocumentSidebar(true);
}

async function checkLoginStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/me`, { credentials: "include" });
    const data = await res.json();

    if (data.logged_in) {
      showMainApp(data.username);
    } else {
      authScreen.style.display = "block";
      mainApp.style.display = "none";
    }
  } catch (err) {
    console.log("Could not check login status:", err.message);
  }
}

uploadBtn.addEventListener("click", async () => {
  const file = pdfInput.files[0];
  if (!file) {
    uploadStatus.textContent = "Please choose a PDF first.";
    return;
  }

  uploadStatus.textContent = "Uploading and processing...";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API_BASE}/api/upload`, {
      method: "POST",
      credentials: "include",
      body: formData
    });
    const data = await res.json();

    if (!res.ok) {
      uploadStatus.textContent = `Error: ${data.error}`;
      return;
    }

    uploadedFilename = data.filename;
    uploadStatus.textContent =
      `Uploaded "${data.filename}" — ${data.num_chunks} chunks created (${data.num_characters} characters).`;
    resetChatWindow();
    loadDocumentSidebar(false);
  } catch (err) {
    uploadStatus.textContent = `Upload failed: ${err.message}. Is the backend running?`;
  }
});

const modeButtons = document.querySelectorAll(".mode-btn");
modeButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    modeButtons.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentMode = btn.dataset.mode;
  });
});

function addMessage(text, sender) {
  const msg = document.createElement("div");
  msg.classList.add("chat-message", sender);
  msg.textContent = text;
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

sendBtn.addEventListener("click", handleSend);
chatInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") handleSend();
  const emptyState = chatWindow.querySelector(".chat-empty");
  if (emptyState) emptyState.remove();
});

function resetChatWindow() {
  chatWindow.innerHTML = '<div class="chat-empty">Upload a PDF, then ask a question, request a summary, or generate a quiz.</div>';
}

async function handleSend() {
  const text = chatInput.value.trim();
  if (!text) return;

  if (!uploadedFilename) {
    addMessage("Please upload a PDF first, then ask your question.", "athena");
    return;
  }

  addMessage(text, "user");
  chatInput.value = "";

  addMessage("Thinking...", "athena");

  try {
    const res = await fetch(`${API_BASE}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        filename: uploadedFilename,
        mode: currentMode,
        question: text
      })
    });
    const data = await res.json();

    chatWindow.lastChild.remove();

    if (!res.ok) {
      addMessage(`Error: ${data.error || "Something went wrong."}`, "athena");
      return;
    }

    addMessage(data.answer, "athena");
  } catch (err) {
    chatWindow.lastChild.remove();
    addMessage(`Error: ${err.message}`, "athena");
  }
}

async function loadDocumentSidebar(autoRestoreLast) {
  try {
    const res = await fetch(`${API_BASE}/api/documents`, { credentials: "include" });
    const data = await res.json();

    if (!res.ok || !data.documents) {
      docList.innerHTML = `<div class="doc-list-empty">Could not load documents.</div>`;
      return;
    }

    renderDocList(data.documents);

    if (autoRestoreLast && data.documents.length > 0) {
      switchToDocument(data.documents[0].filename, data.documents[0].num_chunks, data.documents[0].num_characters);
    }
  } catch (err) {
    docList.innerHTML = `<div class="doc-list-empty">Error loading documents.</div>`;
  }
}

function renderDocList(documents) {
  if (documents.length === 0) {
    docList.innerHTML = `<div class="doc-list-empty">No documents yet. Upload one to get started.</div>`;
    return;
  }

  docList.innerHTML = "";
  documents.forEach(doc => {
    const item = document.createElement("div");
    item.classList.add("doc-item");
    if (doc.filename === uploadedFilename) item.classList.add("active");

    const nameSpan = document.createElement("span");
    nameSpan.classList.add("doc-item-name");
    nameSpan.textContent = doc.filename;
    nameSpan.title = doc.filename;

    const deleteBtn = document.createElement("button");
    deleteBtn.classList.add("doc-delete-btn");
    deleteBtn.textContent = "✕";
    deleteBtn.title = "Delete this document and its chat history";

    nameSpan.addEventListener("click", () => {
      switchToDocument(doc.filename, doc.num_chunks, doc.num_characters);
    });

    deleteBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm(`Delete "${doc.filename}" and all its chat history? This can't be undone.`)) {
        return;
      }
      await deleteDocument(doc.filename);
    });

    item.appendChild(nameSpan);
    item.appendChild(deleteBtn);
    docList.appendChild(item);
  });
}

async function switchToDocument(filename, numChunks, numCharacters) {
  uploadedFilename = filename;
  uploadStatus.textContent = `Now chatting with "${filename}" — ${numChunks} chunks (${numCharacters} characters).`;
  resetChatWindow();

  document.querySelectorAll(".doc-item").forEach(el => el.classList.remove("active"));

  try {
    const historyRes = await fetch(`${API_BASE}/api/history?filename=${encodeURIComponent(filename)}`, {
      credentials: "include"
    });
    const historyData = await historyRes.json();

    if (historyRes.ok && historyData.history) {
      historyData.history.forEach(entry => {
        addMessage(entry.question, "user");
        addMessage(entry.answer, "athena");
      });
    }
  } catch (err) {
    console.log("Could not load history:", err.message);
  }

  loadDocumentSidebar(false);
}

async function deleteDocument(filename) {
  try {
    const res = await fetch(`${API_BASE}/api/documents/${encodeURIComponent(filename)}`, {
      method: "DELETE",
      credentials: "include"
    });

    if (!res.ok) {
      const data = await res.json();
      alert(`Could not delete: ${data.error || "unknown error"}`);
      return;
    }

    if (uploadedFilename === filename) {
      uploadedFilename = null;
      resetChatWindow();
      uploadStatus.textContent = "Document deleted. Upload a new one or pick another from the sidebar.";
    }

    loadDocumentSidebar(false);
  } catch (err) {
    alert(`Error deleting document: ${err.message}`);
  }
}

checkLoginStatus();

// --- New Chat: clear the view so the user can upload a fresh document ---
newChatBtn.addEventListener("click", () => {
  uploadedFilename = null;
  resetChatWindow();
  uploadStatus.textContent = "Upload a new PDF to start a fresh chat.";
  pdfInput.value = "";
  document.querySelectorAll(".doc-item").forEach(el => el.classList.remove("active"));
  pdfInput.scrollIntoView({ behavior: "smooth", block: "center" });
});