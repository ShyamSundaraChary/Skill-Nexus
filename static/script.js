// Initialize animations
AOS.init({
  duration: 800,
  once: true,
  easing: "ease-out-quad",
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
  const percent = parseFloat(element.textContent);
  element.style.setProperty("--match-percent", `${percent}%`);
});

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("uploadForm");
  const resumeInput = document.getElementById("resume");
  const analyzeButton = document.getElementById("analyzeButton");
  const loadingOverlay = document.getElementById("loadingOverlay");
  const dropZone = document.getElementById("dropZone");

  // Drag & Drop Handling
  dropZone.addEventListener("click", () => resumeInput.click());

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
    resumeInput.files = e.dataTransfer.files;
    const file = resumeInput.files[0];
    if (file.size > 5 * 1024 * 1024) {
      alert("File size should be less than 5MB.");
      return;
    }
    alert(`File "${file.name}" uploaded successfully.`);
  });

  // Form Submission Handling
  form.addEventListener("submit", (event) => {
    if (!resumeInput.files || resumeInput.files.length === 0) {
      event.preventDefault();
      alert("Please upload your resume before analyzing jobs.");
      return;
    }

    // Show loading overlay
    loadingOverlay.classList.remove("d-none");

    // Disable the button to prevent multiple submissions
    analyzeButton.disabled = true;
  });
});

