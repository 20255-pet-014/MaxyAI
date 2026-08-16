// ==========================================================================
// MAXY AI Dashboard • Interactive Logic & SSE Client
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    init3DTilt();
    initTabs();
    loadDashboardData();
    setupEventListeners();
});

let currentTopic = "research_function_calling";
let sandboxSnippets = [];

// ==========================================================================
// 3D Card Tilt Effect
// ==========================================================================

function init3DTilt() {
    const cards = document.querySelectorAll("[data-tilt]");
    cards.forEach((card) => {
        card.addEventListener("mousemove", (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / centerY) * -8;
            const rotateY = ((x - centerX) / centerX) * 8;
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
        });

        card.addEventListener("mouseleave", () => {
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)`;
        });
    });
}

// ==========================================================================
// Tab Switching
// ==========================================================================

function initTabs() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    tabButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            tabButtons.forEach((b) => b.classList.remove("active"));
            tabPanes.forEach((p) => p.classList.remove("active"));

            btn.classList.add("active");
            const target = btn.getAttribute("data-tab");
            const targetPane = document.getElementById(target);
            if (targetPane) {
                targetPane.classList.add("active");
            }
        });
    });
}

// ==========================================================================
// Fetch & Load Dashboard Artifacts
// ==========================================================================

async function loadDashboardData() {
    try {
        // 1. Fetch Topics
        const topicsRes = await fetch("/api/topics");
        if (topicsRes.ok) {
            const topics = await topicsRes.json();
            const selectEl = document.getElementById("topic-select");
            selectEl.innerHTML = "";
            topics.forEach((t) => {
                const opt = document.createElement("option");
                opt.value = t.id;
                opt.textContent = `${t.id} (${(t.research_size_bytes / 1024).toFixed(0)} KB)`;
                if (t.id === currentTopic) opt.selected = true;
                selectEl.appendChild(opt);
            });
        }

        // 2. Fetch Artifacts for current topic
        loadTopicArtifacts(currentTopic);
    } catch (err) {
        logToTerminal(`[ERROR] Failed to load initial data: ${err}`, "error");
    }
}

async function loadTopicArtifacts(topic) {
    try {
        const res = await fetch(`/api/artifacts/${topic}`);
        if (!res.ok) return;

        const data = await res.json();

        // Render Article HTML inside container
        const articleContainer = document.getElementById("article-html-container");
        if (data.article_html) {
            // Strip external html/head/body to embed safely
            const parser = new DOMParser();
            const doc = parser.parseFromString(data.article_html, "text/html");
            const wrapper = doc.querySelector(".article-wrapper") || doc.body;
            articleContainer.innerHTML = wrapper.innerHTML;
        } else if (data.article_md) {
            articleContainer.innerHTML = `<pre class="code-preview">${escapeHtml(data.article_md)}</pre>`;
        } else {
            articleContainer.innerHTML = `<div class="loading-spinner">No article.md found yet. Click 'Run Writer' to generate.</div>`;
        }

        // Render Research MD
        const researchEl = document.getElementById("research-raw-content");
        researchEl.textContent = data.research_md || "No research.md found.";

        // Render Sandbox Files
        sandboxSnippets = data.sandbox_files || [];
        document.getElementById("sandbox-count").textContent = sandboxSnippets.length;
        renderSandboxList(sandboxSnippets);
    } catch (err) {
        logToTerminal(`[ERROR] Failed to load artifacts: ${err}`, "error");
    }
}

function renderSandboxList(files) {
    const listEl = document.getElementById("sandbox-file-list");
    listEl.innerHTML = "";

    if (files.length === 0) {
        listEl.innerHTML = `<span style="font-size: 0.75rem; color: #64748b;">No sandbox files.</span>`;
        return;
    }

    files.forEach((file, index) => {
        const btn = document.createElement("button");
        btn.className = `sandbox-file-btn ${index === 0 ? "active" : ""}`;
        btn.textContent = file.name;
        btn.onclick = () => {
            document.querySelectorAll(".sandbox-file-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            showSandboxFile(file);
        };
        listEl.appendChild(btn);
    });

    if (files.length > 0) {
        showSandboxFile(files[0]);
    }
}

function showSandboxFile(file) {
    document.getElementById("current-sandbox-file").textContent = file.name;
    document.getElementById("sandbox-code-preview").textContent = file.content;
}

// ==========================================================================
// Event Listeners & Trigger Actions
// ==========================================================================

function setupEventListeners() {
    // Topic Change
    document.getElementById("topic-select").addEventListener("change", (e) => {
        currentTopic = e.target.value;
        logToTerminal(`[TOPIC] Switched active topic to '${currentTopic}'.`, "info");
        loadTopicArtifacts(currentTopic);
    });

    // Clear Terminal Logs
    document.getElementById("btn-clear-logs").addEventListener("click", () => {
        document.getElementById("terminal-stream").innerHTML = "";
    });

    // Copy Article
    document.getElementById("btn-copy-article").addEventListener("click", () => {
        const researchText = document.getElementById("article-html-container").innerText;
        navigator.clipboard.writeText(researchText);
        showToast("Article copied to clipboard!");
    });

    // Copy Research
    document.getElementById("btn-copy-research").addEventListener("click", () => {
        const researchText = document.getElementById("research-raw-content").textContent;
        navigator.clipboard.writeText(researchText);
        showToast("Research copied to clipboard!");
    });

    // Trigger Run Buttons
    document.getElementById("btn-run-phase2").addEventListener("click", () => triggerAgentRun("phase2"));
    document.getElementById("btn-run-phase3").addEventListener("click", () => triggerAgentRun("phase3"));
    document.getElementById("btn-run-all").addEventListener("click", () => triggerAgentRun("all"));
}

// ==========================================================================
// Real-Time SSE Agent Execution
// ==========================================================================

async function triggerAgentRun(phase) {
    const progressContainer = document.getElementById("progress-container");
    const progressFill = document.getElementById("progress-fill");
    const progressText = document.getElementById("progress-stage-text");
    const progressPercent = document.getElementById("progress-percent");

    progressContainer.style.display = "flex";
    progressFill.style.width = "5%";
    progressPercent.textContent = "5%";
    progressText.textContent = `Launching ${phase.toUpperCase()}...`;

    logToTerminal(`[LAUNCH] Triggering run '${phase}' for '${currentTopic}'...`, "system");

    try {
        const response = await fetch("/api/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ topic: currentTopic, phase: phase }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split("\n");

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const eventData = JSON.parse(line.slice(6));
                    progressFill.style.width = `${eventData.progress}%`;
                    progressPercent.textContent = `${eventData.progress}%`;
                    progressText.textContent = eventData.message;

                    logToTerminal(eventData.message, eventData.stage === "error" ? "error" : "info");

                    if (eventData.stage === "complete") {
                        logToTerminal(`[SUCCESS] Run finished successfully. Refreshing artifacts...`, "success");
                        loadTopicArtifacts(currentTopic);
                        setTimeout(() => {
                            progressContainer.style.display = "none";
                        }, 2500);
                    }
                }
            }
        }
    } catch (err) {
        logToTerminal(`[ERROR] Agent execution failed: ${err}`, "error");
        progressContainer.style.display = "none";
    }
}

// ==========================================================================
// Helper Utilities
// ==========================================================================

function logToTerminal(message, type = "info") {
    const stream = document.getElementById("terminal-stream");
    const line = document.createElement("div");
    const timestamp = new Date().toLocaleTimeString();
    line.className = `log-line ${type}`;
    line.textContent = `[${timestamp}] ${message}`;
    stream.appendChild(line);
    stream.scrollTop = stream.scrollHeight;
}

function showToast(msg) {
    const toast = document.createElement("div");
    toast.className = "pill-value";
    toast.style.cssText = "position: fixed; bottom: 2rem; right: 2rem; background: #00f2fe; color: #000; padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 700; z-index: 999; box-shadow: 0 10px 25px rgba(0,242,254,0.5);";
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2500);
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}
