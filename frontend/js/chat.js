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
    this.messageInputContainer = document.getElementById("messageInputContainer");
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
    this.messageInputContainer.style.display = "flex";
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
    this.messageInputContainer.style.display = "none";
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
    // Get template from HTML
    const template = document.getElementById("messageTemplate");
    const messageDiv = template.content.cloneNode(true).firstElementChild;

    // Determine if message is from current user
    const isOwn = data.sender_id === this.userId;
    const isSupport = data.sender_role === "support";

    if (isOwn) {
      messageDiv.classList.add("own");
    } else if (isSupport) {
      messageDiv.classList.add("support");
    }

    // Set avatar
    const avatar = messageDiv.querySelector(".message-avatar");
    avatar.textContent = data.sender_name
      ? data.sender_name.charAt(0).toUpperCase()
      : "U";

    // Set message content
    const bubble = messageDiv.querySelector(".message-bubble");
    bubble.textContent = data.message;

    // Set metadata
    const senderName = messageDiv.querySelector(".sender-name");
    senderName.textContent = data.sender_name || "User";

    const timestamp = messageDiv.querySelector(".timestamp");
    const date = new Date(data.created_at || data.timestamp);
    timestamp.textContent = date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    this.messagesContainer.appendChild(messageDiv);
    this.scrollToBottom();
  }

  showTypingIndicator(senderName) {
    // Remove existing typing indicator
    const existing = document.getElementById("typingIndicator");
    if (existing) {
      existing.remove();
    }

    // Get template from HTML
    const template = document.getElementById("typingIndicatorTemplate");
    const typingDiv = template.content.cloneNode(true).firstElementChild;

    // Set avatar
    const avatar = typingDiv.querySelector(".message-avatar");
    avatar.textContent = senderName.charAt(0).toUpperCase();

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

    // Гарантируем, что контейнер ввода не сжимается
    const inputContainer = document.querySelector('.message-input-container');
    if (inputContainer) {
      inputContainer.style.minHeight = '92px';
    }

    if (!this.isSupport && this.ws && this.ws.readyState === WebSocket.OPEN) {
      clearTimeout(this.typingTimeout);

      this.ws.send(JSON.stringify({ type: "typing" }));

      this.typingTimeout = setTimeout(() => {
        // Stop typing indicator after 2 seconds
      }, 2000);
    }
  }

  autoResizeTextarea() {
    // Сохраняем минимальную высоту
    this.messageInput.style.height = "auto";
    const newHeight = Math.min(this.messageInput.scrollHeight, 100);
    this.messageInput.style.height = Math.max(newHeight, 44) + "px"; // Минимальная высота 44px
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
    // Get template from HTML
    const template = document.getElementById("notificationTemplate");
    const notification = template.content.cloneNode(true).firstElementChild;
    
    notification.className = `notification ${type}`;
    const textElement = notification.querySelector(".notification-text");
    textElement.textContent = message;
    
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
