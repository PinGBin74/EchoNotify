class ChatApp {
  constructor() {
    this.ws = null;
    this.token = null;
    this.isSupport = false;
    this.roomId = null;
    this.currentRoomId = null;
    this.userId = null;
    this.typingTimeout = null;

    this.initElements();
    this.attachEventListeners();
  }

  initElements() {
    this.loginSection = document.getElementById("loginSection");
    this.chatSection = document.getElementById("chatSection");
    this.tokenInput = document.getElementById("tokenInput");
    this.roomInput = document.getElementById("roomInput");
    this.supportMode = document.getElementById("supportMode");
    this.connectButton = document.getElementById("connectButton");
    this.messagesContainer = document.getElementById("messagesContainer");
    this.messageInput = document.getElementById("messageInput");
    this.sendButton = document.getElementById("sendButton");
    this.statusIndicator = document.getElementById("statusIndicator");
    this.statusText = document.getElementById("statusText");
    this.roomInfo = document.getElementById("roomInfo");
  }

  attachEventListeners() {
    this.connectButton.addEventListener("click", () => this.connect());
    this.sendButton.addEventListener("click", () => this.sendMessage());
    this.messageInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
    this.messageInput.addEventListener("input", () => this.handleTyping());
  }

  connect() {
    this.token = this.tokenInput.value.trim();
    this.isSupport = this.supportMode.checked;
    this.roomId = this.roomInput.value.trim() || null;

    if (!this.token) {
      this.showNotification("Please enter your access token", "error");
      return;
    }

    this.connectButton.disabled = true;
    this.connectButton.textContent = "Connecting...";

    // Change to your WebSocket URL
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = window.location.host || "localhost:8000";
    const wsUrl = `${wsProtocol}//${wsHost}/chat/ws?token=${this.token}&is_support=${this.isSupport}`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => this.onOpen();
    this.ws.onmessage = (event) => this.onMessage(event);
    this.ws.onclose = () => this.onClose();
    this.ws.onerror = (error) => this.onError(error);
  }

  onOpen() {
    console.log("WebSocket connected");
    this.updateStatus(true);
    this.loginSection.classList.add("hidden");
    this.chatSection.classList.remove("hidden");
    this.sendButton.disabled = false;
    this.showNotification("Connected to chat", "success");
  }

  onMessage(event) {
    try {
      const data = JSON.parse(event.data);
      console.log("Received message:", data);

      if (data.type === "auth") {
        this.userId = data.user_id;
        console.log("User authenticated:", this.userId);
      } else if (data.type === "history") {
        this.currentRoomId = data.room_id;
        const messages = data.messages;
        this.roomId = data.room_id;
        this.updateRoomInfo();
        messages.forEach((msg) => this.displayMessage(msg, false));
      } else if (data.type === "message") {
        this.roomId = data.room_id;
        this.displayMessage(data);
      } else if (data.type === "notification") {
        this.showNotification(data.message, "success");
      } else if (data.type === "typing") {
        this.showTypingIndicator(data.sender_name);
      }
    } catch (error) {
      console.error("Error parsing message:", error);
    }
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

  sendMessage() {
    const message = this.messageInput.value.trim();
    if (!message || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    const messageData = {
      type: "message",
      message: message,
      room_id: this.roomId || this.currentRoomId,
    };

    this.ws.send(JSON.stringify(messageData));
    this.messageInput.value = "";
    this.autoResizeTextarea();
  }

  displayMessage(data, animate = true) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "message";

    // Determine if message is from current user
    const isOwn = data.sender_id === this.userId;
    const isSupport = data.sender_role === "support";

    if (isOwn) {
      messageDiv.classList.add("own");
    } else if (isSupport) {
      messageDiv.classList.add("support");
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
    // Remove existing typing indicator
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

    // Remove after 3 seconds
    setTimeout(() => {
      const indicator = document.getElementById("typingIndicator");
      if (indicator) {
        indicator.remove();
      }
    }, 3000);
  }

  handleTyping() {
    this.autoResizeTextarea();

    if (!this.isSupport && this.ws && this.ws.readyState === WebSocket.OPEN) {
      clearTimeout(this.typingTimeout);

      this.ws.send(JSON.stringify({ type: "typing" }));

      this.typingTimeout = setTimeout(() => {
        // Stop typing indicator after 2 seconds
      }, 2000);
    }
  }

  autoResizeTextarea() {
    this.messageInput.style.height = "auto";
    this.messageInput.style.height =
      Math.min(this.messageInput.scrollHeight, 100) + "px";
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

  updateRoomInfo() {
    if (this.roomId) {
      this.roomInfo.textContent = `Room ID: ${this.roomId}`;
      this.roomInfo.classList.remove("hidden");
    }
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
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }
}

// Initialize chat app when page loads
const chat = new ChatApp();
