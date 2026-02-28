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

// Discourage right-click on result area (not real security)
document.addEventListener("contextmenu", (e) => {
  const res = document.getElementById("resultSection");
  if (res && res.contains(e.target)) e.preventDefault();
});
