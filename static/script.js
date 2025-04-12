// Initialize animations
AOS.init({
  duration: 800,
  once: true,
  easing: "ease-out-quad",
});

// Drag & Drop Handling
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("resume");

dropZone.addEventListener("click", () => fileInput.click());

["dragover", "dragenter"].forEach((event) => {
  dropZone.addEventListener(event, (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
});

["dragleave", "dragend", "drop"].forEach((event) => {
  dropZone.addEventListener(event, () => {
    dropZone.classList.remove("dragover");
  });
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  fileInput.files = e.dataTransfer.files;
});

// Dynamic card hover effects
document.querySelectorAll(".job-card").forEach((card) => {
  card.addEventListener("mousemove", (e) => {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    card.style.setProperty("--mouse-x", `${x}px`);
    card.style.setProperty("--mouse-y", `${y}px`);
  });
});
// Update match percentage indicator
document.querySelectorAll(".match-percent").forEach((element) => {
  const percent = parseInt(element.textContent);
  element.style.setProperty("--match-percent", `${percent}%`);
});
