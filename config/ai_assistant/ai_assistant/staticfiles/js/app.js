
const form = document.getElementById("chat-form");

if (form) {
    const input = document.getElementById("message-input");
    const chatBox = document.getElementById("chat-box");
    const sendButton = document.getElementById("send-button");
    const clearButton = document.getElementById("clear-button");
    const statusBadge = document.getElementById("connection-status");
    const offlineNotice = document.getElementById("offline-notice");

    function addMessage(text, sender) {
        const isUser = sender === "user";
        const message = document.createElement("article");
        message.className = `message ${isUser ? "user-message" : "assistant-message"}`;
        message.setAttribute(
            "aria-label",
            isUser ? "Your message" : "ΛΞ Assistant response",
        );

        const meta = document.createElement("div");
        meta.className = `message-meta${isUser ? " user-meta" : ""}`;

        if (isUser) {
            const name = form.dataset.studentName || "You";
            const initials = document.createElement("span");
            initials.className = "avatar avatar-small";
            initials.textContent = name.trim().charAt(0).toUpperCase();

            const label = document.createElement("span");
            label.textContent = name;
            meta.append(label, initials);
        } else {
            const brand = document.createElement("span");
            brand.className = "brand-icon";
            const icon = document.createElementNS(
                "http://www.w3.org/2000/svg",
                "svg",
            );
            icon.classList.add("icon");
            const spark = document.createElementNS(
                "http://www.w3.org/2000/svg",
                "use",
            );
            spark.setAttribute("href", "#i-spark");
            icon.appendChild(spark);
            brand.appendChild(icon);

            const label = document.createElement("strong");
            label.textContent = "ΛΞ Assistant";
            meta.append(brand, label);
        }

        const content = document.createElement(isUser ? "div" : "p");
        content.className = isUser ? "user-bubble" : "response-intro";
        content.textContent = text;

        message.append(meta, content);
        chatBox.appendChild(message);
        message.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function updateConnectionStatus() {
        const online = navigator.onLine;

        statusBadge.querySelector("[data-status-label]").textContent =
            online ? "Online" : "Offline";
        statusBadge.className = `sync-status ${online ? "is-online" : "is-offline"}`;
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
        sendButton.setAttribute("aria-label", "Waiting for response");

        try {
            const csrfToken = form.querySelector(
                "[name=csrfmiddlewaretoken]",
            ).value;
            const response = await fetch(form.dataset.askUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                credentials: "same-origin",
                body: JSON.stringify({ message }),
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Something went wrong.");
            }

            addMessage(data.answer, "ai");
        } catch (error) {
            addMessage(
                error instanceof Error
                    ? error.message
                    : "Unable to contact the AI. Please try again.",
                "ai",
            );
        } finally {
            sendButton.disabled = false;
            sendButton.setAttribute("aria-label", "Send message");
            input.focus();
        }
    });

    clearButton.addEventListener("click", () => {
        chatBox.querySelectorAll(".message").forEach((message) => message.remove());
        addMessage("Chat cleared. What would you like to learn?", "ai");
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

    if ("serviceWorker" in navigator && form.dataset.serviceWorkerUrl) {
        navigator.serviceWorker
            .register(form.dataset.serviceWorkerUrl)
            .catch((error) => {
                console.error("Service worker registration failed:", error);
            });
    }
}
