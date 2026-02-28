const API_BASE = window.location.protocol.startsWith("http")
  ? `${window.location.origin}/api`
  : "http://127.0.0.1:5000/api";

const moods = ["Sad", "Drained", "Excited", "Determined", "Overwhelmed", "Frustrated", "Nervous", "Okay"];

let selectedMood = "";
let currentLogId = null;

// 1. SELECTORS
const moodChoices = document.getElementById("moodChoices");
const afterMoodChoices = document.getElementById("afterMoodChoices");
const noteInput = document.getElementById("noteInput");
const statusText = document.getElementById("statusText");
const generateBtn = document.getElementById("generateBtn");
const quoteCard = document.getElementById("quoteCard");
const activityList = document.getElementById("activityList");
const afterMoodSection = document.getElementById("afterMoodSection");
const historyList = document.getElementById("historyList");
const refreshHistoryBtn = document.getElementById("refreshHistoryBtn");

// 2. MOOD PILL CREATION (Matches your .mood-pill CSS)
function createMoodPills(container, onSelect) {
  container.innerHTML = "";
  moods.forEach((mood) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mood-pill"; // Matches CSS
    button.textContent = mood;
    button.addEventListener("click", () => {
      container.querySelectorAll(".mood-pill").forEach(p => p.classList.remove("active"));
      button.classList.add("active");
      onSelect(mood);
    });
    container.appendChild(button);
  });
}

// 3. RECOMMENDATIONS & ILLUSTRATIONS (Matches your .activity CSS)
function renderRecommendations(data) {
  quoteCard.classList.remove("hidden");
  quoteCard.innerHTML = `
    <p>"${data.quote}"</p>
    <div class="author">- ${data.author}</div>
  `;

  activityList.innerHTML = "";
  (data.activities || []).forEach((activity) => {
    let imgName = "undraw_relaxing-outdoor.svg"; // Fallback
    const title = activity.title.toLowerCase();

    // Mapping keywords to your static/assets/illustrations folder
    if (title.includes("yoga") || title.includes("stretch")) imgName = "undraw_yoga_i399.svg";
    else if (title.includes("music") || title.includes("listen")) imgName = "undraw_dua_lipa_bc8o.svg";
    else if (title.includes("walk") || title.includes("park")) imgName = "undraw_a-day-at-the-park.svg";
    else if (title.includes("write") || title.includes("journal")) imgName = "undraw_writing-down.svg";
    else if (title.includes("call") || title.includes("friend")) imgName = "undraw_calling_ieh0.svg";
    else if (title.includes("book") || title.includes("read")) imgName = "undraw_book-lover_m9n3.svg";
    else if (title.includes("game")) imgName = "undraw_video-games_itxa.svg";
    else if (title.includes("coffee") || title.includes("drink")) imgName = "undraw_drink-coffee_q0ey.svg";

    const card = document.createElement("article");
    card.className = "activity"; // Matches CSS
    card.innerHTML = `
      <img src="/static/assets/illustrations/${imgName}" alt="Illustration">
      <h4>${activity.title}</h4>
      <p>${activity.description}</p>
      ${activity.type === "music_suggestion" ? '<span class="badge">Music Suggestion</span>' : ""}
    `;
    activityList.appendChild(card);
  });

  afterMoodSection.classList.remove("hidden");
}

// 4. API CALLS
async function onGenerate() {
  if (!selectedMood) {
    statusText.textContent = "Please select a mood first.";
    return;
  }

  try {
    generateBtn.disabled = true;
    statusText.textContent = "Consulting Aether...";

    // Save Log
    const logRes = await fetch(`${API_BASE}/logs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mood_before: selectedMood, note: noteInput.value })
    });
    const logData = await logRes.json();
    currentLogId = logData.id;

    // Get Recs
    const res = await fetch(`${API_BASE}/get_recommendations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mood: selectedMood, note: noteInput.value })
    });
    const data = await res.json();

    renderRecommendations(data);
    statusText.textContent = "";
    fetchHistory();
  } catch (e) {
    statusText.textContent = "Connection error. Is the server running?";
  } finally {
    generateBtn.disabled = false;
  }
}

async function fetchHistory() {
  const res = await fetch(`${API_BASE}/history`);
  const logs = await res.json();
  historyList.innerHTML = "";
  logs.forEach(log => {
    const item = document.createElement("div");
    item.className = "history-item"; // Matches CSS
    item.innerHTML = `<p><strong>${log.mood_before}</strong> → ${log.mood_after || '...'}</p><p class="subtitle">${log.note || ""}</p>`;
    historyList.appendChild(item);
  });
}

// 5. INITIALIZATION
generateBtn.addEventListener("click", onGenerate);
createMoodPills(moodChoices, (m) => selectedMood = m);
createMoodPills(afterMoodChoices, async (m) => {
    if (currentLogId) {
        await fetch(`${API_BASE}/logs/${currentLogId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mood_after: m })
        });
        fetchHistory();
    }
});
fetchHistory();

// --- SPLASH SCREEN LOGIC ---
window.addEventListener('load', () => {
    const splash = document.getElementById('splashScreen');
    const mainApp = document.getElementById('mainApp');

    // Wait 2 seconds so the user can actually see the "Aether" branding
    setTimeout(() => {
        if (splash) {
            splash.style.opacity = '0';
            // Wait for the fade-out transition to finish before removing from display
            setTimeout(() => {
                splash.style.display = 'none';
                if (mainApp) mainApp.classList.replace('opacity-0', 'opacity-100');
            }, 1000);
        }
    }, 2000);
});
