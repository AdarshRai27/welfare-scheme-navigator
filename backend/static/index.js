// Client-side interactions for Web Chat Simulator & Diagnostics visualizer

const PHONE_NUMBER = "919999999999";
const BASE_URL = window.location.origin;

// DOM Selectors
const chatFeed = document.getElementById("chatFeed");
const inputForm = document.getElementById("inputForm");
const textInput = document.getElementById("textInput");
const redisState = document.getElementById("redisState");

// Button Triggers
const btnAudio = document.getElementById("btnAudio");
const btnAadhaar = document.getElementById("btnAadhaar");
const btnIncome = document.getElementById("btnIncome");
const btnClear = document.getElementById("btnClear");

// Hidden File Inputs
const fileAudio = document.getElementById("fileAudio");
const fileAadhaar = document.getElementById("fileAadhaar");
const fileIncome = document.getElementById("fileIncome");

// Profile visualizer DOM
const valName = document.getElementById("valName");
const valAadhaar = document.getElementById("valAadhaar");
const valIncome = document.getElementById("valIncome");
const valLand = document.getElementById("valLand");
const valState = document.getElementById("valState");

// Helper to add message bubbles
function addMessage(sender, text) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("msg", sender === "user" ? "user-msg" : "bot-msg");

    // Replace Markdown wraps or links in reply
    let processedText = text;
    
    // Convert relative static paths to absolute links
    processedText = processedText.replace(
        /(\/static\/forms\/[a-zA-Z0-9_\-\.]+)/g,
        `<a href="$1" target="_blank">$1</a>`
    );

    // Convert audio speech paths to embedded audio player controls
    processedText = processedText.replace(
        /(\/static\/audio\/[a-zA-Z0-9_\-\.]+\.mp3)/g,
        `<audio controls class="msg-audio-player" style="display:block; margin-top:8px; width:100%; max-width:240px;" src="$1"></audio>`
    );

    // Get timestamp
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    msgDiv.innerHTML = `
        <div class="bubble">
            <p>${processedText}</p>
            <span class="time">${timeStr}</span>
        </div>
    `;

    chatFeed.appendChild(msgDiv);
    chatFeed.scrollTop = chatFeed.scrollHeight;
}

// POST text or file data to backend
async function sendWebMessage(messageType, text = null, file = null) {
    const formData = new FormData();
    formData.append("phone", PHONE_NUMBER);
    formData.append("message_type", messageType);
    if (text) formData.append("text", text);
    if (file) formData.append("file", file);

    try {
        const response = await fetch(`${BASE_URL}/webhook/web/message`, {
            method: "POST",
            body: formData,
        });
        if (response.ok) {
            const data = await response.json();
            if (data && data.reply_text) {
                addMessage("bot", data.reply_text);
            }
            // Refresh state diagnostics panel
            fetchState();
        } else {
            console.error("Failed sending message:", await response.text());
        }
    } catch (err) {
        console.error("Connection error:", err);
    }
}

// Retrieve active state diagnostics
async function fetchState() {
    try {
        const res = await fetch(`${BASE_URL}/webhook/diagnostics/session/${PHONE_NUMBER}`);
        if (res.ok) {
            const session = await res.json();
            
            // Pretty-print raw Redis JSON
            redisState.textContent = JSON.stringify(session, null, 4);

            if (session && session.extracted_profile) {
                const profile = session.extracted_profile;
                valName.textContent = profile.name || "Not Extracted";
                valAadhaar.textContent = profile.aadhaar_number || "Not Extracted";
                valIncome.textContent = profile.annual_income ? `₹${profile.annual_income}` : "Not Extracted";
                valLand.textContent = profile.land_size_hectares ? `${profile.land_size_hectares} Hectares` : "Not Extracted";
                valState.textContent = profile.state || "Not Extracted";
            } else {
                resetProfileCard();
            }
        }
    } catch (err) {
        console.error("Error retrieving session diagnostics:", err);
    }
}

function resetProfileCard() {
    valName.textContent = "Not Extracted";
    valAadhaar.textContent = "Not Extracted";
    valIncome.textContent = "Not Extracted";
    valLand.textContent = "Not Extracted";
    valState.textContent = "Not Extracted";
}

// Text Form Submit
inputForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = textInput.value.trim();
    if (!query) return;

    addMessage("user", query);
    textInput.value = "";
    sendWebMessage("text", query);
});

// Trigger hidden file inputs on click
btnAudio.addEventListener("click", () => fileAudio.click());
btnAadhaar.addEventListener("click", () => fileAadhaar.click());
btnIncome.addEventListener("click", () => fileIncome.click());

// File input change handlers
fileAudio.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
        addMessage("user", `🎤 [Sent Voice Note: ${file.name}]`);
        sendWebMessage("audio", null, file);
    }
});

fileAadhaar.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
        addMessage("user", `🪪 [Uploaded Aadhaar: ${file.name}]`);
        sendWebMessage("aadhaar", null, file);
    }
});

fileIncome.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
        addMessage("user", `📄 [Uploaded Income Certificate: ${file.name}]`);
        sendWebMessage("income", null, file);
    }
});

// Clear session diag trigger
btnClear.addEventListener("click", async () => {
    try {
        await fetch(`${BASE_URL}/webhook/diagnostics/session/${PHONE_NUMBER}`, { method: "DELETE" });
        redisState.textContent = '{ "status": "Session cleared." }';
        resetProfileCard();
        chatFeed.innerHTML = `
            <div class="msg bot-msg">
                <div class="bubble">
                    <p>सत्र सफलतापूर्वक रीसेट कर दिया गया है। नई बातचीत शुरू करें।</p>
                    <span class="time">Now</span>
                </div>
            </div>
        `;
    } catch (err) {
        console.error("Failed resetting diagnostics session:", err);
    }
});

// Initial diagnostics poll on page load
fetchState();
