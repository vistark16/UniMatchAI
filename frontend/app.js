// ===== Unimatch AI - Frontend (University + Major Selection) =====
const API_BASE = window.API_BASE || "http://127.0.0.1:8000";

const GRADE_FIELDS = [
  "s1","s2","s3","s4","s5",
  "math","language","physics","chemistry","biology",
  "economics","geography","history"
];
const NUMERIC_FIELDS = [...GRADE_FIELDS, "rank_percentile"];

function $(id){ return document.getElementById(id); }
function clamp(n,min,max){ if(Number.isNaN(n)) return undefined; return Math.max(min, Math.min(max, n)); }

function val(id){
  const el = $(id); if(!el) return undefined;
  const raw = el.value?.trim(); if(raw === "") return undefined;
  if(!isNaN(Number(raw)) && NUMERIC_FIELDS.includes(id)){
    let n = Number(raw);
    if(GRADE_FIELDS.includes(id)) n = clamp(n,0,100);
    if(id === "rank_percentile") n = clamp(Math.round(n),1,100);
    return n;
  }
  return raw;
}

function atLeastOneGradeFilled(){
  return GRADE_FIELDS.slice(0,5).some(k => typeof val(k) === "number");
}

/* ====== Data Storage ====== */
const UNIVERSITIES_DATA = { all: [] };
const MAJORS_DATA = { all: [] };

/* ====== University + Major Selection System ====== */
const SELECTION_PAIRS = {
  choice1: { 
    university: { selected: null, input: null, dropdown: null, selectedDiv: null, box: null },
    major: { selected: null, input: null, dropdown: null, selectedDiv: null, box: null, disabled: true }
  },
  choice2: { 
    university: { selected: null, input: null, dropdown: null, selectedDiv: null, box: null },
    major: { selected: null, input: null, dropdown: null, selectedDiv: null, box: null, disabled: true }
  },
  choice3: { 
    university: { selected: null, input: null, dropdown: null, selectedDiv: null, box: null },
    major: { selected: null, input: null, dropdown: null, selectedDiv: null, box: null, disabled: true }
  }
};

function programOfMajor(university, name) {
  if (!university || !name) return "unknown";
  
  const key = `${university} | ${name}`;
  const details = MAJORS_DATA.details[key];
  
  // Jika ada data detail, gunakan program dari sana
  if (details && details.program) {
    return details.program.toLowerCase();
  }
  
  // Fallback ke deteksi berdasarkan nama major
  const s = (name || "").toLowerCase();
  const saintek = ["fisika","kimia","biologi","kedokteran","informatika","statistika","elektro","mesin","teknik","matematika","farmasi","geologi","perikanan","arsitektur","kehutanan","pertanian","perkapalan"];
  const soshum  = ["hukum","ekonomi","manajemen","akuntansi","psikologi","sosiologi","sejarah","ilmu","komunikasi","bahasa","pendidikan","administrasi","hubungan","politik","pariwisata","bisnis"];
  
  if (saintek.some(k => s.includes(k))) return "saintek";
  if (soshum.some(k => s.includes(k))) return "soshum";
  return "unknown";
}

function loadUniversitiesOptions(){
  return fetch(`${API_BASE}/api/kb/universities`)
    .then(r=>r.json())
    .then(d=>{
      UNIVERSITIES_DATA.all = Array.isArray(d.universities) ? d.universities : [];
    })
    .catch(()=>{ UNIVERSITIES_DATA.all = []; });
}

function loadMajorsOptions() {
  return fetch(`${API_BASE}/api/kb/majors-full`)  // Endpoint baru
    .then(r => r.json())
    .then(d => {
      MAJORS_DATA.all = Array.isArray(d.majors) ? d.majors : [];
      MAJORS_DATA.details = d.details || {};
    })
    .catch(() => { 
      MAJORS_DATA.all = [];
      MAJORS_DATA.details = {};
    });
}

function getMajorsForUniversity(universityName) {
  // This would ideally come from an API endpoint that returns majors for a specific university
  // For now, we'll filter based on program type and return all majors
  // In a real implementation, you'd call: `/api/kb/universities/${universityName}/majors`
  
   if (!universityName) return [];
  
  // Filter major berdasarkan universitas yang dipilih
  return MAJORS_DATA.all.filter(m => {
    // Format key di KB: "Universitas | Major"
    const uniMajorKey = `${universityName} | ${m}`;
    return MAJORS_DATA.details[uniMajorKey] !== undefined;
  });
}

function getSelectedUniversities() {
  const selected = [];
  Object.keys(SELECTION_PAIRS).forEach(key => {
    if (SELECTION_PAIRS[key].university.selected) {
      selected.push(SELECTION_PAIRS[key].university.selected);
    }
  });
  return selected;
}

function getSelectedMajors() {
  const selected = [];
  Object.keys(SELECTION_PAIRS).forEach(key => {
    if (SELECTION_PAIRS[key].major.selected) {
      selected.push(SELECTION_PAIRS[key].major.selected);
    }
  });
  return selected;
}

function getAvailableUniversities(currentKey) {
  const alreadySelected = new Set();
  
  // Collect already selected universities from other selectors
  Object.keys(SELECTION_PAIRS).forEach(key => {
    if (key !== currentKey && SELECTION_PAIRS[key].university.selected) {
      alreadySelected.add(SELECTION_PAIRS[key].university.selected);
    }
  });

  return UNIVERSITIES_DATA.all.filter(u => !alreadySelected.has(u));
}

function getAvailableMajorsForChoice(choiceKey) {
  const universitySelected = SELECTION_PAIRS[choiceKey].university.selected;
  if (!universitySelected) return [];
  
  const alreadySelectedMajors = new Set();
  
  // Collect already selected majors from other selectors
  Object.keys(SELECTION_PAIRS).forEach(key => {
    if (key !== choiceKey && SELECTION_PAIRS[key].major.selected) {
      alreadySelectedMajors.add(SELECTION_PAIRS[key].major.selected);
    }
  });

  // Get majors for the selected university and filter out already selected ones
  return getMajorsForUniversity(universitySelected)
    .filter(m => !alreadySelectedMajors.has(m));
}

function renderSelectedItem(choiceKey, type) {
  const selector = SELECTION_PAIRS[choiceKey][type];
  const selectedDiv = selector.selectedDiv;
  
  if (selector.selected) {
    selectedDiv.innerHTML = `
      <div class="selected-chip">
        ${selector.selected}
        <button class="remove-btn" data-choice="${choiceKey}" data-type="${type}">×</button>
      </div>
    `;
    selector.input.style.display = 'none';
    
    // Add remove handler
    selectedDiv.querySelector('.remove-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      clearSelection(choiceKey, type);
    });
  } else {
    selectedDiv.innerHTML = '';
    selector.input.style.display = 'block';
  }
}

function clearSelection(choiceKey, type) {
  SELECTION_PAIRS[choiceKey][type].selected = null;
  SELECTION_PAIRS[choiceKey][type].input.value = '';
  SELECTION_PAIRS[choiceKey][type].dropdown.hidden = true;
  renderSelectedItem(choiceKey, type);
  
  // If clearing university, also clear and disable major
  if (type === 'university') {
    clearSelection(choiceKey, 'major');
    setMajorDisabled(choiceKey, true);
  }
}

function selectItem(choiceKey, type, item) {
  SELECTION_PAIRS[choiceKey][type].selected = item;
  SELECTION_PAIRS[choiceKey][type].input.value = '';
  SELECTION_PAIRS[choiceKey][type].dropdown.hidden = true;
  renderSelectedItem(choiceKey, type);
  
  // If selecting university, enable major selection and clear any existing major
  if (type === 'university') {
    clearSelection(choiceKey, 'major');
    setMajorDisabled(choiceKey, false);
  }
}

function setMajorDisabled(choiceKey, disabled) {
  const majorSelector = SELECTION_PAIRS[choiceKey].major;
  majorSelector.disabled = disabled;
  majorSelector.box.classList.toggle('disabled', disabled);
  majorSelector.input.disabled = disabled;
  if (disabled) {
    majorSelector.input.placeholder = 'Select university first';
  } else {
    majorSelector.input.placeholder = 'Type to search major';
  }
}

function showAllOptions(choiceKey, type) {
  const selector = SELECTION_PAIRS[choiceKey][type];
  let available = [];
  
  if (type === 'university') {
    available = getAvailableUniversities(choiceKey);
  } else if (type === 'major') {
    if (selector.disabled) return;
    available = getAvailableMajorsForChoice(choiceKey);
  }

  if (!available.length) {
    const message = type === 'university' ? 'No universities available.' : 'No majors available.';
    selector.dropdown.innerHTML = `<div class="empty">${message}</div>`;
    selector.dropdown.hidden = false;
    return;
  }

  selector.dropdown.innerHTML = available.slice(0, 12).map(item => 
    `<div class="opt" data-choice="${choiceKey}" data-type="${type}" data-item="${encodeURIComponent(item)}">${item}</div>`
  ).join("");
  
  // Ensure proper z-index before showing
  selector.dropdown.style.zIndex = '9999';
  selector.dropdown.hidden = false;

  // Add click handlers
  selector.dropdown.querySelectorAll(".opt").forEach(opt => {
    opt.addEventListener("mousedown", (e) => {
      e.preventDefault();
      const item = decodeURIComponent(opt.dataset.item);
      const targetChoice = opt.dataset.choice;
      const targetType = opt.dataset.type;
      selectItem(targetChoice, targetType, item);
    });
  });
}

function renderSearchResults(choiceKey, type, query) {
  const selector = SELECTION_PAIRS[choiceKey][type];
  
  if (!query) {
    selector.dropdown.hidden = true;
    return;
  }
  
  let available = [];
  if (type === 'university') {
    available = getAvailableUniversities(choiceKey);
  } else if (type === 'major') {
    if (selector.disabled) return;
    available = getAvailableMajorsForChoice(choiceKey);
  }
  
  const filtered = available.filter(item => 
    item.toLowerCase().includes(query.toLowerCase())
  ).slice(0, 12);

  if (!filtered.length) {
    selector.dropdown.innerHTML = `<div class="empty">No matches for "${query}".</div>`;
    selector.dropdown.style.zIndex = '9999';
    selector.dropdown.hidden = false;
    return;
  }
  
  selector.dropdown.innerHTML = filtered.map(item => 
    `<div class="opt" data-choice="${choiceKey}" data-type="${type}" data-item="${encodeURIComponent(item)}">${item}</div>`
  ).join("");
  
  selector.dropdown.style.zIndex = '9999';
  selector.dropdown.hidden = false;

  // Add click handlers
  selector.dropdown.querySelectorAll(".opt").forEach(opt => {
    opt.addEventListener("mousedown", (e) => {
      e.preventDefault();
      const item = decodeURIComponent(opt.dataset.item);
      const targetChoice = opt.dataset.choice;
      const targetType = opt.dataset.type;
      selectItem(targetChoice, targetType, item);
    });
  });
}

function initSingleSelector(choiceKey, type) {
  const selector = SELECTION_PAIRS[choiceKey][type];
  selector.box = $(`${choiceKey}${type.charAt(0).toUpperCase() + type.slice(1)}Box`);
  selector.input = $(`${choiceKey}${type.charAt(0).toUpperCase() + type.slice(1)}Input`);
  selector.dropdown = $(`${choiceKey}${type.charAt(0).toUpperCase() + type.slice(1)}Dropdown`);
  selector.selectedDiv = $(`${choiceKey}${type.charAt(0).toUpperCase() + type.slice(1)}Selected`);

  // Set initial disabled state for majors
  if (type === 'major') {
    setMajorDisabled(choiceKey, true);
  }

  // Event listeners
  selector.input.addEventListener("input", () => {
    renderSearchResults(choiceKey, type, selector.input.value.trim());
  });
  
  selector.input.addEventListener("focus", () => {
    if (type === 'major' && selector.disabled) return;
    const query = selector.input.value.trim();
    if (query) {
      renderSearchResults(choiceKey, type, query);
    }
  });
  
  selector.input.addEventListener("keydown", (e) => {
    if (type === 'major' && selector.disabled) return;
    if (e.key === "Enter") {
      e.preventDefault();
      const first = selector.dropdown.querySelector(".opt");
      if (first) first.dispatchEvent(new MouseEvent("mousedown"));
    } else if (e.key === "Escape") {
      selector.dropdown.hidden = true;
    }
  });
  
  selector.box.addEventListener("click", (e) => {
    // Don't trigger if clicking remove button
    if (e.target.matches('.remove-btn')) return;
    if (type === 'major' && selector.disabled) return;
    
    if (selector.selected) {
      // If already selected, show options to change
      selector.input.style.display = 'block';
      selector.input.focus();
      showAllOptions(choiceKey, type);
    } else {
      // Show all available options
      selector.input.focus();
      showAllOptions(choiceKey, type);
    }
  });
  
  selector.input.addEventListener("blur", () => {
    setTimeout(() => selector.dropdown.hidden = true, 200);
  });

  // Dalam fungsi initSingleSelector untuk university
  selector.input.addEventListener("change", () => {
    const query = selector.input.value.trim();
    if (query) {
      renderSearchResults(choiceKey, 'university', query);
    }
  
  // Setelah memilih universitas, update major options
    if (selector.selected) {
      setMajorDisabled(choiceKey, false);
      showAllOptions(choiceKey, 'major');
    }
  });
}

function initSelectors() {
  Object.keys(SELECTION_PAIRS).forEach(choiceKey => {
    initSingleSelector(choiceKey, 'university');
    initSingleSelector(choiceKey, 'major');
  });
  
  // Program change handler
  $("program").addEventListener("change", () => {
    // Hide all dropdowns and refresh if any are open
    Object.keys(SELECTION_PAIRS).forEach(choiceKey => {
      ['university', 'major'].forEach(type => {
        const selector = SELECTION_PAIRS[choiceKey][type];
        if (!selector.dropdown.hidden) {
          if (selector.input.value.trim()) {
            renderSearchResults(choiceKey, type, selector.input.value.trim());
          } else {
            showAllOptions(choiceKey, type);
          }
        }
      });
    });
  });

  // Load data
  Promise.all([loadUniversitiesOptions(), loadMajorsOptions()]);
}

/* ====== Payload & Rendering ====== */
function collectPayload(){
  const selectedUniversities = getSelectedUniversities();
  const selectedMajors = getSelectedMajors();
  
  return {
    program: val("program"),
    target_university: selectedUniversities[0] || "Unknown",
    target_universities: selectedUniversities,
    target_university_1: SELECTION_PAIRS.choice1.university.selected || null,
    target_university_2: SELECTION_PAIRS.choice2.university.selected || null,
    target_university_3: SELECTION_PAIRS.choice3.university.selected || null,
    target_major: selectedMajors[0] || "Unknown",
    target_majors: selectedMajors,
    target_major_1: SELECTION_PAIRS.choice1.major.selected || null,
    target_major_2: SELECTION_PAIRS.choice2.major.selected || null,
    target_major_3: SELECTION_PAIRS.choice3.major.selected || null,
    competitiveness: val("competitiveness"),
    s1: val("s1"), s2: val("s2"), s3: val("s3"), s4: val("s4"), s5: val("s5"),
    math: val("math"), language: val("language"),
    physics: val("physics"), chemistry: val("chemistry"), biology: val("biology"),
    economics: val("economics"), geography: val("geography"), history: val("history"),
    rank_percentile: val("rank_percentile") ?? 100,
    achievement: val("achievement"),
    accreditation: val("accreditation"),
  };
}

function renderResult(data){
  const el = $("result");
  if(data.error){ 
    el.className="error"; 
    el.innerHTML = Array.isArray(data.error) 
      ? `<strong>Please check:</strong><ul>${data.error.map(e => `<li>${e}</li>`).join('')}</ul>`
      : `Error: ${data.error}`; 
    return; 
  }
  const p = (data.probability*100).toFixed(1)+"%";
  const tips = (data.tips||[]).map(t=>`<li>${t}</li>`).join("");
  el.className="result";
  el.innerHTML = `
    <div class="prob">
      <div class="bar"><div class="fill ${data.label}" style="width:${(data.probability*100).toFixed(0)}%"></div></div>
      <div class="meta"><strong>Probability:</strong> ${p} &nbsp; <strong>Label:</strong> ${data.label.toUpperCase()}</div>
    </div>
    <details><summary>Details</summary><pre>${JSON.stringify(data.details,null,2)}</pre></details>
    ${tips ? `<h3>Recommendations</h3><ul>${tips}</ul>` : ""}
  `;
}

function tableHtml(title, list){
  if(!list || !list.length) return "";
  const rows = list.map((it, i)=>`
    <tr>
      <td>${i+1}</td>
      <td>${it.university||"-"}</td>
      <td>
        ${it.major||"-"}
        ${(it.tags && it.tags.length) ? `<div class="tags">${
          it.tags.slice(0,3).map(t=>`<span class="tag">${t}</span>`).join("")
        }</div>` : ""}
      </td>
      <td>${(it.probability*100).toFixed(1)}%</td>
      <td>${(it.competitiveness||"-").toUpperCase()}</td>
      <td><span class="badge ${it.bucket||'target'}">${(it.bucket||'target').toUpperCase()}</span></td>
    </tr>
  `).join("");
  return `
    <h3 class="section-heading" style="margin-top:18px">${title}</h3>
    <div class="table-wrap">
      <table class="tbl">
        <thead><tr><th>#</th><th>University</th><th>Major</th><th>Prob.</th><th>Comp.</th><th>Band</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function renderRecommendations(blocks){
  const el = $("result");
  if(!blocks) return;
  const { preferred=[], alternatives=[] } = blocks;
  el.insertAdjacentHTML("beforeend",
    tableHtml("Universities for Your Chosen Majors", preferred) +
    tableHtml("You Might Also Consider", alternatives)
  );
}

function setLoading(v){
  const b=$("predictBtn"); if(!b) return;
  b.disabled=v;
  if(v){ 
    b.dataset._t=b.textContent; 
    b.innerHTML=`<span class="btn-dot"></span> Predicting…`; 
  } else { 
    b.textContent=b.dataset._t||"Predict"; 
  }
}

/* ====== Enhanced Validation ====== */
function validateForm() {
  const issues = [];
  
  // Basic validation
  if (!atLeastOneGradeFilled()) {
    issues.push("Please fill at least one of S1—S5 grades");
  }
  
  // University and major selection validation
  const selectedUniversities = getSelectedUniversities();
  const selectedMajors = getSelectedMajors();
  
  if (selectedUniversities.length === 0) {
    issues.push("Please select at least one target university");
  }
  
  if (selectedMajors.length === 0) {
    issues.push("Please select at least one target major");
  }
  
  // Check if each university has a corresponding major
  Object.keys(SELECTION_PAIRS).forEach((key, index) => {
    const univSelected = SELECTION_PAIRS[key].university.selected;
    const majorSelected = SELECTION_PAIRS[key].major.selected;
    
    if (univSelected && !majorSelected) {
      issues.push(`Please select a major for Choice ${index + 1} (${univSelected})`);
    }
  });
  
  // Program-specific validation
  const program = val("program");
  
  if (program === "saintek" && selectedMajors.length > 0) {
    if (!val("math")) {
      issues.push("Math grade is highly recommended for Saintek program");
    }
    if (!val("physics") && !val("chemistry") && !val("biology")) {
      issues.push("At least one science subject (Physics/Chemistry/Biology) is recommended");
    }
  }
  
  if (program === "soshum" && selectedMajors.length > 0) {
    if (!val("language")) {
      issues.push("Language grade is highly recommended for Soshum program");
    }
  }
  
  return issues;
}

/* ====== Events ====== */
$("predictBtn").addEventListener("click", async ()=>{
  const el=$("result");
  
  // Enhanced validation
  const issues = validateForm();
  if (issues.length > 0) {
    renderResult({ error: issues });
    return;
  }
  
  const payload = collectPayload();
  setLoading(true);
  try{
    const res = await fetch(`${API_BASE}/api/predict`, {
      method:"POST", 
      headers:{"Content-Type":"application/json"}, 
      body:JSON.stringify(payload)
    });
    
    if (!res.ok) {
      throw new Error(`Server error: ${res.status}`);
    }
    
    const data = await res.json();
    renderResult(data);

    const recRes = await fetch(`${API_BASE}/api/recommend?pref_n=8&alt_n=8&per_uni=2`, {
      method:"POST", 
      headers:{"Content-Type":"application/json"}, 
      body:JSON.stringify(payload)
    });
    
    if (recRes.ok) {
      const rec = await recRes.json();
      if(rec.preferred || rec.alternatives) renderRecommendations(rec);
    }
  }catch(err){
    console.error('Prediction error:', err);
    renderResult({
      error: err.message || 'Unable to connect to server. Please try again.'
    });
  }finally{ 
    setLoading(false); 
  }
});

$("resetBtn").addEventListener("click", ()=>{
  document.querySelectorAll("input,select").forEach(el=>{ el.value=""; });
  $("program").value="saintek"; 
  $("competitiveness").value="high"; 
  $("achievement").value="none"; 
  $("accreditation").value="B";
  $("rank_percentile").value="100";
  
  // Reset all selections
  Object.keys(SELECTION_PAIRS).forEach(choiceKey => {
    clearSelection(choiceKey, 'university');
    clearSelection(choiceKey, 'major');
    setMajorDisabled(choiceKey, true);
  });
  
  const res=$("result"); 
  res.className="muted"; 
  res.textContent="Fill the form and click Predict.";
});

/* ===== Theme toggle ===== */
(function () {
  const KEY="unimatch_theme", root=document.documentElement;
  function apply(t){ root.setAttribute("data-theme", t); }
  let saved=localStorage.getItem(KEY);
  if(!saved) saved = (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark":"light";
  apply(saved);
  const btn=$("themeToggle");
  if(btn){ 
    btn.addEventListener("click", ()=>{ 
      const next=root.getAttribute("data-theme")==="dark"?"light":"dark"; 
      apply(next); 
      localStorage.setItem(KEY,next); 
    }); 
  }
})();

/* ===== Init ===== */
document.addEventListener("DOMContentLoaded", ()=>{ 
  initSelectors(); 
});