const $ = (id) => document.getElementById(id);
const STAGES = ["baseline", "audit", "reproduction", "regression"];
const LABELS = { baseline: "Baseline", audit: "Audit", reproduction: "Reproduction", regression: "Regression" };
const MEANING = {
  VERIFIED: "The approved test failed on your original code and passes with this fix. Your existing tests still pass.",
  FAILED: "No fix passed every check. Your original code was not changed.",
  INCONCLUSIVE: "The check could not finish (timeout, sandbox error or AI error). This is neither a pass nor a fail.",
};
const EXAMPLES = {
  "Empty list crashes": {
    source: "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)\n",
    error: "ZeroDivisionError: division by zero when numbers is []",
    expected: "Return None for an empty list. Otherwise return the arithmetic average.",
    reg: "from calculator import calculate_average\n\ndef test_normal_average():\n    assert calculate_average([2, 4, 6]) == 4\n",
  },
  "Off-by-one slice": {
    source: "def first_n(items, n):\n    return items[:n - 1]\n",
    error: "first_n([1, 2, 3], 2) returned [1] but should return [1, 2]",
    expected: "first_n(items, n) returns the first n items of the list.",
    reg: "from calculator import first_n\n\ndef test_empty():\n    assert first_n([], 2) == []\n",
  },
  "Blank form": { source: "", error: "", expected: "", reg: "" },
};

let lastReport = null;

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text; // model output is untrusted: textContent only
  return n;
}

function show(n) {
  ["p1", "p2", "p3"].forEach((id, i) => ($(id).hidden = i + 1 !== n));
  [1, 2, 3].forEach((i) => ($("st" + i).className = i === n ? "on" : i < n ? "done" : ""));
  window.scrollTo(0, 0);
}

async function post(url, body) {
  let res;
  try {
    res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  } catch {
    throw new Error("Could not reach the server. Is it running?");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    throw new Error(typeof d === "string" ? d : "Request failed (" + res.status + ").");
  }
  return data;
}

function busy(btn, text, on) {
  if (on) { btn.dataset.label = btn.textContent; btn.textContent = text; btn.disabled = true; }
  else { btn.textContent = btn.dataset.label; btn.disabled = false; }
}

function loadExample(name) {
  const e = EXAMPLES[name];
  $("source").value = e.source; $("error").value = e.error; $("expected").value = e.expected; $("reg").value = e.reg;
}

$("example").append(...Object.keys(EXAMPLES).map((k) => Object.assign(el("option"), { value: k, textContent: k })));
$("example").onchange = (e) => loadExample(e.target.value);
loadExample("Empty list crashes");

$("go1").onclick = async () => {
  $("e1").textContent = "";
  if (!$("source").value.trim() || !$("expected").value.trim()) {
    $("e1").textContent = "Add the code and what it should do.";
    return;
  }
  busy($("go1"), "Writing a test...", true);
  try {
    const r = await post("/investigate", {
      source: $("source").value,
      error_output: $("error").value,
      expected_behavior: $("expected").value,
    });
    if (r.ok === false) throw new Error(r.error || "The AI step failed. Try again.");
    const d = r.data || r;
    $("diag").textContent = d.diagnosis || "";
    $("test").value = d.reproduction_test || "";
    show(2);
  } catch (e) {
    $("e1").textContent = e.message;
  } finally {
    busy($("go1"), "", false);
  }
};

$("back").onclick = () => show(1);
$("again").onclick = () => { document.body.dataset.status = ""; show(1); };

$("go2").onclick = async () => {
  $("e2").textContent = "";
  if (!$("test").value.trim()) { $("e2").textContent = "The test cannot be empty."; return; }
  const t0 = Date.now();
  const tick = setInterval(() => { $("go2").textContent = "Running checks... " + Math.floor((Date.now() - t0) / 1000) + "s"; }, 500);
  busy($("go2"), "Running checks...", true);
  try {
    const r = await post("/repair", {
      source: $("source").value,
      approved_test: $("test").value,
      error_output: $("error").value,
      regression_tests: $("reg").value,
    });
    lastReport = { created: new Date().toISOString(), source: $("source").value, approved_test: $("test").value, regression_tests: $("reg").value, result: r };
    render(r);
    show(3);
  } catch (e) {
    $("e2").textContent = e.message;
  } finally {
    clearInterval(tick);
    busy($("go2"), "", false);
  }
};

function chipRow(a, host) {
  host.textContent = "";
  const idx = STAGES.indexOf(a.stage);
  STAGES.forEach((s, i) => {
    let st = "";
    if (a.status === "VERIFIED") st = "pass";
    else if (idx === -1) st = "";
    else if (i < idx) st = "pass";
    else if (i === idx) st = a.status === "FAILED" ? "fail" : "warn";
    const c = el("span", "chip " + st);
    c.append(el("i"), el("span", "", LABELS[s]));
    host.append(c);
  });
}

function diffBlock(text) {
  const pre = el("pre", "code");
  text.split("\n").forEach((line) => pre.append(el("span", "ln", line || " ")));
  return pre;
}

function outputText(d) {
  if (!d) return "No output.";
  if (typeof d.output === "string" && d.output.trim()) return d.output;
  if (d.reproduction && typeof d.reproduction.output === "string") return d.reproduction.output;
  if (d.error) return d.error;
  return JSON.stringify(d, null, 2);
}

function render(r) {
  const attempts = r.attempts || [];
  const last = attempts[attempts.length - 1] || { status: r.status || "INCONCLUSIVE", stage: "", message: "", details: null };
  const status = r.status || last.status || "INCONCLUSIVE";
  document.body.dataset.status = status;
  $("vword").textContent = status === "VERIFIED" ? "Verified" : status === "FAILED" ? "Failed" : "Inconclusive";
  let msg = MEANING[status] || "";
  if (status === "FAILED") msg = attempts.length + (attempts.length === 1 ? " fix was" : " fixes were") + " tried. " + msg;
  $("vmsg").textContent = msg;
  chipRow(last, $("vchips"));

  $("patch").textContent = "";
  $("patch").append(last.patch ? diffBlock(last.patch) : el("span", "", "No patch was produced."));
  $("out").textContent = last.message ? last.message + "\n\n" + outputText(last.details) : outputText(last.details);
  $("copy").hidden = !last.patch;
  $("copy").textContent = "Copy";

  const box = $("attempts");
  box.textContent = "";
  attempts.forEach((a) => {
    const d = el("details", "att");
    if (attempts.length === 1) d.open = true;
    const s = el("summary");
    s.append(el("span", "", "Attempt " + a.attempt + " (" + (LABELS[a.stage] || a.stage || "unknown") + ")"), el("span", "pill " + a.status, a.status));
    d.append(s, el("p", "note", a.message || ""));
    if (a.patch) d.append(diffBlock(a.patch));
    d.append(Object.assign(el("pre", "code"), { textContent: outputText(a.details) }));
    box.append(d);
  });
}

$("copy").onclick = async () => {
  const last = (lastReport && lastReport.result.attempts || []).slice(-1)[0];
  if (!last || !last.patch) return;
  try { await navigator.clipboard.writeText(last.patch); $("copy").textContent = "Copied"; }
  catch { $("copy").textContent = "Copy failed"; }
};

$("dl").onclick = () => {
  if (!lastReport) return;
  const a = el("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(lastReport, null, 2)], { type: "application/json" }));
  a.download = "bugtrace-report.json";
  a.click();
  URL.revokeObjectURL(a.href);
};
