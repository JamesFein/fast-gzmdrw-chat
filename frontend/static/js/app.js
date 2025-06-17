/**
 * RAG聊天应用前端JavaScript
 * 实现聊天界面的交互功能
 */

class ChatApp {
  constructor() {
    this.apiBase = "/api";
    this.chatHistory = [];
    this.isLoading = false;

    // DOM元素
    this.elements = {
      chatMessages: document.getElementById("chatMessages"),
      messageInput: document.getElementById("messageInput"),
      sendBtn: document.getElementById("sendBtn"),
      loadDocsBtn: document.getElementById("loadDocsBtn"),
      statusBtn: document.getElementById("statusBtn"),
      clearBtn: document.getElementById("clearBtn"),
      charCount: document.getElementById("charCount"),
      connectionStatus: document.getElementById("connectionStatus"),
      documentCount: document.getElementById("documentCount"),
      storageSize: document.getElementById("storageSize"),
      loadingOverlay: document.getElementById("loadingOverlay"),
      loadingText: document.getElementById("loadingText"),
      modal: document.getElementById("modal"),
      modalTitle: document.getElementById("modalTitle"),
      modalContent: document.getElementById("modalContent"),
      modalClose: document.getElementById("modalClose"),
    };

    this.init();
  }

  init() {
    console.log("初始化聊天应用...");
    this.bindEvents();
    this.loadChatHistory();
    this.updateStatus();
    this.autoResizeTextarea();

    // 检查连接状态
    this.checkConnection();
  }

  bindEvents() {
    // 发送消息
    this.elements.sendBtn.addEventListener("click", () => this.sendMessage());

    // 回车发送消息
    this.elements.messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // 字符计数
    this.elements.messageInput.addEventListener("input", () => {
      this.updateCharCount();
      this.autoResizeTextarea();
    });

    // 加载文档
    this.elements.loadDocsBtn.addEventListener("click", () =>
      this.loadDocuments()
    );

    // 查看状态
    this.elements.statusBtn.addEventListener("click", () => this.showStatus());

    // 清空对话
    this.elements.clearBtn.addEventListener("click", () => this.clearChat());

    // 模态框关闭
    this.elements.modalClose.addEventListener("click", () => this.hideModal());
    this.elements.modal.addEventListener("click", (e) => {
      if (e.target === this.elements.modal) {
        this.hideModal();
      }
    });

    // ESC键关闭模态框
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        this.hideModal();
      }
    });
  }

  async sendMessage() {
    const message = this.elements.messageInput.value.trim();
    if (!message || this.isLoading) return;

    console.log("发送消息:", message);

    // 添加用户消息到界面
    this.addMessage("user", message);

    // 清空输入框
    this.elements.messageInput.value = "";
    this.updateCharCount();
    this.autoResizeTextarea();

    // 显示加载状态
    this.showLoading("正在思考中...");

    try {
      const response = await fetch(`${this.apiBase}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: message,
          max_results: 5,
          similarity_threshold: 0.7,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("收到回复:", data);

      if (data.error) {
        throw new Error(data.message || "服务器返回错误");
      }

      // 添加助手回复到界面
      this.addMessage("assistant", data.answer, data.sources);
    } catch (error) {
      console.error("发送消息失败:", error);
      this.addMessage(
        "assistant",
        `抱歉，发生了错误：${error.message}`,
        null,
        true
      );
    } finally {
      this.hideLoading();
    }
  }

  addMessage(type, content, sources = null, isError = false) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${type}-message`;

    const avatarDiv = document.createElement("div");
    avatarDiv.className = "message-avatar";
    avatarDiv.innerHTML =
      type === "user"
        ? '<i class="fas fa-user"></i>'
        : '<i class="fas fa-robot"></i>';

    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";

    const textDiv = document.createElement("div");
    textDiv.className = "message-text";
    if (isError) {
      textDiv.classList.add("text-error");
    }
    textDiv.innerHTML = this.formatMessage(content);

    contentDiv.appendChild(textDiv);

    // 添加源信息
    if (sources && sources.length > 0) {
      const sourcesDiv = this.createSourcesDiv(sources);
      contentDiv.appendChild(sourcesDiv);
    }

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);

    this.elements.chatMessages.appendChild(messageDiv);
    this.scrollToBottom();

    // 保存到历史记录
    this.chatHistory.push({
      id: Date.now().toString(),
      type,
      content,
      sources,
      timestamp: Date.now(),
    });
    this.saveChatHistory();
  }

  createSourcesDiv(sources) {
    const sourcesDiv = document.createElement("div");
    sourcesDiv.className = "message-sources";

    const titleDiv = document.createElement("h4");
    titleDiv.textContent = "参考来源：";
    sourcesDiv.appendChild(titleDiv);

    sources.forEach((source) => {
      const sourceDiv = document.createElement("div");
      sourceDiv.className = "source-item";

      sourceDiv.innerHTML = `
                <div class="source-filename">
                    📄 ${source.filename}
                    <span class="source-score">相似度: ${(
                      source.score * 100
                    ).toFixed(1)}%</span>
                </div>
                <div class="source-content">${this.truncateText(
                  source.content,
                  150
                )}</div>
            `;

      sourcesDiv.appendChild(sourceDiv);
    });

    return sourcesDiv;
  }

  formatMessage(content) {
    // 简单的文本格式化
    return content
      .replace(/\n/g, "<br>")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>");
  }

  truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  }

  async loadDocuments() {
    if (this.isLoading) return;

    console.log("开始加载文档...");
    this.showLoading("正在加载文档...");

    try {
      const response = await fetch(`${this.apiBase}/load-documents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("文档加载结果:", data);

      if (data.error) {
        throw new Error(data.message || "加载文档失败");
      }

      // 显示加载结果
      this.showModal("文档加载完成", this.formatLoadResult(data));

      // 更新状态
      this.updateStatus();
    } catch (error) {
      console.error("加载文档失败:", error);
      this.showModal(
        "加载失败",
        `<p class="text-error">加载文档时发生错误：${error.message}</p>`
      );
    } finally {
      this.hideLoading();
    }
  }

  formatLoadResult(data) {
    let html = `
            <div class="text-center">
                <p class="text-success"><strong>✅ 文档加载成功！</strong></p>
                <p>处理了 <strong>${
                  data.documents_processed
                }</strong> 个文档</p>
                <p>创建了 <strong>${data.chunks_created}</strong> 个文本块</p>
                <p>处理时间: <strong>${data.processing_time.toFixed(
                  2
                )}</strong> 秒</p>
            </div>
        `;

    if (data.replaced_files && data.replaced_files.length > 0) {
      html += `
                <div style="margin-top: 1rem;">
                    <h4>🔄 替换的文件:</h4>
                    <ul>
                        ${data.replaced_files
                          .map(
                            (file) =>
                              `<li>${file.filename} (${file.old_chunks} → ${file.new_chunks} 块)</li>`
                          )
                          .join("")}
                    </ul>
                </div>
            `;
    }

    if (data.new_files && data.new_files.length > 0) {
      html += `
                <div style="margin-top: 1rem;">
                    <h4>📄 新增的文件:</h4>
                    <ul>
                        ${data.new_files
                          .map((file) => `<li>${file}</li>`)
                          .join("")}
                    </ul>
                </div>
            `;
    }

    return html;
  }

  async showStatus() {
    console.log("查看系统状态...");
    this.showLoading("获取状态信息...");

    try {
      const response = await fetch(`${this.apiBase}/status`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("系统状态:", data);

      if (data.error) {
        throw new Error(data.message || "获取状态失败");
      }

      const statusHtml = `
                <div class="text-center">
                    <p><strong>📊 系统状态</strong></p>
                    <div style="text-align: left; margin-top: 1rem;">
                        <p><strong>状态:</strong> <span class="text-success">${
                          data.status
                        }</span></p>
                        <p><strong>文档数量:</strong> ${
                          data.documents_count
                        }</p>
                        <p><strong>存储大小:</strong> ${data.storage_size}</p>
                        <p><strong>最后更新:</strong> ${new Date(
                          data.last_updated
                        ).toLocaleString()}</p>
                    </div>
                </div>
            `;

      this.showModal("系统状态", statusHtml);
    } catch (error) {
      console.error("获取状态失败:", error);
      this.showModal(
        "状态获取失败",
        `<p class="text-error">获取系统状态时发生错误：${error.message}</p>`
      );
    } finally {
      this.hideLoading();
    }
  }

  clearChat() {
    if (confirm("确定要清空所有对话历史吗？此操作不可撤销。")) {
      console.log("清空对话历史");

      // 清空界面（保留欢迎消息）
      const welcomeMessage = this.elements.chatMessages.querySelector(
        ".message.assistant-message"
      );
      this.elements.chatMessages.innerHTML = "";
      if (welcomeMessage) {
        this.elements.chatMessages.appendChild(welcomeMessage);
      }

      // 清空历史记录
      this.chatHistory = [];
      this.saveChatHistory();
    }
  }

  async updateStatus() {
    try {
      const response = await fetch(`${this.apiBase}/status`);

      if (response.ok) {
        const data = await response.json();

        // 更新连接状态
        const statusIndicator =
          this.elements.connectionStatus.querySelector(".status-indicator");
        const statusText = this.elements.connectionStatus.querySelector("span");
        statusIndicator.className = "fas fa-circle status-indicator connected";
        statusText.textContent = "连接状态: 已连接";

        // 更新文档数量
        this.elements.documentCount.querySelector(
          "span"
        ).textContent = `文档: ${data.documents_count}`;

        // 更新存储大小
        this.elements.storageSize.querySelector(
          "span"
        ).textContent = `存储: ${data.storage_size}`;
      } else {
        throw new Error("连接失败");
      }
    } catch (error) {
      console.error("更新状态失败:", error);

      // 更新连接状态为断开
      const statusIndicator =
        this.elements.connectionStatus.querySelector(".status-indicator");
      const statusText = this.elements.connectionStatus.querySelector("span");
      statusIndicator.className = "fas fa-circle status-indicator disconnected";
      statusText.textContent = "连接状态: 断开连接";
    }
  }

  async checkConnection() {
    console.log("检查服务器连接...");
    await this.updateStatus();

    // 定期检查连接状态
    setInterval(() => {
      this.updateStatus();
    }, 30000); // 每30秒检查一次
  }

  showLoading(text = "处理中...") {
    this.isLoading = true;
    this.elements.loadingText.textContent = text;
    this.elements.loadingOverlay.classList.remove("hidden");
    this.elements.sendBtn.disabled = true;
  }

  hideLoading() {
    this.isLoading = false;
    this.elements.loadingOverlay.classList.add("hidden");
    this.elements.sendBtn.disabled = false;
  }

  showModal(title, content) {
    this.elements.modalTitle.textContent = title;
    this.elements.modalContent.innerHTML = content;
    this.elements.modal.classList.remove("hidden");
  }

  hideModal() {
    this.elements.modal.classList.add("hidden");
  }

  updateCharCount() {
    const length = this.elements.messageInput.value.length;
    this.elements.charCount.textContent = `${length}/1000`;

    if (length > 900) {
      this.elements.charCount.style.color = "#ef4444";
    } else if (length > 800) {
      this.elements.charCount.style.color = "#f59e0b";
    } else {
      this.elements.charCount.style.color = "#6b7280";
    }
  }

  autoResizeTextarea() {
    const textarea = this.elements.messageInput;
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
  }

  scrollToBottom() {
    this.elements.chatMessages.scrollTop =
      this.elements.chatMessages.scrollHeight;
  }

  loadChatHistory() {
    try {
      const saved = localStorage.getItem("chat_history");
      if (saved) {
        this.chatHistory = JSON.parse(saved);
        console.log("加载聊天历史:", this.chatHistory.length, "条消息");

        // 重建聊天界面（跳过欢迎消息）
        this.chatHistory.forEach((msg) => {
          if (msg.type !== "welcome") {
            this.addMessageToUI(msg.type, msg.content, msg.sources);
          }
        });
      }
    } catch (error) {
      console.error("加载聊天历史失败:", error);
      this.chatHistory = [];
    }
  }

  saveChatHistory() {
    try {
      localStorage.setItem("chat_history", JSON.stringify(this.chatHistory));
    } catch (error) {
      console.error("保存聊天历史失败:", error);
    }
  }

  addMessageToUI(type, content, sources = null, isError = false) {
    // 这是一个辅助方法，用于重建界面时添加消息，不保存到历史记录
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${type}-message`;

    const avatarDiv = document.createElement("div");
    avatarDiv.className = "message-avatar";
    avatarDiv.innerHTML =
      type === "user"
        ? '<i class="fas fa-user"></i>'
        : '<i class="fas fa-robot"></i>';

    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";

    const textDiv = document.createElement("div");
    textDiv.className = "message-text";
    if (isError) {
      textDiv.classList.add("text-error");
    }
    textDiv.innerHTML = this.formatMessage(content);

    contentDiv.appendChild(textDiv);

    // 添加源信息
    if (sources && sources.length > 0) {
      const sourcesDiv = this.createSourcesDiv(sources);
      contentDiv.appendChild(sourcesDiv);
    }

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);

    this.elements.chatMessages.appendChild(messageDiv);
  }
}

// 应用初始化
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM加载完成，初始化聊天应用...");
  window.chatApp = new ChatApp();
});
