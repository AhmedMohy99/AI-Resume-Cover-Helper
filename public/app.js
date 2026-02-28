function copyResult() {
  const el = document.getElementById("resultBox");
  if (!el) return;
  navigator.clipboard.writeText(el.innerText);
  alert("Copied!");
}

function toggleFocus() {
  const sec = document.getElementById("resultSection");
  if (!sec) return;
  sec.classList.toggle("focus");
}

window.copyResult = copyResult;
window.toggleFocus = toggleFocus;

// Light “discourage” actions (NOT secure)
document.addEventListener("contextmenu", (e) => {
  // disable right click only inside result
  const res = document.getElementById("resultSection");
  if (res && res.contains(e.target)) e.preventDefault();
});
