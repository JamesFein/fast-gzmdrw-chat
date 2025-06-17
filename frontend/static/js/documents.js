/**
 * 文档管理页面JavaScript
 */

class DocumentManager {
  constructor() {
    this.documents = [];
    this.init();
  }

  init() {
    this.bindEvents();
    this.loadDocuments();
  }

  bindEvents() {
    // 文件选择
    const fileInput = document.getElementById("fileInput");
    fileInput.addEventListener("change", (e) => this.handleFileSelect(e));

    // 刷新按钮
    const refreshBtn = document.getElementById("refreshBtn");
    refreshBtn.addEventListener("click", () => this.loadDocuments());

    // 拖拽上传
    const uploadSection = document.getElementById("uploadSection");
    uploadSection.addEventListener("dragover", (e) => this.handleDragOver(e));
    uploadSection.addEventListener("dragleave", (e) => this.handleDragLeave(e));
    uploadSection.addEventListener("drop", (e) => this.handleDrop(e));
  }

  // 显示提示信息
  showAlert(message, type = "info") {
    const alertContainer = document.getElementById("alertContainer");
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert ${type}`;
    alertDiv.innerHTML = `
            <i class="fas fa-${
              type === "success"
                ? "check-circle"
                : type === "error"
                ? "exclamation-circle"
                : "info-circle"
            }"></i>
            ${message}
        `;
    alertDiv.style.display = "block";

    alertContainer.innerHTML = "";
    alertContainer.appendChild(alertDiv);

    // 3秒后自动隐藏
    setTimeout(() => {
      alertDiv.style.display = "none";
    }, 3000);
  }

  // 加载文档列表
  async loadDocuments() {
    try {
      const response = await fetch("/api/documents");
      const data = await response.json();

      if (data.success) {
        this.documents = data.documents;
        this.renderDocuments();
        this.updateStats(data);
      } else {
        this.showAlert(data.message, "error");
      }
    } catch (error) {
      console.error("加载文档列表失败:", error);
      this.showAlert("加载文档列表失败", "error");
    }
  }

  // 渲染文档列表
  renderDocuments() {
    const container = document.getElementById("documentsContent");
    const statsBar = document.getElementById("statsBar");

    if (this.documents.length === 0) {
      container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fas fa-folder-open"></i>
                    </div>
                    <h3>暂无文档</h3>
                    <p>请上传TXT文件开始使用</p>
                </div>
            `;
      statsBar.style.display = "none";
      return;
    }

    const tableHTML = `
            <table class="documents-table">
                <thead>
                    <tr>
                        <th>文件名</th>
                        <th>文档块数</th>
                        <th>文件大小</th>
                        <th>修改时间</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.documents
                      .map(
                        (doc) => `
                        <tr>
                            <td>
                                <div class="file-name">${doc.filename}</div>
                                <div class="file-stats">${doc.file_path}</div>
                            </td>
                            <td>${doc.chunks_count}</td>
                            <td>${this.formatFileSize(doc.file_size)}</td>
                            <td>${this.formatDate(doc.file_modified)}</td>
                            <td>
                                <button class="delete-btn" onclick="documentManager.deleteDocument('${
                                  doc.filename
                                }')">
                                    <i class="fas fa-trash"></i> 删除
                                </button>
                            </td>
                        </tr>
                    `
                      )
                      .join("")}
                </tbody>
            </table>
        `;

    container.innerHTML = tableHTML;
    statsBar.style.display = "flex";
  }

  // 更新统计信息
  updateStats(data) {
    document.getElementById("docCount").textContent = data.documents.length;
    document.getElementById("chunkCount").textContent = data.total_chunks;
    document.getElementById("lastUpdate").textContent =
      new Date().toLocaleString();
  }

  // 格式化文件大小
  formatFileSize(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  // 格式化日期
  formatDate(timestamp) {
    if (!timestamp) return "-";
    const date = new Date(parseFloat(timestamp) * 1000);
    return date.toLocaleString();
  }

  // 处理文件选择
  handleFileSelect(event) {
    const files = event.target.files;
    this.uploadFiles(files);
  }

  // 处理拖拽
  handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add("dragover");
  }

  handleDragLeave(event) {
    event.preventDefault();
    event.currentTarget.classList.remove("dragover");
  }

  handleDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove("dragover");
    const files = event.dataTransfer.files;
    this.uploadFiles(files);
  }

  // 上传文件
  async uploadFiles(files) {
    for (let file of files) {
      if (!file.name.endsWith(".txt")) {
        this.showAlert(`文件 ${file.name} 不是TXT格式，已跳过`, "error");
        continue;
      }

      await this.uploadSingleFile(file);
    }

    // 重新加载文档列表
    this.loadDocuments();
  }

  // 上传单个文件
  async uploadSingleFile(file) {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/documents/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        if (data.replaced) {
          this.showAlert(
            `文件 ${data.filename} 上传成功！替换了同名文件（旧: ${data.old_chunks}块 → 新: ${data.new_chunks}块）<br>已保存到 data 目录`,
            "success"
          );
        } else {
          this.showAlert(
            `文件 ${data.filename} 上传成功！生成了 ${data.new_chunks} 个文档块<br>已保存到 data 目录`,
            "success"
          );
        }
      } else {
        this.showAlert(`上传失败: ${data.message}`, "error");
      }
    } catch (error) {
      console.error("上传文件失败:", error);
      this.showAlert(`上传文件 ${file.name} 失败`, "error");
    }
  }

  // 删除文档
  async deleteDocument(filename) {
    if (
      !confirm(
        `确定要删除文档 "${filename}" 吗？\n\n此操作将删除：\n- ChromaDB中的所有相关向量和文档块\n- docstore中的所有相关节点\n- 所有相关元数据\n- data目录中的文件\n\n此操作不可恢复！`
      )
    ) {
      return;
    }

    try {
      const response = await fetch(
        `/api/documents/${encodeURIComponent(filename)}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (data.success) {
        let message = `文档 ${data.filename} 删除成功！删除了 ${data.deleted_chunks} 个文档块`;
        if (data.file_deleted_from_disk) {
          message += "<br>已从 data 目录删除文件";
        } else {
          message += "<br>仅删除了数据库记录";
        }
        this.showAlert(message, "success");
        this.loadDocuments();
      } else {
        this.showAlert(`删除失败: ${data.message}`, "error");
      }
    } catch (error) {
      console.error("删除文档失败:", error);
      this.showAlert(`删除文档 ${filename} 失败`, "error");
    }
  }
}

// 初始化文档管理器
const documentManager = new DocumentManager();
