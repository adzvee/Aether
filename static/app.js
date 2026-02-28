const moods = [
  { label: "Happy", emoji: "😊" },
  { label: "Calm", emoji: "🧘" }, // Added Calm here
  { label: "Sad", emoji: "😢" }, { label: "Drained", emoji: "🔋" },
  { label: "Excited", emoji: "✨" }, { label: "Determined", emoji: "💪" },
  { label: "Overwhelmed", emoji: "🌊" }, { label: "Frustrated", emoji: "😤" },
  { label: "Nervous", emoji: "😟" }, { label: "Okay", emoji: "☁️" }
];

let selectedMood = "";
const stages = {
    input: document.getElementById("stage-input"),
    reveal: document.getElementById("stage-reveal"),
    activities: document.getElementById("stage-activities"),
    final: document.getElementById("stage-final")
};

// --- HISTORY LOGIC ---
function saveSessionToHistory(start, end, activity) {
    const history = JSON.parse(localStorage.getItem('aether_history') || '[]');
    const newEntry = {
        date: new Date().toLocaleDateString(),
        journey: `${start} → ${end}`,
        action: activity || "Checked In"
    };
    history.unshift(newEntry);
    localStorage.setItem('aether_history', JSON.stringify(history.slice(0, 15)));
}

// History UI Listeners
document.getElementById("openHistoryBtn").onclick = () => {
    const history = JSON.parse(localStorage.getItem('aether_history') || '[]');
    const list = document.getElementById("historyList");
    list.innerHTML = history.length ? "" : "<p style='text-align:center; color:gray; padding: 20px;'>No journeys recorded yet.</p>";

    history.forEach(item => {
        const div = document.createElement("div");
        div.style = "padding: 1.2rem; border-bottom: 1px solid #f1f5f9;";
        div.innerHTML = `
            <div style="font-size: 0.8rem; color: #64748b;">${item.date}</div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:5px;">
                <strong style="font-size: 1.1rem;">${item.journey}</strong>
                <span style="font-size:0.75rem; background:#f0fdfa; color:#0d9488; padding:4px 10px; border-radius:8px; font-weight:700; text-transform:uppercase;">${item.action}</span>
            </div>
        `;
        list.appendChild(div);
    });
    document.getElementById("historyOverlay").classList.remove("hidden");
};

document.getElementById("closeHistoryBtn").onclick = () => document.getElementById("historyOverlay").classList.add("hidden");

document.getElementById("clearHistory").onclick = () => {
    if(confirm("Are you sure you want to clear your journey history?")) {
        localStorage.removeItem('aether_history');
        document.getElementById("historyList").innerHTML = "<p style='text-align:center; padding: 20px;'>History cleared.</p>";
    }
};

// --- SPLASH LOGIC ---
let breatheCount = 0;
const breatheTexts = ["Breathe in...", "Breathe out..."];
const textEl = document.getElementById("breathingText");
const breatheInterval = setInterval(() => { if(textEl) { breatheCount++; textEl.innerText = breatheTexts[breatheCount % 2]; } }, 2000);

function hideLoadingScreen() {
    clearInterval(breatheInterval);
    const splash = document.getElementById("splashScreen");
    const mainApp = document.getElementById("mainApp");
    if (splash) {
        splash.style.opacity = '0';
        setTimeout(() => { splash.style.display = 'none'; mainApp.classList.remove('hidden'); mainApp.style.opacity = '1'; }, 1200);
    }
}
setTimeout(hideLoadingScreen, 4500);

// --- MOOD RENDERER ---
function setupMoods(containerId, callback) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";
    moods.forEach(m => {
        const btn = document.createElement("button");
        btn.className = "mood-pill";
        btn.innerHTML = `<span style="font-size:2rem;margin-bottom:8px">${m.emoji}</span><span style="font-weight:700" class="pill-label">${m.label}</span>`;
        btn.onclick = () => {
            container.querySelectorAll('.mood-pill').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            callback(m.label);
        };
        container.appendChild(btn);
    });
}

// --- RECOMMENDATION GENERATION ---
document.getElementById("generateBtn").onclick = async () => {
    if (!selectedMood) return alert("Please select a mood!");
    const status = document.getElementById("statusText");
    status.classList.add("visible");

    try {
        const res = await fetch("/api/get_recommendations", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mood: selectedMood, note: document.getElementById("noteInput").value })
        });
        const data = await res.json();

        document.getElementById("quoteText").textContent = `"${data.quote}"`;
        document.getElementById("quoteAuthor").textContent = data.author;

        const list = document.getElementById("activityList");
        const dropdown = document.getElementById("completedActivityInput");
        list.innerHTML = "";
        dropdown.innerHTML = '<option value="None/Other">I did something else / Just checked in</option>';

        data.activities.forEach(act => {
            const opt = document.createElement("option");
            opt.value = act.title;
            opt.textContent = act.title;
            dropdown.appendChild(opt);

            let img = "undraw_relaxing-outdoors_s653.svg";
            const t = act.title.toLowerCase();
            if (t.includes("yoga") || t.includes("stretch")) img = "undraw_yoga_i399.svg";
            else if (t.includes("music") || t.includes("listen") || t.includes("song")) img = "undraw_dua_lipa_bc8o.svg";
            else if (t.includes("walk") || t.includes("outside") || t.includes("nature")) img = "undraw_a-day-at-the-park_9w8d.svg";
            else if (t.includes("write") || t.includes("journal") || t.includes("creative")) img = "undraw_writing-down-ideas_h99r.svg";
            else if (t.includes("break down") || t.includes("task") || t.includes("organize")) img = "undraw_organizing-projects_heze.svg";
            else if (t.includes("read") || t.includes("book")) img = "undraw_book-lover_m9n3.svg";
            else if (t.includes("tea") || t.includes("coffee") || t.includes("drink")) img = "undraw_drink-coffee_q0ey.svg";
            else if (t.includes("game") || t.includes("play")) img = "undraw_video-games_itxa.svg";
            else if (t.includes("call") || t.includes("talk") || t.includes("friend")) img = "undraw_calling_ieh0.svg";

            const card = document.createElement("div");
            card.className = "activity-card";
            card.innerHTML = `
                <img src="/static/assets/illustrations/${img}" alt="Activity" onerror="this.src='/static/assets/illustrations/undraw_relaxing-outdoors_s653.svg'">
                <h3 style="font-size:1.3rem; margin:10px 0; font-weight:800;">${act.title}</h3>
                <p style="color:#64748b; line-height:1.6;">${act.description}</p>
            `;
            list.appendChild(card);
        });

        status.classList.remove("visible");
        stages.input.classList.add("hidden");
        stages.reveal.classList.remove("hidden");
    } catch (e) { status.textContent = "Error connecting to Aether."; }
};

document.getElementById("flipCard").onclick = () => document.getElementById("flipCard").classList.toggle("flipped");

document.getElementById("showActivitiesBtn").onclick = (e) => {
    e.stopPropagation();
    stages.activities.classList.remove("hidden");
    setTimeout(() => { window.scrollTo({ top: stages.activities.offsetTop - 40, behavior: "smooth" }); }, 100);
};

// --- FINAL SUMMARY & HISTORY SAVE ---
setupMoods("afterMoodChoices", (finalMood) => {
    const activityChosen = document.getElementById("completedActivityInput").value;
    saveSessionToHistory(selectedMood, finalMood, activityChosen);

    stages.activities.classList.add("hidden");

    // 1. Parting Messages based on final state
    const partingMessages = {
        "Happy": "Keep this brightness with you as you move through the rest of your day! ✨",
        "Calm": "May this peace stay centered in your heart. You've earned this moment. 🧘",
        "Excited": "That energy is contagious! Go use it to create something amazing. ⚡",
        "Determined": "You've got the momentum now. There's nothing you can't handle. 💪",
        "Okay": "Sometimes 'okay' is exactly where we need to be. Be gentle with yourself. ☁️",
        "Frustrated": "It's alright to still feel a bit tense. Progress isn't always a straight line. 🌿",
        "Sad": "Sending you extra warmth. It’s okay to not be okay right now. ❤️",
        "Drained": "Rest is productive. Allow yourself the space to slowly recharge. 🔋",
        "Overwhelmed": "One step at a time. You've already done the hardest part by checking in. 🌊",
        "Nervous": "Breathe. You've handled everything life has thrown at you so far. You've got this. 😟"
    };

    const personalNote = partingMessages[finalMood] || "Take this feeling with you into your next moment. 🌿";

    // 2. Build the final message
    let summaryHTML = "";
    if (["Happy", "Calm", "Excited", "Determined"].includes(finalMood)) {
        summaryHTML = `
            <p>You started feeling <strong>${selectedMood}</strong> and after <strong>${activityChosen}</strong>, you're now <strong>${finalMood}</strong>! ⚡</p>
            <p style="margin-top: 1.5rem; font-size: 1.2rem; color: #0d9488; font-weight: 600;">${personalNote}</p>
        `;
    } else {
        summaryHTML = `
            <p>You started as <strong>${selectedMood}</strong> and ended as <strong>${finalMood}</strong> after <strong>${activityChosen}</strong>. 🌿</p>
            <p style="margin-top: 1.5rem; font-size: 1.2rem; color: #64748b; font-style: italic;">${personalNote}</p>
        `;
    }

    document.getElementById("finalSummary").innerHTML = summaryHTML;
    stages.final.classList.remove("hidden");

    setTimeout(() => { window.scrollTo({ top: stages.final.offsetTop - 50, behavior: 'smooth' }); }, 50);
});

// --- SHARE LOGIC ---
document.getElementById("shareBtn").onclick = async () => {
    const finalPill = document.querySelector('#afterMoodChoices .mood-pill.active .pill-label');
    const finalMood = finalPill ? finalPill.innerText : "Better";
    const activityChosen = document.getElementById("completedActivityInput").value;
    const shareText = `My Aether Journey: I started feeling ${selectedMood}, tried ${activityChosen}, and now I feel ${finalMood}. 🌿`;

    try {
        if (navigator.share) {
            await navigator.share({ title: 'Aether Journey', text: shareText, url: window.location.href });
        } else {
            await navigator.clipboard.writeText(shareText);
            const btn = document.getElementById("shareBtn");
            const originalText = btn.innerText;
            btn.innerText = "Copied! 📋";
            setTimeout(() => btn.innerText = originalText, 2000);
        }
    } catch (e) {
        navigator.clipboard.writeText(shareText);
        alert("Copied to clipboard! 📋");
    }
};

document.getElementById("restartBtn").onclick = () => {
    location.reload();
};

setupMoods("moodChoices", m => selectedMood = m);
