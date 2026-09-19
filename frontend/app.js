/**
 * ClauseLens Front-End Application Logic
 * Modern FAANG UI/UX Design & High-Fidelity SPA
 */

// ─── Global State ──────────────────────────────────────────────────────────
let currentDocId = "";
let currentDocData = null;
let currentProfileData = null;
let currentPerspective = "tenant";
let currentLang = "en";
let currentRewriteLevel = "plain_english";
let activeCategoryFilter = "ALL";
let activeSearchQuery = "";

// ─── DOM References ────────────────────────────────────────────────────────
const docSelector = document.getElementById("docSelector");
const compareDoc1 = document.getElementById("compareDoc1");
const compareDoc2 = document.getElementById("compareDoc2");
const btnSwapCompare = document.getElementById("btnSwapCompare");
const btnRunCompare = document.getElementById("btnRunCompare");
const toastContainer = document.getElementById("toastContainer");

// Clause Inspector Drawer Elements
const clauseDrawerOverlay = document.getElementById("clauseDrawerOverlay");
const clauseDrawer = document.getElementById("clauseDrawer");
const btnCloseDrawer = document.getElementById("btnCloseDrawer");
const drawerCategoryBadge = document.getElementById("drawerCategoryBadge");
const drawerClauseTitle = document.getElementById("drawerClauseTitle");
const drawerClauseNumber = document.getElementById("drawerClauseNumber");
const drawerPageSpan = document.getElementById("drawerPageSpan");
const drawerClauseText = document.getElementById("drawerClauseText");
const btnCopyClauseText = document.getElementById("btnCopyClauseText");
const btnDrawerAskQA = document.getElementById("btnDrawerAskQA");
let activeInspectedClause = null;

// Tree Toolbar Elements
const treeSearchInput = document.getElementById("treeSearchInput");
const treeCategoryFilters = document.getElementById("treeCategoryFilters");

// Tab Navigation
const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanes = document.querySelectorAll(".tab-pane");

tabButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    switchTab(btn.dataset.tab);
  });
});

function switchTab(tabKey) {
  tabButtons.forEach(b => {
    const isActive = b.dataset.tab === tabKey;
    b.classList.toggle("active", isActive);
    b.setAttribute("aria-selected", isActive ? "true" : "false");
  });

  tabPanes.forEach(p => {
    p.classList.toggle("active", p.id === `pane-${tabKey}`);
  });

  if (tabKey === "actionable") {
    loadDeadlines();
  } else if (tabKey === "compare") {
    setupDefaultCompareDocs();
  }
}

// Actionable Sub-Tabs
const actionPills = document.querySelectorAll("#pane-actionable .role-pill");
actionPills.forEach(pill => {
  pill.addEventListener("click", () => {
    actionPills.forEach(p => p.classList.remove("active"));
    pill.classList.add("active");

    const action = pill.dataset.action;
    document.querySelectorAll("[id^='subpane-']").forEach(sp => sp.style.display = "none");
    const targetSubpane = document.getElementById(`subpane-${action}`);
    if (targetSubpane) targetSubpane.style.display = "block";

    if (action === "deadlines") loadDeadlines();
    else if (action === "lawyer-prep") loadLawyerPrep();
    else if (action === "rewriter") loadRewrites();
    else if (action === "negotiate") loadNegotiations();
  });
});

// ─── Toast Notification System ─────────────────────────────────────────────
function showToast(message, type = "info", duration = 3500) {
  if (!toastContainer) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const iconSvg = {
    success: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="var(--status-success)" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>`,
    warning: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="var(--status-warning)" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
    danger: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="var(--status-danger)" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    info: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="var(--status-info)" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`
  }[type] || "";

  toast.innerHTML = `
    ${iconSvg}
    <div style="flex: 1; font-weight: 500;">${message}</div>
    <button style="background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 2px;" aria-label="Close">✕</button>
  `;

  toast.querySelector("button").addEventListener("click", () => removeToast(toast));

  toastContainer.appendChild(toast);

  const timeoutId = setTimeout(() => {
    removeToast(toast);
  }, duration);

  function removeToast(el) {
    clearTimeout(timeoutId);
    el.style.opacity = "0";
    el.style.transform = "translateX(40px)";
    setTimeout(() => {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 250);
  }
}

// ─── Slide-Over Clause Inspector ───────────────────────────────────────────
function openClauseInspector(clause) {
  if (!clause) return;
  activeInspectedClause = clause;

  drawerCategoryBadge.textContent = clause.category || "GENERAL";
  drawerClauseTitle.textContent = clause.title || "Untitled Clause";
  drawerClauseNumber.textContent = clause.clause_number ? `§ ${clause.clause_number}` : "§ -";

  let spansSummary = "Offset: Page 1";
  if (clause.spans && clause.spans.length > 0) {
    const s = clause.spans[0];
    spansSummary = `Pg ${s.page} [${s.bbox ? s.bbox.map(n => Math.round(n)).join(", ") : "0, 0, 0, 0"}]`;
  }
  drawerPageSpan.textContent = spansSummary;
  drawerClauseText.textContent = clause.text || "No text available.";

  clauseDrawerOverlay.classList.add("open");
  clauseDrawer.classList.add("open");
  clauseDrawer.setAttribute("aria-hidden", "false");
}

function closeClauseInspector() {
  clauseDrawerOverlay.classList.remove("open");
  clauseDrawer.classList.remove("open");
  clauseDrawer.setAttribute("aria-hidden", "true");
  activeInspectedClause = null;
}

if (btnCloseDrawer) btnCloseDrawer.addEventListener("click", closeClauseInspector);
if (clauseDrawerOverlay) clauseDrawerOverlay.addEventListener("click", closeClauseInspector);

if (btnCopyClauseText) {
  btnCopyClauseText.addEventListener("click", () => {
    if (!activeInspectedClause) return;
    navigator.clipboard.writeText(activeInspectedClause.text || "").then(() => {
      showToast(`Copied Clause ${activeInspectedClause.clause_number || ''} text to clipboard`, "success");
    }).catch(() => {
      showToast("Unable to copy to clipboard", "warning");
    });
  });
}

if (btnDrawerAskQA) {
  btnDrawerAskQA.addEventListener("click", () => {
    if (!activeInspectedClause) return;
    const clauseNum = activeInspectedClause.clause_number || "";
    const clauseTitle = activeInspectedClause.title || "";
    closeClauseInspector();
    switchTab("qa");
    const qaInput = document.getElementById("qaInput");
    if (qaInput) {
      qaInput.value = `Explain the rights, liabilities, and obligations outlined under Clause ${clauseNum}: ${clauseTitle}.`;
      qaInput.focus();
    }
  });
}

// ─── Initialize Application ────────────────────────────────────────────────
async function initApp() {
  try {
    const res = await fetch("/api/documents");
    const docs = await res.json();

    if (!docs || docs.length === 0) {
      docSelector.innerHTML = `<option value="">No contracts loaded</option>`;
      return;
    }

    docSelector.innerHTML = "";
    compareDoc1.innerHTML = "";
    compareDoc2.innerHTML = "";

    docs.forEach(d => {
      const opt = document.createElement("option");
      opt.value = d.id;
      opt.textContent = `${d.filename} (${d.file_type.toUpperCase()} · ${d.doc_type})`;
      docSelector.appendChild(opt);

      compareDoc1.appendChild(opt.cloneNode(true));
      compareDoc2.appendChild(opt.cloneNode(true));
    });

    currentDocId = docs[0].id;
    docSelector.value = currentDocId;
    await loadDocument(currentDocId);

    setupDefaultCompareDocs();

  } catch (err) {
    console.error("Failed to fetch documents:", err);
    showToast("Error loading document index from server", "danger");
  }
}

// Setup default compare documents
function setupDefaultCompareDocs() {
  const options = Array.from(compareDoc1.options).map(o => o.value);
  if (options.includes("doc_saas_terms") && options.includes("doc_saas_terms_v2")) {
    compareDoc1.value = "doc_saas_terms";
    compareDoc2.value = "doc_saas_terms_v2";
  } else if (options.length >= 2) {
    compareDoc1.value = options[0];
    compareDoc2.value = options[1];
  }
}

// Swap documents in compare view
if (btnSwapCompare) {
  btnSwapCompare.addEventListener("click", () => {
    const temp = compareDoc1.value;
    compareDoc1.value = compareDoc2.value;
    compareDoc2.value = temp;
    showToast("Swapped baseline and revised documents", "info", 1800);
  });
}

// ─── Load Document & Render Views ──────────────────────────────────────────
async function loadDocument(docId) {
  currentDocId = docId;
  try {
    const res = await fetch(`/api/documents/${docId}`);
    currentDocData = await res.json();

    const profRes = await fetch(`/api/documents/${docId}/profile`);
    currentProfileData = await profRes.json();

    renderDocumentSummary(currentDocData, currentProfileData);
    renderFilteredClauseTree();
    renderDefectsAndDefinitions(currentDocData.defects, currentDocData.definitions);
    configurePerspectiveButtons(currentDocData.doc_type);

    await loadRiskProfile(docId, currentPerspective);

  } catch (err) {
    console.error("Error loading document:", err);
    showToast(`Error retrieving document analysis for: ${docId}`, "danger");
  }
}

// Render Document Stats & Template Compliance
function renderDocumentSummary(doc, profile) {
  document.getElementById("statDocType").textContent = profile.doc_type_name || doc.doc_type.toUpperCase();
  document.getElementById("statClauseCount").textContent = doc.clauses.length;
  document.getElementById("statCrossrefCount").textContent = doc.crossrefs.length;
  document.getElementById("statDefectCount").textContent = doc.defects.length;
  document.getElementById("treeClauseTotal").textContent = `${doc.clauses.length} Clauses`;

  const auditContainer = document.getElementById("missingClauseAuditContent");
  const missingBadge = document.getElementById("profileStatusBadge");

  if (profile.missing_clauses && profile.missing_clauses.length > 0) {
    missingBadge.className = "badge badge-warning";
    missingBadge.textContent = `${profile.missing_clauses.length} Missing Standard Clauses`;
    auditContainer.innerHTML = `
      <div style="margin-bottom: 0.6rem;">
        <span style="color: var(--text-muted); font-weight: 600;">Expected Clauses Present:</span> 
        ${profile.present_clauses.map(c => `<span class="node-number" style="margin-right: 5px; font-size: 0.75rem;">${c}</span>`).join(" ")}
      </div>
      <div>
        <span style="color: #FCD34D; font-weight: 600;">Missing Standard Provisions:</span> 
        ${profile.missing_clauses.map(c => `<span class="badge badge-warning" style="margin-right: 5px;">${c}</span>`).join(" ")}
      </div>
    `;
  } else {
    missingBadge.className = "badge badge-success";
    missingBadge.textContent = "100% Template Compliant";
    auditContainer.innerHTML = `
      <p style="color: var(--status-success); display: flex; align-items: center; gap: 0.5rem;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
        <span>All standard legal provisions required for ${profile.doc_type_name || doc.doc_type} are fully represented.</span>
      </p>
    `;
  }
}

// ─── Filtered Clause Tree Rendering ────────────────────────────────────────
function renderFilteredClauseTree() {
  const container = document.getElementById("clauseTreeContainer");
  container.innerHTML = "";

  if (!currentDocData || !currentDocData.clauses || currentDocData.clauses.length === 0) {
    container.innerHTML = `<p style="color: var(--text-muted); padding: 1.5rem; text-align: center;">No clauses detected in this document.</p>`;
    return;
  }

  const query = (activeSearchQuery || "").toLowerCase();
  const catFilter = activeCategoryFilter.toUpperCase();

  const filtered = currentDocData.clauses.filter(clause => {
    // Category match
    const category = (clause.category || "").toUpperCase();
    const matchesCat = catFilter === "ALL" || category === catFilter || category.includes(catFilter);

    // Search query match
    if (!matchesCat) return false;
    if (!query) return true;

    const title = (clause.title || "").toLowerCase();
    const text = (clause.text || "").toLowerCase();
    const num = (clause.clause_number || "").toLowerCase();
    return title.includes(query) || text.includes(query) || num.includes(query);
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-muted);">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 0.5rem;"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <p style="font-weight: 600;">No clauses match your filter criteria.</p>
        <p style="font-size: 0.8rem; margin-top: 0.25rem;">Try a different keyword or category.</p>
      </div>
    `;
    return;
  }

  filtered.forEach(clause => {
    const node = document.createElement("div");
    node.className = "tree-node";
    node.style.marginLeft = `${Math.max(0, (clause.level - 1) * 18)}px`;

    let spansSummary = "Span: Offset [0-0]";
    if (clause.spans && clause.spans.length > 0) {
      const s = clause.spans[0];
      spansSummary = `Pg ${s.page} [${s.bbox ? s.bbox.map(n => Math.round(n)).join(", ") : "0, 0, 0, 0"}]`;
    }

    node.innerHTML = `
      <div class="tree-node-header">
        <div class="node-title-group">
          <span class="node-number">${clause.clause_number || "§"}</span>
          <span class="node-title">${clause.title || "Untitled Clause"}</span>
        </div>
        <div style="display: flex; gap: 0.5rem; align-items: center;">
          <span class="badge badge-info">${clause.category || "GENERAL"}</span>
          <span class="node-spans-pill">${spansSummary}</span>
        </div>
      </div>
      <p class="node-text">${clause.text}</p>
    `;

    // Click opens slide-over clause inspector
    node.addEventListener("click", () => {
      openClauseInspector(clause);
    });

    container.appendChild(node);
  });
}

// Tree Search & Filter Listeners
if (treeSearchInput) {
  treeSearchInput.addEventListener("input", (e) => {
    activeSearchQuery = e.target.value.trim();
    renderFilteredClauseTree();
  });
}

if (treeCategoryFilters) {
  treeCategoryFilters.querySelectorAll(".filter-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      treeCategoryFilters.querySelectorAll(".filter-chip").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeCategoryFilter = btn.dataset.category || "ALL";
      renderFilteredClauseTree();
    });
  });
}

// ─── Render Defects and Defined Terms ──────────────────────────────────────
function renderDefectsAndDefinitions(defects, definitions) {
  // Defects
  const defectsContainer = document.getElementById("defectsList");
  document.getElementById("defectCountBadge").textContent = `${defects.length} Caught`;
  defectsContainer.innerHTML = "";

  if (!defects || defects.length === 0) {
    defectsContainer.innerHTML = `<p style="color: var(--status-success); font-size: 0.85rem; padding: 0.5rem;">No drafting flaws or dangling references detected.</p>`;
  } else {
    defects.forEach(d => {
      const isDangling = d.defect_type === "dangling_crossref";
      const isConflicting = d.defect_type === "conflicting_notice";
      const badgeClass = isDangling ? "badge-danger" : (isConflicting ? "badge-warning" : "badge-info");

      const item = document.createElement("div");
      item.style.padding = "0.85rem";
      item.style.background = isDangling ? "rgba(244, 63, 94, 0.08)" : "rgba(255, 255, 255, 0.03)";
      item.style.borderRadius = "var(--radius-sm)";
      item.style.border = `1px solid ${isDangling ? "rgba(244, 63, 94, 0.35)" : "var(--border-subtle)"}`;
      item.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
          <span class="badge ${badgeClass}">${d.defect_type.replace(/_/g, ' ')}</span>
          <span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 700;">${d.severity.toUpperCase()}</span>
        </div>
        <p style="font-size: 0.84rem; color: var(--text-secondary); line-height: 1.5;">${d.description}</p>
      `;
      defectsContainer.appendChild(item);
    });
  }

  // Definitions
  const defsContainer = document.getElementById("definitionsList");
  document.getElementById("definitionCountBadge").textContent = `${definitions.length} Terms`;
  defsContainer.innerHTML = "";

  if (!definitions || definitions.length === 0) {
    defsContainer.innerHTML = `<p style="color: var(--text-muted); font-size: 0.85rem; padding: 0.5rem;">No explicit defined terms declared.</p>`;
  } else {
    definitions.forEach(def => {
      const item = document.createElement("div");
      item.style.padding = "0.75rem 0.9rem";
      item.style.background = "rgba(255, 255, 255, 0.03)";
      item.style.borderRadius = "var(--radius-sm)";
      item.style.border = "1px solid var(--border-subtle)";
      item.innerHTML = `
        <div style="font-weight: 700; font-size: 0.86rem; color: #38BDF8; margin-bottom: 2px;">"${def.term}"</div>
        <div style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.5;">${def.definition}</div>
      `;
      defsContainer.appendChild(item);
    });
  }
}

// ─── Configure Perspective Buttons ─────────────────────────────────────────
function configurePerspectiveButtons(docType) {
  const container = document.getElementById("perspectiveButtons");
  container.innerHTML = "";

  let roles = [
    { key: "tenant", label: "Tenant" },
    { key: "landlord", label: "Landlord" }
  ];

  if (docType === "employment") {
    roles = [
      { key: "employee", label: "Employee" },
      { key: "employer", label: "Employer" }
    ];
  } else if (docType === "saas_terms" || docType === "service_agreement") {
    roles = [
      { key: "customer", label: "Customer" },
      { key: "vendor", label: "Vendor" }
    ];
  }

  currentPerspective = roles[0].key;

  roles.forEach((r, idx) => {
    const btn = document.createElement("button");
    btn.className = `role-pill ${idx === 0 ? "active" : ""}`;
    btn.textContent = r.label;
    btn.dataset.role = r.key;
    btn.addEventListener("click", () => {
      container.querySelectorAll(".role-pill").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      currentPerspective = r.key;
      loadRiskProfile(currentDocId, currentPerspective);
    });
    container.appendChild(btn);
  });
}

// ─── Load Perspective Risk Assessment with Animated SVG Gauge ──────────────
async function loadRiskProfile(docId, perspective) {
  try {
    const res = await fetch(`/api/documents/${docId}/risk?perspective=${perspective}`);
    const risk = await res.json();

    const gaugeProgress = document.getElementById("riskGaugeProgress");
    const scoreVal = document.getElementById("riskScoreValue");
    const tierTitle = document.getElementById("riskTierTitle");
    const summaryDesc = document.getElementById("riskSummaryDesc");
    const itemsContainer = document.getElementById("riskItemsList");
    const badge = document.getElementById("riskItemsCountBadge");

    const score = Math.round(risk.overall_risk_score || 0);
    badge.textContent = `${risk.risk_items.length} Assessed`;

    // Animate score counter
    animateCounter(scoreVal, score, 800);

    // SVG Circular Progress animation (Circumference: 2 * PI * 60 = 376.99)
    const circumference = 377;
    const strokeOffset = circumference - (score / 100) * circumference;
    if (gaugeProgress) {
      gaugeProgress.style.strokeDashoffset = strokeOffset;
    }

    if (score > 70) {
      if (gaugeProgress) gaugeProgress.style.stroke = "var(--status-danger)";
      tierTitle.textContent = `High Risk Exposure for ${perspective.toUpperCase()}`;
      tierTitle.style.color = "var(--status-danger)";
      summaryDesc.textContent = `Multiple aggressive provisions, liability exposure, or structural flaws detected disproportionately affecting the ${perspective}.`;
    } else if (score > 40) {
      if (gaugeProgress) gaugeProgress.style.stroke = "var(--status-warning)";
      tierTitle.textContent = `Moderate Risk Exposure for ${perspective.toUpperCase()}`;
      tierTitle.style.color = "var(--status-warning)";
      summaryDesc.textContent = `Standard baseline provisions present with some non-standard clauses to scrutinize.`;
    } else {
      if (gaugeProgress) gaugeProgress.style.stroke = "var(--status-success)";
      tierTitle.textContent = `Low Risk Exposure for ${perspective.toUpperCase()}`;
      tierTitle.style.color = "var(--status-success)";
      summaryDesc.textContent = `Provisions align solidly with bilateral market conventions and balanced covenants.`;
    }

    // Render Risk Items
    itemsContainer.innerHTML = "";
    if (risk.risk_items.length === 0) {
      itemsContainer.innerHTML = `<p style="color: var(--text-muted); padding: 1.5rem; text-align: center;">No notable risk deviations found for this perspective.</p>`;
      return;
    }

    risk.risk_items.forEach(item => {
      const card = document.createElement("div");
      card.className = `risk-item-card ${item.perspective_risk.toLowerCase()}`;

      let badgeClass = "badge-info";
      if (item.perspective_risk === "critical") badgeClass = "badge-danger";
      else if (item.perspective_risk === "high") badgeClass = "badge-warning";
      else if (item.perspective_risk === "low") badgeClass = "badge-success";

      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; flex-wrap: wrap; gap: 0.5rem;">
          <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span class="node-number">Clause ${item.clause_number}</span>
            <span style="font-weight: 700; font-size: 0.98rem; color: var(--text-primary);">${item.category.toUpperCase()}</span>
          </div>
          <div style="display: flex; gap: 0.5rem;">
            <span class="badge ${badgeClass}">Risk: ${item.perspective_risk.toUpperCase()}</span>
            <span class="badge badge-info">Deviation: ${item.deviation_rating.toUpperCase()}</span>
          </div>
        </div>
        <p style="font-size: 0.88rem; color: var(--text-secondary); margin-bottom: 0.75rem; line-height: 1.6;">${item.rationale}</p>
        <div style="font-size: 0.82rem; background: rgba(0,0,0,0.35); padding: 0.7rem 0.9rem; border-radius: var(--radius-sm); border-left: 3px solid var(--accent-primary); color: #E2E8F0;">
          <strong style="color: #A5B4FC;">Driving Text Span:</strong> "${item.driving_span}"
        </div>
      `;
      itemsContainer.appendChild(card);
    });

  } catch (err) {
    console.error("Failed to load risk profile:", err);
    showToast("Failed to calculate perspective risk profile", "danger");
  }
}

function animateCounter(element, target, duration) {
  let start = 0;
  const startTime = performance.now();

  function update(time) {
    const elapsed = time - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const val = Math.round(start + (target - start) * easeOutQuad(progress));
    element.textContent = val;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

function easeOutQuad(x) {
  return 1 - (1 - x) * (1 - x);
}

// ─── Grounded QA Interaction ───────────────────────────────────────────────
const qaForm = document.getElementById("qaForm");
const qaInput = document.getElementById("qaInput");
const qaMessages = document.getElementById("qaMessages");

qaForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = qaInput.value.trim();
  if (!query) return;
  await submitQuestion(query);
});

// Click suggested prompt chips
document.querySelectorAll(".query-chip").forEach(chip => {
  chip.addEventListener("click", async () => {
    const q = chip.dataset.q;
    qaInput.value = q;
    await submitQuestion(q);
  });
});

async function submitQuestion(question) {
  // Append User Message
  appendMessage("user", `<p>${escapeHtml(question)}</p>`);
  qaInput.value = "";

  // Append Thinking Bubble with animated bouncing dots
  const thinkingId = "msg-thinking-" + Date.now();
  const thinkingNode = document.createElement("div");
  thinkingNode.id = thinkingId;
  thinkingNode.className = "message-card agent";
  thinkingNode.innerHTML = `
    <div class="typing-dots">
      <span></span><span></span><span></span>
    </div>
    <span style="font-size: 0.85rem; color: var(--text-muted); margin-left: 6px;">Retrieving grounded citations & analyzing hierarchy...</span>
  `;
  qaMessages.appendChild(thinkingNode);
  qaMessages.scrollTop = qaMessages.scrollHeight;

  try {
    const res = await fetch(`/api/documents/${currentDocId}/qa`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question })
    });
    const qaResult = await res.json();
    thinkingNode.remove();

    let contentHtml = `
      <div class="agent-meta-header">
        <span>ClauseLens Grounded Engine</span>
        <button class="btn-copy-answer" title="Copy answer">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          <span>Copy</span>
        </button>
      </div>
      <p style="white-space: pre-wrap;">${qaResult.answer}</p>
    `;

    // Refusal Guardrail Alert
    if (qaResult.is_refusal) {
      contentHtml += `
        <div class="refusal-alert">
          <strong>⚠️ Informational Guardrail:</strong> This query solicited legal advice or court case prediction. ClauseLens operates strictly as an objective analytical engine and never provides formal legal advice.
        </div>
      `;
    }

    // Grounded Citations
    if (qaResult.cited_clauses && qaResult.cited_clauses.length > 0) {
      contentHtml += `<div class="citation-box"><span style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Grounded Clause Citations:</span>`;
      qaResult.cited_clauses.forEach(c => {
        let spanCoords = "Coordinates: [0, 0, 0, 0]";
        if (c.spans && c.spans.length > 0) {
          spanCoords = `Pg ${c.spans[0].page} [${c.spans[0].bbox ? c.spans[0].bbox.map(Math.round).join(", ") : ""}]`;
        }
        contentHtml += `
          <div class="citation-pill" data-clause-num="${c.clause_number}">
            <span>📍 Clause ${c.clause_number}: ${c.title}</span>
            <span style="color: var(--text-muted); font-size: 0.7rem;">(${spanCoords})</span>
          </div>
        `;
      });
      contentHtml += `</div>`;
    }

    const msgEl = appendMessage("agent", contentHtml);

    // Setup Copy button listener
    const copyBtn = msgEl.querySelector(".btn-copy-answer");
    if (copyBtn) {
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(qaResult.answer).then(() => {
          showToast("Answer copied to clipboard", "success");
        });
      });
    }

    // Setup citation pill clicks to open Clause Inspector
    msgEl.querySelectorAll(".citation-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        const num = pill.dataset.clauseNum;
        if (currentDocData && currentDocData.clauses) {
          const matched = currentDocData.clauses.find(cl => cl.clause_number == num);
          if (matched) openClauseInspector(matched);
        }
      });
    });

  } catch (err) {
    thinkingNode.remove();
    appendMessage("agent", `<span style="color: var(--status-danger);">Error querying document QA endpoint. Please check your connection.</span>`);
    showToast("QA query failed", "danger");
  }
}

function appendMessage(role, html) {
  const div = document.createElement("div");
  div.className = `message-card ${role}`;
  div.innerHTML = html;
  qaMessages.appendChild(div);
  qaMessages.scrollTop = qaMessages.scrollHeight;
  return div;
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ─── Compare Documents Handler ─────────────────────────────────────────────
btnRunCompare.addEventListener("click", async () => {
  const doc1 = compareDoc1.value;
  const doc2 = compareDoc2.value;

  if (!doc1 || !doc2) {
    showToast("Please select two documents to compare.", "warning");
    return;
  }

  if (doc1 === doc2) {
    showToast("Please select two different documents to compare.", "warning");
    return;
  }

  const container = document.getElementById("diffResultsContainer");
  container.innerHTML = `
    <div style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
      <div class="typing-dots" style="margin-bottom: 0.5rem;"><span></span><span></span><span></span></div>
      <p>Aligning clauses and calculating semantic shift...</p>
    </div>
  `;

  try {
    const res = await fetch("/api/documents/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ doc_id_a: doc1, doc_id_b: doc2 })
    });
    const diff = await res.json();

    const addedList = diff.added || [];
    const removedList = diff.removed || [];
    const modifiedList = diff.materially_changed || [];

    document.getElementById("statDiffAdded").textContent = addedList.length;
    document.getElementById("statDiffRemoved").textContent = removedList.length;
    document.getElementById("statDiffModified").textContent = modifiedList.length;

    let html = "";

    // 1. Materially Modified Clauses
    if (modifiedList.length > 0) {
      html += `<div class="diff-bucket modified"><h3 style="color: #FBBF24; margin-bottom: 1rem; font-size: 1.05rem;">Δ Materially Changed Provisions (${modifiedList.length})</h3>`;
      modifiedList.forEach(m => {
        html += `
          <div class="diff-box-inner">
            <div style="display: flex; justify-content: space-between; align-items: center; font-weight: 700; margin-bottom: 0.6rem;">
              <span>Clause ${m.clause_number_a || "§"} ➔ ${m.clause_number_b || "§"} (${m.title_b || m.title_a})</span>
              <span class="badge badge-warning">Similarity: ${(m.similarity_score * 100).toFixed(0)}%</span>
            </div>
            <div style="padding: 0.6rem 0.85rem; background: rgba(245, 158, 11, 0.12); border-left: 3px solid #F59E0B; margin-bottom: 0.75rem; font-size: 0.86rem; color: #FDE68A; border-radius: 4px;">
              <strong>Semantic Shift:</strong> ${m.semantic_change_summary || "Material wording or timeline modification."}
            </div>
            <div class="layout-split" style="font-size: 0.84rem;">
              <div style="color: #F87171; background: rgba(244, 63, 94, 0.05); padding: 0.75rem; border-radius: 6px;">
                <strong>v1 Original:</strong> "${m.text_a}"
              </div>
              <div style="color: #34D399; background: rgba(16, 185, 129, 0.05); padding: 0.75rem; border-radius: 6px;">
                <strong>v2 Revision:</strong> "${m.text_b}"
              </div>
            </div>
          </div>
        `;
      });
      html += `</div>`;
    }

    // 2. Added Clauses
    if (addedList.length > 0) {
      html += `<div class="diff-bucket added"><h3 style="color: var(--status-success); margin-bottom: 1rem; font-size: 1.05rem;">+ Added Provisions (Present in v2 only) (${addedList.length})</h3>`;
      addedList.forEach(c => {
        html += `
          <div class="diff-box-inner">
            <div style="font-weight: 700; font-size: 0.92rem; color: #34D399;">Clause ${c.clause_number_b}: ${c.title_b}</div>
            <p style="font-size: 0.84rem; color: var(--text-secondary); margin-top: 0.35rem; line-height: 1.5;">${c.text_b}</p>
          </div>
        `;
      });
      html += `</div>`;
    }

    // 3. Removed Clauses
    if (removedList.length > 0) {
      html += `<div class="diff-bucket removed"><h3 style="color: var(--status-danger); margin-bottom: 1rem; font-size: 1.05rem;">- Removed Provisions (Omitted in v2) (${removedList.length})</h3>`;
      removedList.forEach(c => {
        html += `
          <div class="diff-box-inner">
            <div style="font-weight: 700; font-size: 0.92rem; color: #F87171;">Clause ${c.clause_number_a}: ${c.title_a}</div>
            <p style="font-size: 0.84rem; color: var(--text-secondary); margin-top: 0.35rem; line-height: 1.5;">${c.text_a}</p>
          </div>
        `;
      });
      html += `</div>`;
    }

    container.innerHTML = html || `<p style="color: var(--status-success); text-align: center; padding: 2.5rem;">Both documents are structurally and semantically identical.</p>`;
    showToast("Semantic comparison complete", "success");

  } catch (err) {
    container.innerHTML = `<p style="color: var(--status-danger); text-align: center; padding: 2rem;">Failed to execute semantic comparison.</p>`;
    showToast("Semantic comparison failed", "danger");
  }
});

// ─── Actionable 1: Deadlines ───────────────────────────────────────────────
async function loadDeadlines() {
  const baseDate = document.getElementById("effectiveDateInput").value || "2026-10-01";
  const container = document.getElementById("deadlinesTimeline");
  container.innerHTML = `<p style="color: var(--text-muted); padding: 1.5rem;">Extracting obligations timeline...</p>`;

  try {
    const res = await fetch(`/api/documents/${currentDocId}/actionable/deadlines?effective_date=${baseDate}`);
    const data = await res.json();

    container.innerHTML = "";
    if (!data.deadlines || data.deadlines.length === 0) {
      container.innerHTML = `<p style="color: var(--text-muted); padding: 1.5rem;">No time-bound deadlines detected in this document.</p>`;
      return;
    }

    data.deadlines.forEach(dl => {
      const item = document.createElement("div");
      item.className = "timeline-item";
      item.innerHTML = `
        <div class="timeline-dot"></div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
          <span style="font-family: var(--font-mono); font-weight: 700; color: var(--accent-primary); font-size: 0.95rem;">${dl.resolved_date || 'Relative Date'}</span>
          <span class="badge badge-info">${(dl.party || 'PARTY').toUpperCase()}</span>
        </div>
        <h4 style="font-size: 0.95rem; margin-bottom: 0.3rem; color: var(--text-primary);">Clause ${dl.clause_number}: ${dl.obligation}</h4>
        <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.45rem;">
          <strong>Trigger:</strong> ${dl.trigger} (${dl.relative_days} days offset)
        </div>
      `;
      container.appendChild(item);
    });

  } catch (err) {
    container.innerHTML = `<p style="color: var(--status-danger); padding: 1rem;">Failed to load deadlines.</p>`;
  }
}

// Export .ics Calendar
document.getElementById("btnExportIcs").addEventListener("click", () => {
  const baseDate = document.getElementById("effectiveDateInput").value || "2026-10-01";
  window.open(`/api/documents/${currentDocId}/actionable/deadlines/ics?effective_date=${baseDate}`, "_blank");
  showToast("Downloading .ics calendar schedule", "info");
});

// ─── Actionable 2: Lawyer-Prep ─────────────────────────────────────────────
async function loadLawyerPrep() {
  const container = document.getElementById("lawyerPrepContent");
  container.innerHTML = `<p style="color: var(--text-muted); padding: 1.5rem;">Compiling Lawyer Consultation Brief...</p>`;

  try {
    const res = await fetch(`/api/documents/${currentDocId}/actionable/lawyer-prep`);
    const pack = await res.json();

    let factsHtml = "";
    if (typeof pack.fact_summary === "object" && pack.fact_summary !== null) {
      factsHtml = Object.entries(pack.fact_summary)
        .map(([k, v]) => `<div><strong style="color: #A5B4FC;">${k.replace(/_/g, ' ').toUpperCase()}:</strong> ${typeof v === 'object' ? JSON.stringify(v) : v}</div>`)
        .join('');
    } else {
      factsHtml = `<p>${pack.fact_summary}</p>`;
    }

    const checklist = pack.checklist || [];
    const questions = pack.prioritized_questions || [];

    let html = `
      <div style="background: rgba(0,0,0,0.3); padding: 1.25rem; border-radius: var(--radius-md); margin-bottom: 1.35rem; border: 1px solid var(--border-subtle);">
        <h3 style="font-size: 1.05rem; margin-bottom: 0.6rem; color: var(--accent-primary);">1. Executive Document Summary</h3>
        <div style="font-size: 0.9rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 0.4rem;">
          ${factsHtml}
        </div>
      </div>

      <div style="margin-bottom: 1.35rem;">
        <h3 style="font-size: 1.05rem; margin-bottom: 0.6rem; color: #F59E0B;">2. Document Integrity Audit Checklist</h3>
        <div style="display: flex; flex-direction: column; gap: 0.55rem;">
          ${checklist.map(item => `
            <div style="display: flex; align-items: center; gap: 0.75rem; font-size: 0.88rem; padding: 0.6rem 0.9rem; background: rgba(255,255,255,0.02); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
              <span>${item.status === 'pass' || item.passed ? "✅" : "⚠️"}</span>
              <span style="font-weight: 600; min-width: 170px; color: var(--text-primary);">${item.name || item.item || "Check"}:</span>
              <span style="color: var(--text-secondary);">${item.notes || item.status || ""}</span>
            </div>
          `).join("")}
        </div>
      </div>

      <div>
        <h3 style="font-size: 1.05rem; margin-bottom: 0.6rem; color: var(--status-danger);">3. Prioritized Questions for Counsel</h3>
        <div style="display: flex; flex-direction: column; gap: 0.85rem;">
          ${questions.map((q, idx) => `
            <div style="background: rgba(244, 63, 94, 0.05); border: 1px solid rgba(244, 63, 94, 0.25); border-radius: var(--radius-md); padding: 1rem;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                <span class="badge ${q.priority === 'critical' ? 'badge-danger' : 'badge-warning'}">Priority: ${(q.priority || 'MEDIUM').toUpperCase()}</span>
                <span class="node-number">Target: Clause ${q.clause_number || q.clause_id}</span>
              </div>
              <p style="font-size: 0.92rem; font-weight: 600; color: #FFFFFF; margin-bottom: 0.3rem;">"${q.question}"</p>
              <p style="font-size: 0.82rem; color: var(--text-secondary);">Context: ${q.context_reason || q.rationale || ""}</p>
            </div>
          `).join("")}
        </div>
      </div>
    `;

    container.innerHTML = html;

  } catch (err) {
    container.innerHTML = `<p style="color: var(--status-danger); padding: 1rem;">Failed to compile lawyer consultation pack.</p>`;
  }
}

// ─── Actionable 3: Plain-Language Rewrites & Translations ──────────────────
document.querySelectorAll("#subpane-rewriter .btn-secondary[data-lang]").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#subpane-rewriter .btn-secondary[data-lang]").forEach(b => b.classList.remove("active-lang"));
    btn.classList.add("active-lang");
    currentLang = btn.dataset.lang;
    loadRewrites();
  });
});

document.querySelectorAll("input[name='rwLevel']").forEach(radio => {
  radio.addEventListener("change", (e) => {
    currentRewriteLevel = e.target.value;
    loadRewrites();
  });
});

async function loadRewrites() {
  const container = document.getElementById("rewriterCardsContainer");
  container.innerHTML = `<p style="color: var(--text-muted); padding: 1.5rem;">Generating plain-language translations (${currentLang.toUpperCase()})...</p>`;

  try {
    const res = await fetch(`/api/documents/${currentDocId}/actionable/rewrite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level: currentRewriteLevel, language: currentLang })
    });
    const data = await res.json();

    container.innerHTML = "";
    const simplified = data.clauses_simplified || data.simplified_clauses || [];
    simplified.forEach(sc => {
      const card = document.createElement("div");
      card.style.background = "rgba(14, 21, 38, 0.7)";
      card.style.border = "1px solid var(--border-subtle)";
      card.style.borderRadius = "var(--radius-md)";
      card.style.padding = "1.2rem";
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
          <span class="node-number">Clause ${sc.clause_number}: ${sc.title || ''}</span>
          <span class="badge badge-info">${data.language.toUpperCase()} · ${data.level ? data.level.toUpperCase() : ''}</span>
        </div>
        <p style="font-size: 0.94rem; color: #F8FAFC; margin-bottom: 0.75rem; line-height: 1.65;">${sc.simplified_text}</p>
        <details style="font-size: 0.8rem; color: var(--text-muted); cursor: pointer;">
          <summary style="font-weight: 600;">View Original Legalese</summary>
          <p style="margin-top: 0.4rem; padding: 0.6rem; background: rgba(0,0,0,0.3); border-radius: var(--radius-xs); color: var(--text-secondary); line-height: 1.5;">${sc.original_text}</p>
        </details>
      `;
      container.appendChild(card);
    });

  } catch (err) {
    container.innerHTML = `<p style="color: var(--status-danger); padding: 1rem;">Failed to load rewrites.</p>`;
  }
}

// ─── Actionable 4: Negotiations ────────────────────────────────────────────
async function loadNegotiations() {
  const container = document.getElementById("negotiationCardsContainer");
  container.innerHTML = `<p style="color: var(--text-muted); padding: 1.5rem;">Generating balanced negotiation counter-proposals...</p>`;

  try {
    const res = await fetch(`/api/documents/${currentDocId}/actionable/negotiations`);
    const proposals = await res.json();

    container.innerHTML = "";
    if (proposals.length === 0) {
      container.innerHTML = `<p style="color: var(--status-success); padding: 1.5rem; text-align: center;">No aggressive or one-sided terms found requiring counter-proposals.</p>`;
      return;
    }

    proposals.forEach(p => {
      const card = document.createElement("div");
      card.style.background = "rgba(245, 158, 11, 0.05)";
      card.style.border = "1px solid rgba(245, 158, 11, 0.25)";
      card.style.borderRadius = "var(--radius-md)";
      card.style.padding = "1.25rem";
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
          <span class="node-number">Clause ${p.clause_number} (${p.category.toUpperCase()})</span>
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <span class="badge badge-warning">Counter-Proposal</span>
            <button class="btn-copy-proposal btn-secondary" style="padding: 2px 7px; font-size: 0.74rem;">Copy</button>
          </div>
        </div>
        <div style="font-size: 0.86rem; color: #F87171; margin-bottom: 0.75rem; line-height: 1.5;">
          <strong>Original Aggressive Provision:</strong> "${p.original_text}"
        </div>
        <div style="font-size: 0.92rem; color: #34D399; background: rgba(16, 185, 129, 0.1); padding: 0.85rem; border-radius: var(--radius-sm); border-left: 3px solid #10B981; margin-bottom: 0.6rem; line-height: 1.6;">
          <strong>Proposed Balanced Alternative:</strong> "${p.proposed_alternative_text || p.proposed_alternative}"
        </div>
        <div style="font-size: 0.82rem; color: var(--text-secondary);">
          <strong>One-Line Rationale:</strong> ${p.one_line_rationale || p.rationale}
        </div>
      `;

      card.querySelector(".btn-copy-proposal").addEventListener("click", () => {
        const text = p.proposed_alternative_text || p.proposed_alternative;
        navigator.clipboard.writeText(text).then(() => {
          showToast("Copied negotiation proposal to clipboard", "success");
        });
      });

      container.appendChild(card);
    });

  } catch (err) {
    container.innerHTML = `<p style="color: var(--status-danger); padding: 1rem;">Failed to load negotiation proposals.</p>`;
  }
}

// ─── Switch Document Listener ──────────────────────────────────────────────
docSelector.addEventListener("change", (e) => {
  const selected = e.target.value;
  if (selected) {
    loadDocument(selected);
    showToast(`Switched active document to ${docSelector.options[docSelector.selectedIndex].text}`, "info");
  }
});

// ─── Upload Modal Logic ────────────────────────────────────────────────────
const uploadModal = document.getElementById("uploadModal");
const btnOpenUpload = document.getElementById("btnOpenUpload");
const btnCloseUpload = document.getElementById("btnCloseUpload");
const btnChooseFile = document.getElementById("btnChooseFile");
const fileInput = document.getElementById("fileInput");
const dropzone = document.getElementById("dropzone");
const uploadStatus = document.getElementById("uploadStatus");

btnOpenUpload.addEventListener("click", () => {
  uploadModal.classList.add("open");
  uploadModal.setAttribute("aria-hidden", "false");
  uploadStatus.textContent = "";
});

btnCloseUpload.addEventListener("click", () => {
  uploadModal.classList.remove("open");
  uploadModal.setAttribute("aria-hidden", "true");
});

btnChooseFile.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length > 0) uploadFile(e.target.files[0]);
});

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files.length > 0) uploadFile(e.dataTransfer.files[0]);
});

async function uploadFile(file) {
  uploadStatus.innerHTML = `<em>Uploading and analyzing "${file.name}"...</em>`;
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/documents/upload", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      uploadStatus.innerHTML = `<span style="color: var(--status-danger);">Upload failed: ${err.detail || 'Error'}</span>`;
      showToast(`Upload failed: ${err.detail || 'Error'}`, "danger");
      return;
    }

    const data = await res.json();
    uploadStatus.innerHTML = `<span style="color: var(--status-success);">Success! Ingested ${data.document.clauses.length} clauses.</span>`;
    showToast(`Successfully analyzed "${file.name}"`, "success");

    setTimeout(async () => {
      uploadModal.classList.remove("open");
      uploadModal.setAttribute("aria-hidden", "true");
      await initApp();
      docSelector.value = data.document.id;
      loadDocument(data.document.id);
    }, 800);

  } catch (err) {
    uploadStatus.innerHTML = `<span style="color: var(--status-danger);">Network or server error during upload.</span>`;
    showToast("Upload network error", "danger");
  }
}

// ─── Global Keyboard Shortcuts ─────────────────────────────────────────────
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeClauseInspector();
    uploadModal.classList.remove("open");
    uploadModal.setAttribute("aria-hidden", "true");
  }
});

// Run init on DOM ready
document.addEventListener("DOMContentLoaded", initApp);
