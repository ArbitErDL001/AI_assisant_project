const form = document.getElementById("chat-form");

if (form) {
    const input = document.getElementById("message-input");
    const chatBox = document.getElementById("chat-box");
    const sendButton = document.getElementById("send-button");
    const newChatButton = document.getElementById("clear-button");
    const currentChatItem = document.getElementById("current-chat-item");
    const currentChatTitle = document.getElementById("current-chat-title");
    const conversationTitle = document.getElementById("conversation-title");
    const recentChats = document.getElementById("recent-chats");
    const historyDivider = document.getElementById("history-divider");
    const historyStorageWarning = document.getElementById("history-storage-warning");
    const statusBadge = document.getElementById("connection-status");
    const offlineNotice = document.getElementById("offline-notice");
    const offlineGame = document.getElementById("offline-game");
    const offlineGameTitle = document.getElementById("offline-game-title");
    const navToggle = document.getElementById("nav-toggle");
    const storageKey = "lambda-xi-assistant-chats-v1";
    const starterMessage = chatBox.querySelector(".message")?.cloneNode(true);

    let conversations = [];
    let activeConversationId = createConversationId();
    let currentMessages = [];

    function createConversationId() {
        if (typeof crypto.randomUUID === "function") {
            return crypto.randomUUID();
        }
        return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    }

    function showStorageWarning(error) {
        console.error("Recent chat history could not be stored:", error);
        historyStorageWarning.hidden = false;
    }

    function isValidConversation(value) {
        return (
            value !== null &&
            typeof value === "object" &&
            typeof value.id === "string" &&
            Array.isArray(value.messages) &&
            value.messages.every(
                (message) =>
                    message !== null &&
                    typeof message === "object" &&
                    (message.sender === "user" || message.sender === "ai") &&
                    typeof message.text === "string",
            )
        );
    }

    function loadHistory() {
        try {
            const saved = localStorage.getItem(storageKey);
            if (!saved) return;

            const data = JSON.parse(saved);
            if (
                data === null ||
                typeof data !== "object" ||
                !Array.isArray(data.conversations)
            ) {
                throw new Error("Saved chat history has an invalid format.");
            }

            conversations = data.conversations.filter(isValidConversation);
        } catch (error) {
            showStorageWarning(error);
        }
    }

    function saveHistory() {
        try {
            localStorage.setItem(
                storageKey,
                JSON.stringify({
                    activeConversationId,
                    conversations,
                }),
            );
            historyStorageWarning.hidden = true;
        } catch (error) {
            showStorageWarning(error);
        }
    }

    function titleFor(messages) {
        const firstUserMessage = messages.find(
            (message) => message.sender === "user",
        );
        if (!firstUserMessage) return "New chat";
        const title = firstUserMessage.text.trim();
        return title.length > 36 ? `${title.slice(0, 36)}…` : title;
    }

    function updateConversationTitle(title) {
        currentChatTitle.textContent = title;
        conversationTitle.textContent = title;
    }

    function addMessage(text, sender, persist = true) {
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

        if (persist) {
            currentMessages.push({ sender, text });
            updateConversationTitle(titleFor(currentMessages));
            storeCurrentConversation();
        }

        message.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function storeCurrentConversation() {
        if (!currentMessages.some((message) => message.sender === "user")) {
            renderRecentChats();
            saveHistory();
            return;
        }

        const conversation = {
            id: activeConversationId,
            title: titleFor(currentMessages),
            messages: currentMessages,
            updatedAt: Date.now(),
        };
        conversations = conversations.filter(
            (item) => item.id !== activeConversationId,
        );
        conversations.push(conversation);
        conversations.sort((left, right) => right.updatedAt - left.updatedAt);
        renderRecentChats();
        saveHistory();
    }

    function appendHistoryIcon(button) {
        const icon = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "svg",
        );
        icon.classList.add("icon");
        icon.setAttribute("aria-hidden", "true");
        const use = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "use",
        );
        use.setAttribute("href", "#i-chat");
        icon.appendChild(use);
        button.appendChild(icon);
    }

    function deleteConversation(conversationId) {
        conversations = conversations.filter(
            (conversation) => conversation.id !== conversationId,
        );
        renderRecentChats();
        saveHistory();
    }

    function renderRecentChats() {
        recentChats.replaceChildren();

        const recentConversations = conversations.filter(
            (conversation) => conversation.id !== activeConversationId,
        );
        historyDivider.hidden =
            recentConversations.length === 0 && currentMessages.length === 0;

        for (const conversation of recentConversations) {
            const row = document.createElement("div");
            row.className = "history-row";

            const button = document.createElement("button");
            button.className = "history-item";
            button.type = "button";
            button.dataset.conversationId = conversation.id;
            button.disabled = sendButton.disabled;
            appendHistoryIcon(button);

            const title = document.createElement("span");
            title.textContent = conversation.title || titleFor(conversation.messages);
            button.appendChild(title);
            button.addEventListener("click", () => {
                openConversation(conversation.id);
            });
            row.appendChild(button);

            const deleteButton = document.createElement("button");
            deleteButton.className = "history-delete";
            deleteButton.type = "button";
            deleteButton.disabled = sendButton.disabled;
            deleteButton.setAttribute(
                "aria-label",
                `Delete chat: ${conversation.title || titleFor(conversation.messages)}`,
            );
            deleteButton.title = "Delete chat";
            const deleteIcon = document.createElementNS(
                "http://www.w3.org/2000/svg",
                "svg",
            );
            deleteIcon.classList.add("icon");
            deleteIcon.setAttribute("aria-hidden", "true");
            const deletePath = document.createElementNS(
                "http://www.w3.org/2000/svg",
                "path",
            );
            deletePath.setAttribute(
                "d",
                "M3 6h18M8 6V4h8v2m3 0-1 14H6L5 6m4 4v6m6-6v6",
            );
            deleteIcon.appendChild(deletePath);
            deleteButton.appendChild(deleteIcon);
            deleteButton.addEventListener("click", () => {
                deleteConversation(conversation.id);
            });
            row.appendChild(deleteButton);
            recentChats.appendChild(row);
        }
    }

    function renderCurrentConversation() {
        chatBox.querySelectorAll(".message").forEach((message) => message.remove());
        if (currentMessages.length === 0) {
            if (starterMessage) chatBox.appendChild(starterMessage.cloneNode(true));
            return;
        }
        currentMessages.forEach(({ text, sender }) => {
            addMessage(text, sender, false);
        });
    }

    function setConversationControlsDisabled(disabled) {
        newChatButton.disabled = disabled;
        currentChatItem.disabled = disabled;
        recentChats.querySelectorAll("button").forEach((button) => {
            button.disabled = disabled;
        });
    }

    function openConversation(conversationId) {
        const conversation = conversations.find(
            (item) => item.id === conversationId,
        );
        if (!conversation || conversationId === activeConversationId) return;

        storeCurrentConversation();
        activeConversationId = conversation.id;
        currentMessages = conversation.messages.map((message) => ({
            sender: message.sender,
            text: message.text,
        }));
        updateConversationTitle(titleFor(currentMessages));
        renderCurrentConversation();
        renderRecentChats();
        saveHistory();
        input.value = "";
        navToggle.checked = false;
    }

    function startNewConversation() {
        if (sendButton.disabled) return;

        storeCurrentConversation();
        activeConversationId = createConversationId();
        currentMessages = [];
        updateConversationTitle("New chat");
        renderCurrentConversation();
        renderRecentChats();
        saveHistory();
        input.value = "";
        input.focus();
        navToggle.checked = false;
    }

    function updateConnectionStatus() {
        const online = navigator.onLine;

        statusBadge.querySelector("[data-status-label]").textContent =
            online ? "Online" : "Offline";
        statusBadge.className = `sync-status ${online ? "is-online" : "is-offline"}`;
        offlineNotice.hidden = online;

        const wasOffline = offlineGame.hidden === false;
        offlineGame.hidden = online;
        if (!online && !wasOffline) {
            offlineGameTitle.focus({ preventScroll: true });
        }
    }

    loadHistory();
    updateConversationTitle(titleFor(currentMessages));
    renderCurrentConversation();
    renderRecentChats();
    currentChatItem.addEventListener("click", () => {
        renderCurrentConversation();
        input.focus();
        navToggle.checked = false;
    });

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
        setConversationControlsDisabled(true);

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
            setConversationControlsDisabled(false);
            input.focus();
        }
    });

    newChatButton.addEventListener("click", startNewConversation);

    document.querySelectorAll(".suggestion").forEach((button) => {
        button.addEventListener("click", () => {
            input.value = button.dataset.prompt || button.textContent.trim();
            input.focus();
        });
    });

    window.addEventListener("online", updateConnectionStatus);
    window.addEventListener("offline", updateConnectionStatus);
    window.addEventListener("storage", (event) => {
        if (event.key !== storageKey || event.newValue === null) return;

        try {
            const data = JSON.parse(event.newValue);
            if (!Array.isArray(data.conversations)) {
                throw new Error("Saved chat history has an invalid format.");
            }
            conversations = data.conversations.filter(isValidConversation);
            renderRecentChats();
        } catch (error) {
            showStorageWarning(error);
        }
    });
    updateConnectionStatus();

    if ("serviceWorker" in navigator && form.dataset.serviceWorkerUrl) {
        navigator.serviceWorker
            .register(form.dataset.serviceWorkerUrl)
            .catch((error) => {
                console.error("Service worker registration failed:", error);
            });
    }
}
