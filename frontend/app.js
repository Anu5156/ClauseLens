/**
 * ClauseLens Front-End Application Logic
 * Single Page Application interacting with FastAPI REST endpoints.
 */

// Global State
let currentDocId = "";
let currentDocData = null;
let currentPerspective = "tenant";
let currentLang = "en";
let currentRewriteLevel = "plain_english";

// DOM Elements
const docSelector = document.getElementById("docSelector");
const compareDoc1 = document.getElementById("compareDoc1");
const compareDoc2 = document.getElementById("compareDoc2");
const btnRunCompare = document.getElementById("btnRunCompare");

// Tab Navigation
const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanes = document.querySelectorAll(".tab-pane");

tabButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    tabButtons.forEach(b => {
      b.classList.remove("active");
      b.setAttribute("aria-selected", "false");
    });
    tabPanes.forEach(p => p.classList.remove("active"));

    btn.classList.add("active");
    btn.setAttribute("aria-selected", "true");
    const target = document.getElementById(`pane-${btn.dataset.tab}`);
    if (target) target.classList.add("active");

    if (btn.dataset.tab === "actionable") {
      loadDeadlines();
    } else if (btn.dataset.tab === "compare") {
      setupDefaultCompareDocs();
    }
  });
});

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

// Initialize Application
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

    docs.forEach((d, idx) => {
      const opt = document.createElement("option");
      opt.value = d.id;
      opt.textContent = `${d.filename} (${d.file_type.toUpperCase()} · ${d.doc_type})`;
      docSelector.appendChild(opt);

      // Clone for compare selectors
      compareDoc1.appendChild(opt.cloneNode(true));
      compareDoc2.appendChild(opt.cloneNode(true));
    });

    // Default select first doc
    currentDocId = docs[0].id;
    docSelector.value = currentDocId;
    await loadDocument(currentDocId);

    // Setup compare defaults
    setupDefaultCompareDocs();

  } catch (err) {
    console.error("Failed to fetch documents:", err);
  }
}

// Setup default compare documents (saas_terms vs saas_terms_v2 if available)
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

// Load Document Data & Render Views
async function loadDocument(docId) {
  currentDocId = docId;
  try {
    // 1. Fetch Document Parsed Tree & Metadata
    const res = await fetch(`/api/documents/${docId}`);
    currentDocData = await res.json();

    // 2. Fetch Document Profile (Template Compliance)
    const profRes = await fetch(`/api/documents/${docId}/profile`);
    const profile = await profRes.json();

    renderDocumentSummary(currentDocData, profile);
    renderClauseTree(currentDocData.clauses);
    renderDefectsAndDefinitions(currentDocData.defects, currentDocData.definitions);
    configurePerspectiveButtons(currentDocData.doc_type);

    // 3. Load Perspective Risk with default perspective
    await loadRiskProfile(docId, currentPerspective);

  } catch (err) {
    console.error("Error loading document:", err);
  }
}

// Render Document Stats & Template Compliance
function renderDocumentSummary(doc, profile) {
  document.getElementById("statDocType").textContent = profile.doc_type_name || doc.doc_type.toUpperCase();
  document.getElementById("statClauseCount").textContent = doc.clauses.length;
  document.getElementById("statCrossrefCount").textContent = doc.crossrefs.length;
  document.getElementById("statDefectCount").textContent = doc.defects.length;
  document.getElementById("treeClauseTotal").textContent = `${doc.clauses.length} Clauses`;

  // Audit Compliance Box
  const auditContainer = document.getElementById("missingClauseAuditContent");
  const missingBadge = document.getElementById("profileStatusBadge");

  if (profile.missing_clauses && profile.missing_clauses.length > 0) {
    missingBadge.className = "badge badge-warning";
    missingBadge.textContent = `${profile.missing_clauses.length} Missing Standard Clauses`;
    auditContainer.innerHTML = `
      <p style="margin-bottom: 0.5rem;"><strong>Expected Clauses Present:</strong> ${profile.present_clauses.map(c => `<span class="node-number" style="margin-right:4px;">${c}</span>`).join(" ")}</p>
      <p style="color: #FCD34D;"><strong>Missing Standard Provisions Detected:</strong> ${profile.missing_clauses.map(c => `<span class="badge badge-warning" style="margin-right:4px;">${c}</span>`).join(" ")}</p>
    `;
  } else {
    missingBadge.className = "badge badge-success";
    missingBadge.textContent = "100% Template Compliant";
    auditContainer.innerHTML = `
      <p style="color: var(--status-success);">All standard clauses required for ${profile.doc_type_name} are present.</p>
    `;
  }
}

// Render Hierarchical Clause Tree
function renderClauseTree(clauses) {
  const container = document.getElementById("clauseTreeContainer");
  container.innerHTML = "";

  if (!clauses || clauses.length === 0) {
    container.innerHTML = `<p style="color: var(--text-muted);">No clauses detected.</p>`;
    return;
  }

  clauses.forEach(clause => {
    const node = document.createElement("div");
    node.className = "tree-node";
    node.style.marginLeft = `${Math.max(0, (clause.level - 1) * 20)}px`;

    let spansSummary = "Span: Offset [0-0]";
    if (clause.spans && clause.spans.length > 0) {
      const s = clause.spans[0];
      spansSummary = `Pg ${s.page} [${s.bbox.map(n => Math.round(n)).join(", ")}]`;
    }

    node.innerHTML = `
      <div class="tree-node-header">
        <div class="node-title-group">
          <span class="node-number">${clause.clause_number || "§"}</span>
          <span class="node-title">${clause.title}</span>
        </div>
        <div style="display: flex; gap: 0.4rem; align-items: center;">
          <span class="badge badge-info">${clause.category}</span>
          <span class="node-spans-pill">${spansSummary}</span>
        </div>
      </div>
      <p class="node-text">${clause.text}</p>
    `;

    // Click to view full text modal/alert
    node.addEventListener("click", () => {
      alert(`[Clause ${clause.clause_number}: ${clause.title}]\nCategory: ${clause.category}\nSpans: ${spansSummary}\n\nFull Text:\n${clause.text}`);
    });

    container.appendChild(node);
  });
}

// Render Defects and Defined Terms
function renderDefectsAndDefinitions(defects, definitions) {
  // Defects
  const defectsContainer = document.getElementById("defectsList");
  document.getElementById("defectCountBadge").textContent = `${defects.length} Caught`;
  defectsContainer.innerHTML = "";

  if (!defects || defects.length === 0) {
    defectsContainer.innerHTML = `<p style="color: var(--status-success); font-size: 0.85rem;">No drafting flaws or dangling references detected.</p>`;
  } else {
    defects.forEach(d => {
      const isDangling = d.defect_type === "dangling_crossref";
      const isConflicting = d.defect_type === "conflicting_notice";
      const badgeClass = isDangling ? "badge-danger" : (isConflicting ? "badge-warning" : "badge-info");

      const item = document.createElement("div");
      item.style.padding = "0.75rem";
      item.style.background = isDangling ? "rgba(244, 63, 94, 0.08)" : "rgba(255, 255, 255, 0.03)";
      item.style.borderRadius = "8px";
      item.style.border = `1px solid ${isDangling ? "rgba(244, 63, 94, 0.3)" : "var(--border-subtle)"}`;
      item.innerHTML = `
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
          <span class="badge ${badgeClass}">${d.defect_type}</span>
          <span style="font-size: 0.72rem; color: var(--text-muted);">${d.severity.toUpperCase()}</span>
        </div>
        <p style="font-size: 0.82rem; color: var(--text-secondary);">${d.description}</p>
      `;
      defectsContainer.appendChild(item);
    });
  }

  // Definitions
  const defsContainer = document.getElementById("definitionsList");
  document.getElementById("definitionCountBadge").textContent = `${definitions.length} Terms`;
  defsContainer.innerHTML = "";

  if (!definitions || definitions.length === 0) {
    defsContainer.innerHTML = `<p style="color: var(--text-muted); font-size: 0.85rem;">No explicit definitions defined.</p>`;
  } else {
    definitions.forEach(def => {
      const item = document.createElement("div");
      item.style.padding = "0.6rem 0.8rem";
      item.style.background = "rgba(255, 255, 255, 0.03)";
      item.style.borderRadius = "6px";
      item.style.border = "1px solid var(--border-subtle)";
      item.innerHTML = `
        <div style="font-weight: 600; font-size: 0.85rem; color: #38BDF8;">"${def.term}"</div>
        <div style="font-size: 0.8rem; color: var(--text-secondary);">${def.definition}</div>
      `;
      defsContainer.appendChild(item);
    });
  }
}

// Configure Perspective Buttons based on Doc Type
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

// Load Perspective Risk Assessment
async function loadRiskProfile(docId, perspective) {
  try {
    const res = await fetch(`/api/documents/${docId}/risk?perspective=${perspective}`);
    const risk = await res.json();

    const circle = document.getElementById("riskGaugeCircle");
    const scoreVal = document.getElementById("riskScoreValue");
    const tierTitle = document.getElementById("riskTierTitle");
    const summaryDesc = document.getElementById("riskSummaryDesc");
    const itemsContainer = document.getElementById("riskItemsList");
    const badge = document.getElementById("riskItemsCountBadge");

    scoreVal.textContent = risk.overall_risk_score;
    badge.textContent = `${risk.risk_items.length} Assessed`;

    // Dynamic coloring based on risk score
    if (risk.overall_risk_score > 70) {
      circle.className = "risk-circle";
      tierTitle.textContent = `High Risk Exposure for ${perspective.toUpperCase()}`;
      tierTitle.style.color = "var(--status-danger)";
      summaryDesc.textContent = `Multiple aggressive provisions, liability exposure, or structural flaws detected affecting the ${perspective}.`;
    } else if (risk.overall_risk_score > 40) {
      circle.className = "risk-circle";
      circle.style.borderColor = "var(--status-warning)";
      circle.style.background = "rgba(245, 158, 11, 0.08)";
      tierTitle.textContent = `Moderate Risk Exposure for ${perspective.toUpperCase()}`;
      tierTitle.style.color = "var(--status-warning)";
      summaryDesc.textContent = `Standard baseline provisions present with some non-standard clauses to review.`;
    } else {
      circle.className = "risk-circle low";
      tierTitle.textContent = `Low Risk Exposure for ${perspective.toUpperCase()}`;
      tierTitle.style.color = "var(--status-success)";
      summaryDesc.textContent = `Provisions align with market-standard bilateral conventions.`;
    }

    // Render Risk Items
    itemsContainer.innerHTML = "";
    if (risk.risk_items.length === 0) {
      itemsContainer.innerHTML = `<p style="color: var(--text-muted); padding: 1rem;">No notable risk deviations found.</p>`;
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
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span class="node-number">Clause ${item.clause_number}</span>
            <span style="font-weight: 700; font-size: 0.95rem;">${item.category.toUpperCase()}</span>
          </div>
          <div style="display: flex; gap: 0.5rem;">
            <span class="badge ${badgeClass}">Risk: ${item.perspective_risk.toUpperCase()}</span>
            <span class="badge badge-info">Deviation: ${item.deviation_rating.toUpperCase()}</span>
          </div>
        </div>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.6rem;">${item.rationale}</p>
        <div style="font-size: 0.8rem; background: rgba(0,0,0,0.3); padding: 0.6rem 0.8rem; border-radius: 6px; border-left: 3px solid var(--accent-primary);">
          <strong>Driving Text Span:</strong> "${item.driving_span}"
        </div>
      `;
      itemsContainer.appendChild(card);
    });

  } catch (err) {
    console.error("Failed to load risk profile:", err);
  }
}

// Grounded QA Interaction
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
  appendMessage("user", question);
  qaInput.value = "";

  // Append Thinking Bubble
  const thinkingId = "msg-thinking-" + Date.now();
  const thinkingNode = document.createElement("div");
  thinkingNode.id = thinkingId;
  thinkingNode.className = "message-card agent";
  thinkingNode.innerHTML = `<em>Analyzing clause hierarchy and retrieving citations...</em>`;
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

    // Render Agent Answer
    let contentHtml = `<p>${qaResult.answer}</p>`;

    // Refusal Guardrail Alert
    if (qaResult.is_refusal) {
      contentHtml += `
        <div class="refusal-alert">
          <strong>⚠️ Informational Guardrail:</strong> This query solicited legal advice or case prediction. ClauseLens operates strictly as an objective analytical engine and never provides legal advice.
        </div>
      `;
    }

    // Citations with Spans & BBoxes
    if (qaResult.cited_clauses && qaResult.cited_clauses.length > 0) {
      contentHtml += `<div class="citation-box"><strong>Grounded Clause Citations:</strong>`;
      qaResult.cited_clauses.forEach(c => {
        let spanCoords = "Coordinates: [54, 143, 401, 156]";
        if (c.spans && c.spans.length > 0) {
          spanCoords = `Pg ${c.spans[0].page} [${c.spans[0].bbox.map(Math.round).join(", ")}]`;
        }
        contentHtml += `
          <div class="citation-pill">
            <span>📍 Clause ${c.clause_number}: ${c.title}</span>
            <span style="color: var(--text-muted); font-size: 0.7rem;">(${spanCoords})</span>
          </div>
        `;
      });
      contentHtml += `</div>`;
    }

    appendMessage("agent", contentHtml);

  } catch (err) {
    thinkingNode.remove();
    appendMessage("agent", `<span style="color: var(--status-danger);">Error querying document QA endpoint.</span>`);
  }
}

function appendMessage(role, html) {
  const div = document.createElement("div");
  div.className = `message-card ${role}`;
  div.innerHTML = html;
  qaMessages.appendChild(div);
  qaMessages.scrollTop = qaMessages.scrollHeight;
}

// Compare Documents Handler
btnRunCompare.addEventListener("click", async () => {
  const doc1 = compareDoc1.value;
  const doc2 = compareDoc2.value;

  if (doc1 === doc2) {
    alert("Please select two different documents to compare.");
    return;
  }

  const container = document.getElementById("diffResultsContainer");
  container.innerHTML = `<p style="text-align: center; color: var(--text-muted);">Aligning clauses and calculating semantic shift...</p>`;

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

    // 1. Materially Modified Clauses (with Semantic Shifts)
    if (modifiedList.length > 0) {
      html += `<div class="diff-bucket modified"><h3 style="color: #FBBF24; margin-bottom: 0.8rem;">Δ Materially Changed Provisions</h3>`;
      modifiedList.forEach(m => {
        html += `
          <div style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem;">
            <div style="display: flex; justify-content: space-between; font-weight: 700; margin-bottom: 0.5rem;">
              <span>Clause ${m.clause_number_a || "§"} ➔ ${m.clause_number_b || "§"} (${m.title_b || m.title_a})</span>
              <span class="badge badge-warning">Similarity: ${(m.similarity_score * 100).toFixed(0)}%</span>
            </div>
            <div style="padding: 0.5rem 0.75rem; background: rgba(245, 158, 11, 0.12); border-left: 3px solid #F59E0B; margin-bottom: 0.6rem; font-size: 0.85rem; color: #FDE68A;">
              <strong>Semantic Shift Summary:</strong> ${m.semantic_change_summary || "Material wording or timeline modification."}
            </div>
            <div class="layout-split" style="font-size: 0.8rem;">
              <div style="color: #F87171;"><strong>v1 Original:</strong> "${m.text_a}"</div>
              <div style="color: #34D399;"><strong>v2 Revision:</strong> "${m.text_b}"</div>
            </div>
          </div>
        `;
      });
      html += `</div>`;
    }

    // 2. Added Clauses
    if (addedList.length > 0) {
      html += `<div class="diff-bucket added"><h3 style="color: var(--status-success); margin-bottom: 0.8rem;">+ Added Provisions (Present in v2 only)</h3>`;
      addedList.forEach(c => {
        html += `
          <div style="background: rgba(0,0,0,0.3); padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 0.5rem;">
            <div style="font-weight: 600; font-size: 0.9rem; color: #34D399;">Clause ${c.clause_number_b}: ${c.title_b}</div>
            <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.2rem;">${c.text_b}</p>
          </div>
        `;
      });
      html += `</div>`;
    }

    // 3. Removed Clauses
    if (removedList.length > 0) {
      html += `<div class="diff-bucket removed"><h3 style="color: var(--status-danger); margin-bottom: 0.8rem;">- Removed Provisions (Omitted in v2)</h3>`;
      removedList.forEach(c => {
        html += `
          <div style="background: rgba(0,0,0,0.3); padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 0.5rem;">
            <div style="font-weight: 600; font-size: 0.9rem; color: #F87171;">Clause ${c.clause_number_a}: ${c.title_a}</div>
            <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.2rem;">${c.text_a}</p>
          </div>
        `;
      });
      html += `</div>`;
    }

    container.innerHTML = html || `<p style="color: var(--status-success); text-align: center;">Documents are identical with no material deviations.</p>`;

  } catch (err) {
    container.innerHTML = `<p style="color: var(--status-danger);">Failed to execute semantic comparison.</p>`;
  }
});

// Actionable 1: Deadlines
async function loadDeadlines() {
  const baseDate = document.getElementById("effectiveDateInput").value || "2026-10-01";
  const container = document.getElementById("deadlinesTimeline");
  container.innerHTML = `<p style="color: var(--text-muted);">Extracting obligations timeline...</p>`;

  try {
    const res = await fetch(`/api/documents/${currentDocId}/actionable/deadlines?effective_date=${baseDate}`);
    const data = await res.json();

    container.innerHTML = "";
    if (!data.deadlines || data.deadlines.length === 0) {
      container.innerHTML = `<p style="color: var(--text-muted); padding: 1rem;">No time-bound deadlines detected in this document.</p>`;
      return;
    }

    data.deadlines.forEach(dl => {
      const item = document.createElement("div");
      item.className = "timeline-item";
      item.innerHTML = `
        <div class="timeline-dot"></div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
          <span style="font-family: var(--font-mono); font-weight: 700; color: var(--accent-primary); font-size: 0.95rem;">${dl.resolved_date || 'Relative'}</span>
          <span class="badge badge-info">${(dl.party || 'PARTY').toUpperCase()}</span>
        </div>
        <h4 style="font-size: 0.95rem; margin-bottom: 0.25rem;">Clause ${dl.clause_number}: ${dl.obligation}</h4>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.4rem;">Trigger: ${dl.trigger} (${dl.relative_days} days offset)</div>
      `;
      container.appendChild(item);
    });

  } catch (err) {
    container.innerHTML = `<p style="color: var(--status-danger);">Failed to load deadlines.</p>`;
  }
}

// Export .ics Calendar
document.getElementById("btnExportIcs").addEventListener("click", () => {
  const baseDate = document.getElementById("effectiveDateInput").value || "2026-10-01";
  window.open(`/api/documents/${currentDocId}/actionable/deadlines/ics?effective_date=${baseDate}`, "_blank");
});

// Actionable 2: Lawyer-Prep
async function loadLawyerPrep() {
  const container = document.getElementById("lawyerPrepContent");
  container.innerHTML = `<p style="color: var(--text-muted);">Compiling Lawyer Consultation Brief...</p>`;

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
      <div style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; margin-bottom: 1.25rem;">
        <h3 style="font-size: 1rem; margin-bottom: 0.5rem; color: var(--accent-primary);">1. Executive Document Summary</h3>
        <div style="font-size: 0.88rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 0.3rem;">
          ${factsHtml}
        </div>
      </div>

      <div style="margin-bottom: 1.25rem;">
        <h3 style="font-size: 1rem; margin-bottom: 0.5rem; color: #F59E0B;">2. Document Integrity Audit Checklist</h3>
        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
          ${checklist.map(item => `
            <div style="display: flex; align-items: center; gap: 0.6rem; font-size: 0.85rem; padding: 0.5rem 0.8rem; background: rgba(255,255,255,0.02); border-radius: 6px;">
              <span>${item.status === 'pass' || item.passed ? "✅" : "⚠️"}</span>
              <span style="font-weight: 600; min-width: 160px;">${item.name || item.item || "Check"}:</span>
              <span style="color: var(--text-secondary);">${item.notes || item.status || ""}</span>
            </div>
          `).join("")}
        </div>
      </div>

      <div>
        <h3 style="font-size: 1rem; margin-bottom: 0.5rem; color: var(--status-danger);">3. Prioritized Questions for Counsel</h3>
        <div style="display: flex; flex-direction: column; gap: 0.75rem;">
          ${questions.map((q, idx) => `
            <div style="background: rgba(244, 63, 94, 0.05); border: 1px solid rgba(244, 63, 94, 0.25); border-radius: 8px; padding: 0.85rem;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                <span class="badge ${q.priority === 'critical' ? 'badge-danger' : 'badge-warning'}">Priority: ${(q.priority || 'MEDIUM').toUpperCase()}</span>
                <span class="node-number">Target: Clause ${q.clause_number || q.clause_id}</span>
              </div>
              <p style="font-size: 0.9rem; font-weight: 600; color: white;">"${q.question}"</p>
              <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">Context: ${q.context_reason || q.rationale || ""}</p>
            </div>
          `).join("")}
        </div>
      </div>
    `;

    container.innerHTML = html;

  } catch (err) {
    container.innerHTML = `<p style="color: var(--status-danger);">Failed to load lawyer prep pack.</p>`;
  }
}

// Actionable 3: Plain-Language Rewrites & Indic Translations
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
  container.innerHTML = `<p style="color: var(--text-muted);">Generating plain-language translations (${currentLang.toUpperCase()})...</p>`;

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
      card.style.background = "rgba(0,0,0,0.3)";
      card.style.border = "1px solid var(--border-subtle)";
      card.style.borderRadius = "8px";
      card.style.padding = "1rem";
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
          <span class="node-number">Clause ${sc.clause_number}: ${sc.title || ''}</span>
          <span class="badge badge-info">${data.language.toUpperCase()} · ${data.level ? data.level.toUpperCase() : ''}</span>
        </div>
        <p style="font-size: 0.92rem; color: #F8FAFC; margin-bottom: 0.5rem; line-height: 1.6;">${sc.simplified_text}</p>
        <details style="font-size: 0.78rem; color: var(--text-muted); cursor: pointer;">
          <summary>View Original Legalese</summary>
          <p style="margin-top: 0.3rem; padding: 0.4rem; background: rgba(255,255,255,0.02); border-radius: 4px;">${sc.original_text}</p>
        </details>
      `;
      container.appendChild(card);
    });

  } catch (err) {
    container.innerHTML = `<p style="color: var(--status-danger);">Failed to load rewrites.</p>`;
  }
}

// Actionable 4: Negotiations
async function loadNegotiations() {
  const container = document.getElementById("negotiationCardsContainer");
  container.innerHTML = `<p style="color: var(--text-muted);">Generating balanced negotiation counter-proposals...</p>`;

  try {
    const res = await fetch(`/api/documents/${currentDocId}/actionable/negotiations`);
    const proposals = await res.json();

    container.innerHTML = "";
    if (proposals.length === 0) {
      container.innerHTML = `<p style="color: var(--status-success); padding: 1rem;">No aggressive or one-sided terms found requiring counter-proposals.</p>`;
      return;
    }

    proposals.forEach(p => {
      const card = document.createElement("div");
      card.style.background = "rgba(245, 158, 11, 0.05)";
      card.style.border = "1px solid rgba(245, 158, 11, 0.25)";
      card.style.borderRadius = "8px";
      card.style.padding = "1.1rem";
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <span class="node-number">Clause ${p.clause_number} (${p.category.toUpperCase()})</span>
          <span class="badge badge-warning">Counter-Proposal</span>
        </div>
        <div style="font-size: 0.85rem; color: #F87171; margin-bottom: 0.6rem;">
          <strong>Original Aggressive Provision:</strong> "${p.original_text}"
        </div>
        <div style="font-size: 0.9rem; color: #34D399; background: rgba(16, 185, 129, 0.1); padding: 0.75rem; border-radius: 6px; border-left: 3px solid #10B981; margin-bottom: 0.5rem;">
          <strong>Proposed Balanced Alternative:</strong> "${p.proposed_alternative_text || p.proposed_alternative}"
        </div>
        <div style="font-size: 0.8rem; color: var(--text-secondary);">
          <strong>One-Line Rationale:</strong> ${p.one_line_rationale || p.rationale}
        </div>
      `;
      container.appendChild(card);
    });

  } catch (err) {
    container.innerHTML = `<p style="color: var(--status-danger);">Failed to load negotiation proposals.</p>`;
  }
}

// Switch Document Listener
docSelector.addEventListener("change", (e) => {
  const selected = e.target.value;
  if (selected) loadDocument(selected);
});

// Upload Modal Logic
const uploadModal = document.getElementById("uploadModal");
const btnOpenUpload = document.getElementById("btnOpenUpload");
const btnCloseUpload = document.getElementById("btnCloseUpload");
const btnChooseFile = document.getElementById("btnChooseFile");
const fileInput = document.getElementById("fileInput");
const dropzone = document.getElementById("dropzone");
const uploadStatus = document.getElementById("uploadStatus");

btnOpenUpload.addEventListener("click", () => {
  uploadModal.classList.add("open");
  uploadStatus.textContent = "";
});

btnCloseUpload.addEventListener("click", () => {
  uploadModal.classList.remove("open");
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
  uploadStatus.innerHTML = `<em>Uploading and parsing "${file.name}" through pipeline...</em>`;
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
      return;
    }

    const data = await res.json();
    uploadStatus.innerHTML = `<span style="color: var(--status-success);">Success! Ingested ${data.document.clauses.length} clauses.</span>`;
    
    // Refresh doc list and select uploaded doc
    setTimeout(async () => {
      uploadModal.classList.remove("open");
      await initApp();
      docSelector.value = data.document.id;
      loadDocument(data.document.id);
    }, 1000);

  } catch (err) {
    uploadStatus.innerHTML = `<span style="color: var(--status-danger);">Network or server error during upload.</span>`;
  }
}

// Run init on DOM ready
document.addEventListener("DOMContentLoaded", initApp);
