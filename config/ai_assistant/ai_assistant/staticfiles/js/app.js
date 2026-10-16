
const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const chatBox = document.getElementById("chat-box");
const sendButton = document.getElementById("send-button");
const clearButton = document.getElementById("clear-button");
const statusBadge = document.getElementById("connection-status");
const offlineNotice = document.getElementById("offline-notice");

function addMessage(text, sender) {
    const message = document.createElement("div");
    message.className = `message ${sender}-message`;

    const label = document.createElement("span");
    label.className = "message-label";
    label.textContent =
        sender === "user" ? "STUDENT" : "CLASS ASSISTANT";

    const content = document.createElement("p");
    content.className = "message-content";
    content.textContent = text;

    message.append(label, content);
    chatBox.appendChild(message);
    message.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
    });
}

function updateConnectionStatus() {
    const online = navigator.onLine;

    statusBadge.textContent = online ? "Online" : "Offline";
    statusBadge.className =
        `connection-status ${online ? "is-online" : "is-offline"}`;

    offlineNotice.hidden = online;
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = input.value.trim();

    if (!message || sendButton.disabled || message.length > 4000) {
        return;
    }

    if (!navigator.onLine) {
        updateConnectionStatus();
        return;
    }

    addMessage(message, "user");
    input.value = "";
    sendButton.disabled = true;
    sendButton.textContent = "Thinking...";

    try {
        const csrfToken = form.querySelector(
            "[name=csrfmiddlewaretoken]"
        ).value;

        const response = await fetch(form.dataset.askUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({ message })
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.error || "Something went wrong.");
        }

        addMessage(data.answer, "ai");
    } catch (error) {
        addMessage(
            error instanceof Error
                ? error.message
                : "Unable to contact the AI. Please try again.",
            "ai"
        );
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "Send";
        input.focus();
    }
});

clearButton.addEventListener("click", () => {
    chatBox.replaceChildren();
    addMessage(
        "Chat cleared. What would you like to learn?",
        "ai"
    );
    input.focus();
});

document.querySelectorAll(".suggestion").forEach((button) => {
    button.addEventListener("click", () => {
        input.value = button.textContent.trim();
        input.focus();
    });
});

window.addEventListener("online", updateConnectionStatus);
window.addEventListener("offline", updateConnectionStatus);

updateConnectionStatus();

if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register(
            form.dataset.serviceWorkerUrl
        ).catch((error) => {
            console.error("Service worker registration failed.", error);
        });
    });
}
