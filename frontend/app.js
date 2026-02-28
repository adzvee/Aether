const API_BASE = window.location.protocol.startsWith("http")
  ? `${window.location.origin}/api`
  : "http://127.0.0.1:5000/api";
const moods = ["Sad", "Drained", "Excited", "Determined", "Overwhelmed", "Frustrated", "Nervous", "Okay"];

let selectedMood = "";
let selectedAfterMood = "";
let currentLogId = null;

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

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.style.color = isError ? "#9f2f2f" : "var(--ink-soft)";
}

function createMoodPills(container, onSelect) {
  container.innerHTML = "";
  moods.forEach((mood) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mood-pill";
    button.textContent = mood;
    button.addEventListener("click", () => {
      const pills = container.querySelectorAll(".mood-pill");
      pills.forEach((pill) => pill.classList.remove("active"));
      button.classList.add("active");
      onSelect(mood);
    });
    container.appendChild(button);
  });
}

function renderRecommendations(data) {
  quoteCard.classList.remove("hidden");
  quoteCard.innerHTML = `
    <p>"${data.quote}"</p>
    <p class="author">- ${data.author}</p>
  `;

  activityList.innerHTML = "";
  (data.activities || []).forEach((activity) => {
    const card = document.createElement("article");
    card.className = "activity";
    card.innerHTML = `
      <h4>${activity.title}</h4>
      <p>${activity.description}</p>
      ${activity.type === "music_suggestion" ? '<span class="badge">Music suggestion</span>' : ""}
    `;
    activityList.appendChild(card);
  });

  afterMoodSection.classList.remove("hidden");
}

function formatDate(isoDate) {
  if (!isoDate) {
    return "Unknown";
  }

  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) {
    return isoDate;
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

async function fetchHistory() {
  try {
    const response = await fetch(`${API_BASE}/history`);
    if (!response.ok) {
      throw new Error("Failed to load history");
    }

    const logs = await response.json();
    historyList.innerHTML = "";

    if (!logs.length) {
      historyList.innerHTML = "<p>No mood history yet.</p>";
      return;
    }

    logs.forEach((log) => {
      const item = document.createElement("article");
      item.className = "history-item";
      item.innerHTML = `
        <p><strong>${log.mood_before}</strong> -> ${log.mood_after || "(pending)"}</p>
        <p>${log.note || "No note"}</p>
        <p>${formatDate(log.timestamp)}</p>
      `;
      historyList.appendChild(item);
    });
  } catch (error) {
    historyList.innerHTML = `<p>Could not load history: ${error.message}</p>`;
  }
}

async function saveInitialLog(mood, note) {
  const response = await fetch(`${API_BASE}/logs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mood_before: mood, note })
  });

  if (!response.ok) {
    throw new Error("Failed to save initial log");
  }

  const data = await response.json();
  return data.id;
}

async function updateAfterMood(logId, mood) {
  const response = await fetch(`${API_BASE}/logs/${logId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mood_after: mood })
  });

  if (!response.ok) {
    throw new Error("Failed to update mood");
  }
}

async function getRecommendations(mood, note) {
  const response = await fetch(`${API_BASE}/get_recommendations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mood, note })
  });

  if (!response.ok) {
    let message = "Failed to get recommendations";
    try {
      const payload = await response.json();
      message = payload.error || message;
    } catch {
      // Keep default message when backend doesn't return JSON.
    }
    throw new Error(message);
  }

  return response.json();
}

async function onGenerate() {
  if (!selectedMood) {
    setStatus("Select a mood before requesting recommendations.", true);
    return;
  }

  const note = noteInput.value.trim();

  try {
    setStatus("Saving mood and getting recommendations...");
    generateBtn.disabled = true;

    currentLogId = await saveInitialLog(selectedMood, note);
    const recData = await getRecommendations(selectedMood, note);
    renderRecommendations(recData);

    setStatus("Recommendations are ready.");
    await fetchHistory();
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    generateBtn.disabled = false;
  }
}

async function onAfterMoodSelected(mood) {
  selectedAfterMood = mood;

  if (!currentLogId) {
    return;
  }

  try {
    await updateAfterMood(currentLogId, selectedAfterMood);
    setStatus(`Saved your follow-up mood: ${selectedAfterMood}.`);
    await fetchHistory();
  } catch (error) {
    setStatus(error.message, true);
  }
}

generateBtn.addEventListener("click", onGenerate);
refreshHistoryBtn.addEventListener("click", fetchHistory);

createMoodPills(moodChoices, (mood) => {
  selectedMood = mood;
});

createMoodPills(afterMoodChoices, onAfterMoodSelected);
fetchHistory();
