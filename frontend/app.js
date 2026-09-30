// Codebase Understanding Agent - Frontend Application Logic

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const repoSelect = document.getElementById("repo-select");
    const customRepoPath = document.getElementById("custom-repo-path");
    const questionInput = document.getElementById("question-input");
    const btnInvestigate = document.getElementById("btn-investigate");
    const activityTimeline = document.getElementById("activity-timeline");
    const agentStatusLabel = document.getElementById("agent-status-label");
    
    // Result panels & tabs
    const activeQuestionBanner = document.getElementById("active-question-banner");
    const activeQuestionText = document.getElementById("active-question-text");
    const activeRepoBadge = document.getElementById("active-repo-badge");
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    const answerContainer = document.getElementById("answer-container");
    const evidenceContainer = document.getElementById("evidence-container");
    const flowContainer = document.getElementById("flow-container");
    const evidenceBadge = document.getElementById("evidence-badge");
    const flowBadge = document.getElementById("flow-badge");
    
    // Quick question pills
    const pills = document.querySelectorAll(".pill");
    
    // Tools Sandbox Modal Elements
    const btnToggleTools = document.getElementById("btn-toggle-tools");
    const toolsModal = document.getElementById("tools-modal");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const toolTabs = document.querySelectorAll(".tool-tab");
    const toolRepoInput = document.getElementById("tool-repo-input");
    const toolParamContainer = document.getElementById("tool-param-container");
    const btnExecuteTool = document.getElementById("btn-execute-tool");
    const toolOutputPre = document.getElementById("tool-output-pre");
    const toolExecTime = document.getElementById("tool-exec-time");

    let currentSelectedTool = "list_files";

    // 1. Fetch available repositories
    async function loadRepositories() {
        try {
            const resp = await fetch("/api/repositories");
            if (!resp.ok) throw new Error("Failed to load repositories");
            const data = await resp.json();
            
            repoSelect.innerHTML = "";
            if (data.repositories && data.repositories.length > 0) {
                data.repositories.forEach((repo, idx) => {
                    const opt = document.createElement("option");
                    opt.value = repo.name;
                    opt.textContent = `${repo.name} (${repo.type})`;
                    if (idx === 0) opt.selected = true;
                    repoSelect.appendChild(opt);
                });
                toolRepoInput.value = data.repositories[0].name;
            } else {
                repoSelect.innerHTML = `<option value="">No sample repos found (use custom path below)</option>`;
            }
        } catch (err) {
            console.error("Error loading repositories:", err);
            repoSelect.innerHTML = `<option value="sample-auth-service">sample-auth-service (Default)</option>`;
        }
    }

    // 2. Tab Navigation
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));
            
            btn.classList.add("active");
            const targetId = btn.getAttribute("data-target");
            const targetContent = document.getElementById(targetId);
            if (targetContent) targetContent.classList.add("active");
        });
    });

    // 3. Preset Question Pills
    pills.forEach(pill => {
        pill.addEventListener("click", () => {
            questionInput.value = pill.getAttribute("data-query");
            questionInput.focus();
        });
    });

    // 4. Start Agent Investigation
    btnInvestigate.addEventListener("click", async () => {
        const repoPath = customRepoPath.value.trim() || repoSelect.value;
        const question = questionInput.value.trim();

        if (!repoPath) {
            alert("Please select or enter a repository path.");
            return;
        }

        if (!question) {
            alert("Please enter a question about the codebase.");
            questionInput.focus();
            return;
        }

        // Set Loading State
        btnInvestigate.disabled = true;
        btnInvestigate.innerHTML = `
            <svg class="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="2" x2="12" y2="6"></line>
                <line x1="12" y1="18" x2="12" y2="22"></line>
                <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
                <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
                <line x1="2" y1="12" x2="6" y2="12"></line>
                <line x1="18" y1="12" x2="22" y2="12"></line>
                <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
                <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
            </svg>
            <span>Investigating Repository...</span>
        `;
        agentStatusLabel.textContent = "Investigating...";

        // Reset Panels & Banner
        activeQuestionBanner.classList.remove("hidden");
        activeQuestionText.textContent = question;
        activeRepoBadge.textContent = repoPath;

        activityTimeline.innerHTML = `<div class="empty-state-mini">Launching agent investigation loop...</div>`;
        answerContainer.innerHTML = `<div class="empty-state"><h3>Investigating Codebase</h3><p>Tracing files, dependencies, and execution pathways...</p></div>`;
        evidenceContainer.innerHTML = `<div class="empty-state-mini">Collecting evidence...</div>`;
        flowContainer.innerHTML = `<div class="empty-state-mini">Tracing execution...</div>`;
        evidenceBadge.textContent = "0";
        flowBadge.textContent = "0";

        try {
            const resp = await fetch("/api/investigate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    repository_path: repoPath,
                    question: question
                })
            });

            if (!resp.ok) {
                const errData = await resp.json().catch(() => ({}));
                throw new Error(errData.detail || `Server error (${resp.status})`);
            }

            const result = await resp.json();
            renderInvestigationResults(result);

        } catch (err) {
            console.error("Investigation failed:", err);
            activityTimeline.innerHTML += `
                <div class="activity-item">
                    <div class="activity-icon" style="color: var(--accent-rose); background: rgba(244, 63, 94, 0.15);">✕</div>
                    <div class="activity-text-group">
                        <div class="activity-title">Investigation Error</div>
                        <div class="activity-summary">${err.message}</div>
                    </div>
                </div>
            `;
            answerContainer.innerHTML = `
                <div class="empty-state" style="color: var(--accent-rose);">
                    <h3>Investigation Error</h3>
                    <p>${err.message}</p>
                </div>
            `;
        } finally {
            btnInvestigate.disabled = false;
            btnInvestigate.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <span>Start Agent Investigation</span>
            `;
            agentStatusLabel.textContent = "Agent Ready";
        }
    });

    // 5. Render Results
    function renderInvestigationResults(data) {
        // A. Update Question Banner (strictly clean question)
        activeQuestionBanner.classList.remove("hidden");
        activeQuestionText.textContent = data.question;
        activeRepoBadge.textContent = data.repository;

        // B. Render Activity Timeline
        activityTimeline.innerHTML = "";
        if (data.investigation_steps && data.investigation_steps.length > 0) {
            data.investigation_steps.forEach((step) => {
                const item = document.createElement("div");
                item.className = "activity-item";
                item.innerHTML = `
                    <div class="activity-icon">✓</div>
                    <div class="activity-text-group">
                        <div class="activity-title">${step.activity}</div>
                        ${step.result_summary ? `<div class="activity-summary">${step.result_summary}</div>` : ""}
                    </div>
                `;
                activityTimeline.appendChild(item);
            });
        }

        // C. Render Final Answer (Markdown)
        if (window.marked && data.final_answer) {
            answerContainer.innerHTML = marked.parse(data.final_answer);
        } else {
            answerContainer.innerText = data.final_answer || "No answer returned.";
        }

        // D. Render Evidence Cards
        evidenceContainer.innerHTML = "";
        const evidenceList = data.evidence || [];
        evidenceBadge.textContent = evidenceList.length;

        if (evidenceList.length > 0) {
            evidenceList.forEach(ev => {
                const card = document.createElement("div");
                card.className = "evidence-card";
                card.innerHTML = `
                    <div class="evidence-header">
                        <span class="evidence-file">📄 ${ev.file_path}</span>
                        <span class="evidence-lines">Lines ${ev.lines}</span>
                    </div>
                    <div class="evidence-finding">${ev.finding}</div>
                    ${ev.snippet ? `<pre class="evidence-snippet"><code>${escapeHtml(ev.snippet)}</code></pre>` : ""}
                `;
                evidenceContainer.appendChild(card);
            });
        } else {
            evidenceContainer.innerHTML = `<div class="empty-state-mini">No explicit evidence items were cited.</div>`;
        }

        // E. Render Execution Flow
        flowContainer.innerHTML = "";
        const flowList = data.execution_flow || [];
        flowBadge.textContent = flowList.length;

        if (flowList.length > 0) {
            flowList.forEach(node => {
                const card = document.createElement("div");
                card.className = "flow-card";
                card.innerHTML = `
                    <div class="flow-node-bullet">${node.step}</div>
                    <div class="flow-title">${node.component_or_function}</div>
                    <div class="flow-meta">File: ${node.file_path}</div>
                    <div class="flow-desc">${node.description}</div>
                `;
                flowContainer.appendChild(card);
            });
        } else {
            flowContainer.innerHTML = `<div class="empty-state-mini">No multi-step execution flow was required for this query.</div>`;
        }
    }

    // 6. Tools Sandbox Modal Logic
    btnToggleTools.addEventListener("click", () => {
        toolsModal.classList.remove("hidden");
        renderToolInputs();
    });

    btnCloseModal.addEventListener("click", () => {
        toolsModal.classList.add("hidden");
    });

    toolsModal.addEventListener("click", (e) => {
        if (e.target === toolsModal) toolsModal.classList.add("hidden");
    });

    toolTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            toolTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            currentSelectedTool = tab.getAttribute("data-tool");
            renderToolInputs();
        });
    });

    function renderToolInputs() {
        if (currentSelectedTool === "list_files") {
            toolParamContainer.innerHTML = `
                <label>Subpath (optional):</label>
                <input type="text" id="param-subpath" placeholder="e.g. src or empty for root">
            `;
        } else if (currentSelectedTool === "search_code") {
            toolParamContainer.innerHTML = `
                <label>Search Query:</label>
                <input type="text" id="param-query" value="jwt" placeholder="e.g. jwt, authenticate, Task">
            `;
        } else if (currentSelectedTool === "read_file") {
            toolParamContainer.innerHTML = `
                <label>File Path:</label>
                <input type="text" id="param-filepath" value="src/services/authService.js" placeholder="Relative file path">
                <label style="margin-left: 10px; width: 60px;">Lines:</label>
                <input type="number" id="param-startline" value="1" style="width: 70px;">
                <span>to</span>
                <input type="number" id="param-endline" value="60" style="width: 70px;">
            `;
        } else if (currentSelectedTool === "get_dependencies") {
            toolParamContainer.innerHTML = `<span style="font-size: 0.85rem; color: var(--text-dim);">Scans all manifests (package.json, requirements.txt, pyproject.toml, pom.xml, go.mod, Cargo.toml)</span>`;
        } else if (currentSelectedTool === "read_documentation") {
            toolParamContainer.innerHTML = `<span style="font-size: 0.85rem; color: var(--text-dim);">Scans for README.md and documentation guides in repository</span>`;
        }
    }

    btnExecuteTool.addEventListener("click", async () => {
        const repo = toolRepoInput.value.trim();
        if (!repo) {
            alert("Please provide a repository.");
            return;
        }

        let url = "";
        if (currentSelectedTool === "list_files") {
            const subpath = document.getElementById("param-subpath")?.value.trim() || "";
            url = `/api/tools/list_files?repo=${encodeURIComponent(repo)}&subpath=${encodeURIComponent(subpath)}`;
        } else if (currentSelectedTool === "search_code") {
            const query = document.getElementById("param-query")?.value.trim() || "";
            url = `/api/tools/search_code?repo=${encodeURIComponent(repo)}&query=${encodeURIComponent(query)}`;
        } else if (currentSelectedTool === "read_file") {
            const fp = document.getElementById("param-filepath")?.value.trim() || "";
            const sl = document.getElementById("param-startline")?.value || "1";
            const el = document.getElementById("param-endline")?.value || "60";
            url = `/api/tools/read_file?repo=${encodeURIComponent(repo)}&file_path=${encodeURIComponent(fp)}&start_line=${sl}&end_line=${el}`;
        } else if (currentSelectedTool === "get_dependencies") {
            url = `/api/tools/get_dependencies?repo=${encodeURIComponent(repo)}`;
        } else if (currentSelectedTool === "read_documentation") {
            url = `/api/tools/read_documentation?repo=${encodeURIComponent(repo)}`;
        }

        toolOutputPre.textContent = "Executing tool...";
        const startTime = performance.now();

        try {
            const resp = await fetch(url);
            const data = await resp.json();
            const elapsed = (performance.now() - startTime).toFixed(1);
            toolExecTime.textContent = `Completed in ${elapsed}ms`;
            toolOutputPre.textContent = JSON.stringify(data, null, 2);
        } catch (err) {
            toolOutputPre.textContent = `Error executing tool: ${err.message}`;
        }
    });

    function escapeHtml(str) {
        if (!str) return "";
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // Initialize
    loadRepositories();
    renderToolInputs();
});
