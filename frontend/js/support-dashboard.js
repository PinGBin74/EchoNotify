class SupportDashboard {
    constructor() {
        this.ws = null;
        this.token = null;
        this.rooms = new Map();
        this.currentRoomId = null;
        this.messagesCache = new Map();

        this.initElements();
        this.attachEventListeners();
    }

    initElements() {
        this.loginSection = document.getElementById("loginSection");
        this.roomsSection = document.getElementById("roomsSection");
        this.emptyState = document.getElementById("emptyState");
        this.chatSection = document.getElementById("chatSection");
        this.tokenInput = document.getElementById("tokenInput");
        this.connectButton =
            document.getElementById("connectButton");
        this.roomsList = document.getElementById("roomsList");
        this.messagesContainer =
            document.getElementById("messagesContainer");
        this.messageInput = document.getElementById("messageInput");
        this.sendButton = document.getElementById("sendButton");
        this.statusIndicator =
            document.getElementById("statusIndicator");
        this.statusText = document.getElementById("statusText");
        this.activeRoomsCount =
            document.getElementById("activeRoomsCount");
        this.unreadCount = document.getElementById("unreadCount");
        this.chatUserName = document.getElementById("chatUserName");
        this.chatRoomId = document.getElementById("chatRoomId");
        this.chatStartTime =
            document.getElementById("chatStartTime");
        this.closeRoomButton =
            document.getElementById("closeRoomButton");
    }

    attachEventListeners() {
        this.connectButton.addEventListener("click", () =>
            this.connect(),
        );
        this.sendButton.addEventListener("click", () =>
            this.sendMessage(),
        );
        this.messageInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.messageInput.addEventListener("input", () =>
            this.autoResizeTextarea(),
        );
        this.closeRoomButton.addEventListener("click", () =>
            this.closeCurrentRoom(),
        );
    }

    connect() {
        this.token = this.tokenInput.value.trim();

        if (!this.token) {
            this.showNotification(
                "Please enter your access token",
                "error",
            );
            return;
        }

        this.connectButton.disabled = true;
        this.connectButton.textContent = "Connecting...";

        const wsProtocol =
            window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsHost = window.location.host || "localhost:8000";
        const wsUrl = `${wsProtocol}//${wsHost}/chat/ws?token=${this.token}&is_support=true`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => this.onOpen();
        this.ws.onmessage = (event) => this.onMessage(event);
        this.ws.onclose = () => this.onClose();
        this.ws.onerror = (error) => this.onError(error);
    }

    async onOpen() {
        console.log("WebSocket connected");
        this.updateStatus(true);
        this.loginSection.classList.add("hidden");
        this.roomsSection.classList.remove("hidden");
        this.showNotification(
            "Connected to support chat",
            "success",
        );

        // Fetch active rooms
        await this.fetchActiveRooms();
    }

    async fetchActiveRooms() {
        try {
            const response = await fetch("/chat/rooms", {
                headers: {
                    Authorization: `Bearer ${this.token}`,
                },
            });

            if (response.ok) {
                const rooms = await response.json();
                rooms.forEach((room) => this.addOrUpdateRoom(room));
                this.updateStats();
            }
        } catch (error) {
            console.error("Error fetching rooms:", error);
        }
    }

    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log("Received message:", data);

            if (data.type === "notification") {
                // New message notification
                this.showNotification(data.message, "success");
                this.fetchActiveRooms();
            } else if (data.type === "message") {
                // Message in a room
                this.handleIncomingMessage(data);
            } else if (data.type === "typing") {
                this.showTypingIndicator(data.sender_name);
            }
        } catch (error) {
            console.error("Error parsing message:", error);
        }
    }

    handleIncomingMessage(data) {
        const roomId = data.room_id;

        // Add to cache
        if (!this.messagesCache.has(roomId)) {
            this.messagesCache.set(roomId, []);
        }
        this.messagesCache.get(roomId).push(data);

        // Display if current room
        if (roomId === this.currentRoomId) {
            this.displayMessage(data);
        } else {
            // Update room as unread
            const room = this.rooms.get(roomId);
            if (room) {
                room.unread = (room.unread || 0) + 1;
                this.refreshRoomsList();
            }
        }

        this.updateStats();
    }

    onClose() {
        console.log("WebSocket disconnected");
        this.updateStatus(false);
        this.sendButton.disabled = true;
        this.connectButton.disabled = false;
        this.connectButton.textContent = "Connect";
        this.showNotification("Disconnected from chat", "error");
    }

    onError(error) {
        console.error("WebSocket error:", error);
        this.showNotification("Connection error occurred", "error");
    }

    addOrUpdateRoom(roomData) {
        this.rooms.set(roomData.id, {
            ...roomData,
            unread: 0,
            lastMessage: "",
            lastMessageTime: roomData.updated_at,
        });
        this.refreshRoomsList();
    }

    refreshRoomsList() {
        this.roomsList.innerHTML = "";

        const sortedRooms = Array.from(this.rooms.values()).sort(
            (a, b) =>
                new Date(b.lastMessageTime) -
                new Date(a.lastMessageTime),
        );

        sortedRooms.forEach((room) => {
            const roomElement = this.createRoomElement(room);
            this.roomsList.appendChild(roomElement);
        });

        this.updateStats();
    }

    createRoomElement(room) {
        const div = document.createElement("div");
        div.className = "room-item";
        if (room.id === this.currentRoomId) {
            div.classList.add("active");
        }
        if (room.unread > 0) {
            div.classList.add("unread");
        }

        const userName = `User #${room.user_id}`;
        const time = new Date(
            room.lastMessageTime,
        ).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
        });

        div.innerHTML = `
                        <div class="room-user">
                            <span>${userName}</span>
                            ${room.unread > 0 ? `<span class="unread-badge">${room.unread}</span>` : ""}
                        </div>
                        <div class="room-preview">${room.lastMessage || "No messages yet"}</div>
                        <div class="room-time">Room #${room.id} • ${time}</div>
                    `;

        div.addEventListener("click", () =>
            this.selectRoom(room.id),
        );
        return div;
    }

    async selectRoom(roomId) {
        this.currentRoomId = roomId;
        const room = this.rooms.get(roomId);

        if (!room) return;

        // Mark as read
        room.unread = 0;
        this.refreshRoomsList();

        // Update UI
        this.emptyState.classList.add("hidden");
        this.chatSection.classList.remove("hidden");
        this.sendButton.disabled = false;

        this.chatUserName.textContent = `User #${room.user_id}`;
        this.chatRoomId.textContent = room.id;
        this.chatStartTime.textContent = new Date(
            room.created_at,
        ).toLocaleString();

        // Load messages
        await this.loadRoomHistory(roomId);
    }

    async loadRoomHistory(roomId) {
        try {
            const response = await fetch(
                `/chat/rooms/${roomId}/history`,
                {
                    headers: {
                        Authorization: `Bearer ${this.token}`,
                    },
                },
            );

            if (response.ok) {
                const data = await response.json();
                this.messagesContainer.innerHTML = "";
                this.messagesCache.set(roomId, data.messages);
                data.messages.forEach((msg) =>
                    this.displayMessage(msg, false),
                );
            }
        } catch (error) {
            console.error("Error loading history:", error);
        }
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        if (
            !message ||
            !this.ws ||
            this.ws.readyState !== WebSocket.OPEN ||
            !this.currentRoomId
        ) {
            return;
        }

        const messageData = {
            type: "message",
            message: message,
            room_id: this.currentRoomId,
        };

        this.ws.send(JSON.stringify(messageData));
        this.messageInput.value = "";
        this.autoResizeTextarea();
    }

    displayMessage(data, animate = true) {
        const messageDiv = document.createElement("div");
        messageDiv.className = "message";

        const isOwn = data.sender_role === "support";
        if (isOwn) {
            messageDiv.classList.add("own");
        }

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = data.sender_name
            ? data.sender_name.charAt(0).toUpperCase()
            : "U";

        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        bubble.textContent = data.message;

        const meta = document.createElement("div");
        meta.className = "message-meta";

        const senderName = document.createElement("span");
        senderName.textContent = data.sender_name || "User";

        const timestamp = document.createElement("span");
        const date = new Date(data.created_at || data.timestamp);
        timestamp.textContent = date.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
        });

        meta.appendChild(senderName);
        meta.appendChild(timestamp);

        contentDiv.appendChild(bubble);
        contentDiv.appendChild(meta);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator(senderName) {
        const existing = document.getElementById("typingIndicator");
        if (existing) {
            existing.remove();
        }

        const typingDiv = document.createElement("div");
        typingDiv.id = "typingIndicator";
        typingDiv.className = "message";
        typingDiv.innerHTML = `
                        <div class="message-avatar">
                            ${senderName.charAt(0).toUpperCase()}
                        </div>
                        <div class="message-content">
                            <div class="message-bubble">
                                <div class="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                    `;

        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();

        setTimeout(() => {
            const indicator =
                document.getElementById("typingIndicator");
            if (indicator) {
                indicator.remove();
            }
        }, 3000);
    }

    async closeCurrentRoom() {
        if (!this.currentRoomId) return;

        if (
            !confirm(
                "Are you sure you want to close this chat room?",
            )
        ) {
            return;
        }

        try {
            const response = await fetch(
                `/chat/rooms/${this.currentRoomId}/close`,
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${this.token}`,
                    },
                },
            );

            if (response.ok) {
                this.showNotification(
                    "Chat room closed",
                    "success",
                );
                this.rooms.delete(this.currentRoomId);
                this.currentRoomId = null;
                this.emptyState.classList.remove("hidden");
                this.chatSection.classList.add("hidden");
                this.refreshRoomsList();
            }
        } catch (error) {
            console.error("Error closing room:", error);
            this.showNotification("Failed to close room", "error");
        }
    }

    autoResizeTextarea() {
        this.messageInput.style.height = "auto";
        this.messageInput.style.height =
            Math.min(this.messageInput.scrollHeight, 120) + "px";
    }

    updateStatus(connected) {
        if (connected) {
            this.statusIndicator.classList.add("connected");
            this.statusText.textContent = "Connected";
        } else {
            this.statusIndicator.classList.remove("connected");
            this.statusText.textContent = "Disconnected";
        }
    }

    updateStats() {
        this.activeRoomsCount.textContent = this.rooms.size;
        const unread = Array.from(this.rooms.values()).reduce(
            (sum, room) => sum + (room.unread || 0),
            0,
        );
        this.unreadCount.textContent = unread;
    }

    showNotification(message, type = "success") {
        const notification = document.createElement("div");
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop =
            this.messagesContainer.scrollHeight;
    }
}

// Initialize support dashboard when page loads
const dashboard = new SupportDashboard();