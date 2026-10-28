const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function api(url, opts) {
  const res = await fetch(url, opts && { headers: { "Content-Type": "application/json" }, ...opts });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2200);
}

// Tabs
document.querySelectorAll(".tab").forEach((btn) =>
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab, .panel").forEach((e) => e.classList.remove("active"));
    btn.classList.add("active");
    $("#" + btn.dataset.tab).classList.add("active");
    if (btn.dataset.tab === "students") loadStudents();
    if (btn.dataset.tab === "mark") loadMark();
    if (btn.dataset.tab === "report") loadReport();
  })
);

// Students
async function loadStudents() {
  const students = await api("/api/students");
  $("#student-body").innerHTML = students.map((s) =>
    `<tr><td>${esc(s.roll_no)}</td><td>${esc(s.name)}</td><td>${esc(s.class_name)}</td>
     <td><button class="danger" data-id="${s.id}">Delete</button></td></tr>`).join("");
}

$("#student-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/students", { method: "POST", body: JSON.stringify({
      roll_no: $("#roll").value, name: $("#name").value, class_name: $("#cls").value }) });
    e.target.reset();
    loadStudents();
    toast("Student added");
  } catch (err) { toast(err.message); }
});

$("#student-body").addEventListener("click", async (e) => {
  const id = e.target.dataset.id;
  if (id && confirm("Delete this student and their attendance records?")) {
    await api("/api/students/" + id, { method: "DELETE" });
    loadStudents();
  }
});

// Mark attendance
$("#mark-date").value = new Date().toISOString().slice(0, 10);
$("#mark-date").addEventListener("change", loadMark);

async function loadMark() {
  const date = $("#mark-date").value;
  const [students, saved] = await Promise.all([api("/api/students"), api("/api/attendance?date=" + date)]);
  $("#mark-body").innerHTML = students.map((s) => {
    const status = saved[s.id] || "Present";
    return `<tr data-id="${s.id}"><td>${esc(s.roll_no)}</td><td>${esc(s.name)}</td>
      <td><input type="radio" name="st${s.id}" value="Present" ${status === "Present" ? "checked" : ""}></td>
      <td><input type="radio" name="st${s.id}" value="Absent" ${status === "Absent" ? "checked" : ""}></td></tr>`;
  }).join("");
}

$("#all-present").addEventListener("click", () =>
  document.querySelectorAll('#mark-body input[value="Present"]').forEach((r) => (r.checked = true)));

$("#save-att").addEventListener("click", async () => {
  const records = [...document.querySelectorAll("#mark-body tr")].map((tr) => ({
    student_id: +tr.dataset.id,
    status: tr.querySelector("input:checked").value,
  }));
  try {
    await api("/api/attendance", { method: "POST", body: JSON.stringify({ date: $("#mark-date").value, records }) });
    toast("Attendance saved");
  } catch (err) { toast(err.message); }
});

// Reports
function reportQuery() {
  const p = new URLSearchParams();
  if ($("#from").value) p.set("start", $("#from").value);
  if ($("#to").value) p.set("end", $("#to").value);
  return p.toString();
}

async function loadReport() {
  const q = reportQuery();
  $("#csv").href = "/api/report.csv?" + q;
  const rows = await api("/api/report?" + q);
  $("#report-body").innerHTML = rows.map((r) =>
    `<tr class="${r.total && r.percentage < 75 ? "low" : ""}">
      <td>${esc(r.roll_no)}</td><td>${esc(r.name)}</td><td>${esc(r.class_name)}</td>
      <td>${r.total}</td><td>${r.present}</td><td>${r.absent}</td><td><b>${r.percentage}%</b></td></tr>`).join("");
}
$("#gen").addEventListener("click", loadReport);

loadStudents();
