// Client-side interactions for Web Chat Simulator & Diagnostics visualizer

const PHONE_NUMBER = "919999999999";
const BASE_URL = window.location.origin;

// DOM Selectors
const chatFeed = document.getElementById("chatFeed");
const inputForm = document.getElementById("inputForm");
const textInput = document.getElementById("textInput");
const btnAudio = document.getElementById("btnAudio");
const btnAadhaar = document.getElementById("btnAadhaar");
const btnIncome = document.getElementById("btnIncome");
const btnClear = document.getElementById("btnClear");
const redisState = document.getElementById("redisState");

// Profile visualizer DOM
const valName = document.getElementById("valName");
const valAadhaar = document.getElementById("valAadhaar");
const valIncome = document.getElementById("valIncome");
const valLand = document.getElementById("valLand");
const valState = document.getElementById("valState");

// Helpers to add message bubbles
function addMessage(sender, text) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("msg", sender === "user" ? "user-msg" : "bot-msg");

    // Replace Markdown wraps or links in reply
    let processedText = text;
    // Simple replacement of relative static paths with absolute links
    processedText = processedText.replace(
        /(\/static\/forms\/[a-zA-Z0-9_\-\.]+)/g,
        `<a href="$1" target="_blank">$1</a>`
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

// REST call to trigger webhook
async function postWebhook(payload) {
    try {
        const response = await fetch(`${BASE_URL}/webhook/whatsapp`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });
        if (response.ok) {
            // Wait brief moment for graph execution, then refresh diagnostics state
            setTimeout(fetchState, 600);
        } else {
            console.error("Webhook POST failed:", await response.text());
        }
    } catch (err) {
        console.error("Connection error posting webhook:", err);
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

// Send user text messages
inputForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = textInput.value.trim();
    if (!query) return;

    addMessage("user", query);
    textInput.value = "";

    const payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": PHONE_NUMBER,
                        "id": "web_" + Math.random().toString(36).substr(2, 9),
                        "timestamp": Math.floor(Date.now() / 1000).toString(),
                        "text": { "body": query },
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    };

    postWebhook(payload);
});

// Trigger mock voice note
btnAudio.addEventListener("click", () => {
    addMessage("user", "🎤 [Sent Spoken Hindi Voice Note]");
    
    const payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": PHONE_NUMBER,
                        "id": "web_audio_" + Math.random().toString(36).substr(2, 9),
                        "timestamp": Math.floor(Date.now() / 1000).toString(),
                        "audio": {
                            "id": "mock_audio_media_id",
                            "mime_type": "audio/ogg"
                        },
                        "type": "audio"
                    }]
                },
                "field": "messages"
            }]
        }]
    };

    postWebhook(payload);
});

// Trigger mock Aadhaar OCR
btnAadhaar.addEventListener("click", () => {
    addMessage("user", "🪪 [Uploaded Aadhaar Card Photo]");

    const payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": PHONE_NUMBER,
                        "id": "web_img_aadhaar_" + Math.random().toString(36).substr(2, 9),
                        "timestamp": Math.floor(Date.now() / 1000).toString(),
                        "image": {
                            "id": "media_image_aadhaar",
                            "mime_type": "image/jpeg"
                        },
                        "type": "image"
                    }]
                },
                "field": "messages"
            }]
        }]
    };

    postWebhook(payload);
});

// Trigger mock Income OCR
btnIncome.addEventListener("click", () => {
    addMessage("user", "📄 [Uploaded Income Certificate Photo]");

    const payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": PHONE_NUMBER,
                        "id": "web_img_income_" + Math.random().toString(36).substr(2, 9),
                        "timestamp": Math.floor(Date.now() / 1000).toString(),
                        "image": {
                            "id": "media_image_income",
                            "mime_type": "image/jpeg"
                        },
                        "type": "image"
                    }]
                },
                "field": "messages"
            }]
        }]
    };

    postWebhook(payload);
});

// Clear session diag trigger
btnClear.addEventListener("click", async () => {
    try {
        const payload = {
            "whatsapp_id": PHONE_NUMBER,
            "preferred_language": "hi",
            "extracted_profile": {}
        };
        // Clear Redis cache immediately
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
