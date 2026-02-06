const API = "http://127.0.0.1:8000";

document.querySelector("#gen").addEventListener("click", async () => {
  const resume_md = document.querySelector("#resume").value.trim();
  const jd_text = document.querySelector("#jd").value.trim();
  const style = document.querySelector("#style").value;

  if (!resume_md || !jd_text) {
    alert("Paste both resume and job description.");
    return;
  }

  const btn = document.querySelector("#gen");
  btn.disabled = true;
  btn.textContent = "Generating...";

  try {
    const res = await fetch(`${API}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_md, jd_text, style })
    });

    const data = await res.json();
    if (!res.ok) {
      alert(data.detail || "Generate failed");
      return;
    }

    document.querySelector("#out").value = data.md;
  } catch (e) {
    alert("Backend not running or blocked by CORS.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Generate";
  }
});

document.querySelector("#pdf").addEventListener("click", async () => {
  const md_text = document.querySelector("#out").value.trim();
  if (!md_text) {
    alert("Generate a cover letter first.");
    return;
  }

  const res = await fetch(`${API}/api/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ md_text })
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    alert(data.detail || "PDF failed");
    return;
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "coverletter.pdf";
  a.click();

  URL.revokeObjectURL(url);
});