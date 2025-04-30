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
  // Initialize animations
  AOS.init({
    duration: 800,
    once: true,
    easing: "ease-out-quad",
  });

  // Dark Mode Toggle
  const themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    const body = document.body;
    const themeIcon = themeToggle.querySelector("i");

    // Check for saved theme preference or respect OS preference
    const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");
    const savedTheme = localStorage.getItem("theme");

    if (savedTheme === "dark" || (!savedTheme && prefersDarkScheme.matches)) {
      body.classList.add("dark-mode");
      themeIcon.classList.replace("fa-moon", "fa-sun");
    }

    // Theme toggle functionality
    themeToggle.addEventListener("click", () => {
      body.classList.toggle("dark-mode");

      if (body.classList.contains("dark-mode")) {
        localStorage.setItem("theme", "dark");
        themeIcon.classList.replace("fa-moon", "fa-sun");
      } else {
        localStorage.setItem("theme", "light");
        themeIcon.classList.replace("fa-sun", "fa-moon");
      }
    });
  }

  // Form handling
  const form = document.getElementById("uploadForm");
  const resumeInput = document.getElementById("resume");
  const analyzeButton = document.getElementById("analyzeButton");
  const loadingOverlay = document.getElementById("loadingOverlay");
  const dropZone = document.getElementById("dropZone");
  const locationInput = document.getElementById("location");
  const experienceSelect = document.getElementById("experience_level");

  // Load saved preferences if available
  if (locationInput && experienceSelect) {
    const savedPreferences =
      JSON.parse(localStorage.getItem("userPreferences")) || {};

    if (savedPreferences.location) {
      locationInput.value = savedPreferences.location;
    }

    if (savedPreferences.experience) {
      experienceSelect.value = savedPreferences.experience;
    }

    // Save preferences when changed
    locationInput.addEventListener("change", saveUserPreferences);
    experienceSelect.addEventListener("change", saveUserPreferences);
  }

  function saveUserPreferences() {
    const preferences = {
      location: locationInput.value,
      experience: experienceSelect.value,
    };

    localStorage.setItem("userPreferences", JSON.stringify(preferences));

    // Show feedback
    const preferenceSaved = document.createElement("div");
    preferenceSaved.className = "preference-saved";
    preferenceSaved.textContent = "Preferences saved!";

    // Remove any existing feedback messages
    const existingMsg = document.querySelector(".preference-saved");
    if (existingMsg) {
      existingMsg.remove();
    }

    // Add feedback to the page
    form.appendChild(preferenceSaved);

    // Remove message after 2 seconds
    setTimeout(() => {
      preferenceSaved.classList.add("fade-out");
      setTimeout(() => preferenceSaved.remove(), 500);
    }, 2000);
  }

  if (form) {
    // Form validation
    form.addEventListener("submit", (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      } else if (!resumeInput.files || resumeInput.files.length === 0) {
        event.preventDefault();
        alert("Please upload your resume before analyzing jobs.");
        return;
      } else {
        // Save user preferences
        saveUserPreferences();

        // Show loading overlay
        loadingOverlay.classList.remove("d-none");
        // Disable the button to prevent multiple submissions
        analyzeButton.disabled = true;
      }

      form.classList.add("was-validated");
    });
  }

  // Drag & Drop Handling
  if (dropZone && resumeInput) {
    // Click on drop zone to trigger file input
    dropZone.addEventListener("click", () => resumeInput.click());

    // Highlight drop zone on drag over
    ["dragover", "dragenter"].forEach((event) => {
      dropZone.addEventListener(event, (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
      });
    });

    // Remove highlight on drag leave
    ["dragleave", "dragend", "drop"].forEach((event) => {
      dropZone.addEventListener(event, (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
      });
    });

    // Handle dropped files
    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      resumeInput.files = e.dataTransfer.files;

      const file = resumeInput.files[0];
      if (file) {
        // Validate file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
          alert("File size should be less than 5MB.");
          resumeInput.value = "";
          return;
        }

        // Validate file type
        const validTypes = [
          "application/pdf",
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ];
        const fileExtension = file.name.split(".").pop().toLowerCase();
        const isValidType =
          validTypes.includes(file.type) ||
          ["pdf", "docx"].includes(fileExtension);

        if (!isValidType) {
          alert("Please upload a valid PDF or DOCX file.");
          resumeInput.value = "";
          return;
        }

        // Display file name
        const fileNameElement = document.createElement("div");
        fileNameElement.classList.add("selected-file", "mt-3", "text-success");
        fileNameElement.innerHTML = `<i class="fas fa-file-alt me-2"></i>${file.name}`;

        // Remove previous file name display if exists
        const previousFile = dropZone.querySelector(".selected-file");
        if (previousFile) {
          previousFile.remove();
        }

        dropZone.appendChild(fileNameElement);
      }
    });

    // Handle selected file via input
    resumeInput.addEventListener("change", () => {
      const file = resumeInput.files[0];
      if (file) {
        // Validate file size
        if (file.size > 5 * 1024 * 1024) {
          alert("File size should be less than 5MB.");
          resumeInput.value = "";
          return;
        }

        // Display file name
        const fileNameElement = document.createElement("div");
        fileNameElement.classList.add("selected-file", "mt-3", "text-success");
        fileNameElement.innerHTML = `<i class="fas fa-file-alt me-2"></i>${file.name}`;

        // Remove previous file name display if exists
        const previousFile = dropZone.querySelector(".selected-file");
        if (previousFile) {
          previousFile.remove();
        }

        dropZone.appendChild(fileNameElement);
      }
    });
  }

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
    const progressBar = element.parentNode.querySelector(".progress-bar");

    if (progressBar) {
      // Calculate the stroke dashoffset based on the percentage
      const circumference = 2 * Math.PI * 35; // 2πr where r=35
      const offset = circumference - (percent / 100) * circumference;
      progressBar.style.strokeDashoffset = offset;
    }
  });

  // Job Bookmarking System
  const bookmarkButtons = document.querySelectorAll(".btn-bookmark");

  // Load existing bookmarks from localStorage
  const bookmarkedJobs =
    JSON.parse(localStorage.getItem("bookmarkedJobs")) || [];

  // Initialize bookmark buttons
  bookmarkButtons.forEach((button) => {
    const jobId = button.getAttribute("data-job-id");
    const icon = button.querySelector("i");

    // Set initial state based on localStorage
    if (bookmarkedJobs.includes(jobId)) {
      icon.classList.replace("far", "fas");
      button.classList.add("bookmarked");
    }

    button.addEventListener("click", () => {
      // Toggle bookmark state
      if (icon.classList.contains("far")) {
        // Add bookmark
        icon.classList.replace("far", "fas");
        button.classList.add("bookmarked");

        // Send API request to save bookmark
        fetch("/api/bookmark", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ job_id: jobId }),
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              // Store in localStorage if not already there
              if (!bookmarkedJobs.includes(jobId)) {
                bookmarkedJobs.push(jobId);
                localStorage.setItem(
                  "bookmarkedJobs",
                  JSON.stringify(bookmarkedJobs)
                );
              }
            } else {
              console.error("Failed to save bookmark");
              // Revert the UI state
              icon.classList.replace("fas", "far");
              button.classList.remove("bookmarked");
            }
          })
          .catch((error) => {
            console.error("Error:", error);
            // Revert the UI state
            icon.classList.replace("fas", "far");
            button.classList.remove("bookmarked");
          });
      } else {
        // Remove bookmark
        icon.classList.replace("fas", "far");
        button.classList.remove("bookmarked");

        // Remove from localStorage
        const index = bookmarkedJobs.indexOf(jobId);
        if (index > -1) {
          bookmarkedJobs.splice(index, 1);
          localStorage.setItem(
            "bookmarkedJobs",
            JSON.stringify(bookmarkedJobs)
          );
        }
      }
    });
  });

  // Job Filtering System
  const filterPills = document.querySelectorAll(".filter-pill");
  const jobCards = document.querySelectorAll(".job-card");

  // Filter functionality
  filterPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      // Update active state
      filterPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");

      const filter = pill.getAttribute("data-filter");

      // For sorting jobs (recent or match score)
      let jobsArray = Array.from(jobCards);

      // Apply filtering logic
      if (filter === "recent") {
        // Sort jobs by recency (most recent first)
        jobsArray.sort((a, b) => {
          const daysA = parseInt(a.getAttribute("data-days")) || 999;
          const daysB = parseInt(b.getAttribute("data-days")) || 999;
          return daysA - daysB;
        });

        // Show all jobs but in sorted order
        jobsArray.forEach((card, index) => {
          card.style.display = "";
          card.style.order = index;

          // Apply animation with staggered delay
          setTimeout(() => {
            card.style.opacity = "1";
            card.style.transform = "translateY(0)";
          }, index * 50);
        });

        // Add temporary class to job grid for sorting
        const jobGrid = document.querySelector(".job-grid");
        if (jobGrid) {
          jobGrid.classList.add("sort-enabled");
          // Remove class after transition
          setTimeout(() => {
            jobGrid.classList.remove("sort-enabled");
          }, jobsArray.length * 50 + 300);
        }

        return;
      } else if (filter === "match-high") {
        // Sort jobs by match score (highest first)
        jobsArray.sort((a, b) => {
          const scoreA = parseInt(a.getAttribute("data-match-score")) || 0;
          const scoreB = parseInt(b.getAttribute("data-match-score")) || 0;
          return scoreB - scoreA;
        });

        // Show jobs with score >= 20% in sorted order
        jobsArray.forEach((card, index) => {
          const score = parseInt(card.getAttribute("data-match-score")) || 0;
          const shouldShow = score >= 20;

          card.style.order = index;

          if (shouldShow) {
            card.style.display = "";
            // Apply animation with staggered delay
            setTimeout(() => {
              card.style.opacity = "1";
              card.style.transform = "translateY(0)";
            }, index * 50);
          } else {
            card.style.opacity = "0";
            card.style.transform = "translateY(20px)";
            setTimeout(() => {
              card.style.display = "none";
            }, 300);
          }
        });

        // Add temporary class to job grid for sorting
        const jobGrid = document.querySelector(".job-grid");
        if (jobGrid) {
          jobGrid.classList.add("sort-enabled");
          // Remove class after transition
          setTimeout(() => {
            jobGrid.classList.remove("sort-enabled");
          }, jobsArray.length * 50 + 300);
        }

        return;
      }

      // For other filters (all, bookmarked, source-specific)
      jobCards.forEach((card) => {
        // Default is to show the card
        let shouldShow = true;

        // Apply specific filters
        if (filter === "all") {
          // Show all jobs
          shouldShow = true;
        } else if (filter === "bookmarked") {
          // Show only bookmarked jobs
          const jobId = card
            .querySelector(".btn-bookmark")
            .getAttribute("data-job-id");
          shouldShow = bookmarkedJobs.includes(jobId);
        } else if (filter.startsWith("source-")) {
          // Filter by source
          const source = filter.replace("source-", "");
          shouldShow = card.getAttribute("data-job-source") === source;
        }

        // Apply visibility with animation
        if (shouldShow) {
          card.style.display = "";
          setTimeout(() => {
            card.style.opacity = "1";
            card.style.transform = "translateY(0)";
          }, 10);
        } else {
          card.style.opacity = "0";
          card.style.transform = "translateY(20px)";
          setTimeout(() => {
            card.style.display = "none";
          }, 300);
        }
      });
    });
  });

  // Newsletter subscription
  const subscribeForm = document.querySelector(".subscribe-form");
  if (subscribeForm) {
    subscribeForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const emailInput = this.querySelector('input[type="email"]');
      const email = emailInput.value.trim();

      if (!email) {
        alert("Please enter your email address");
        return;
      }

      // Validate email format
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        alert("Please enter a valid email address");
        return;
      }

      // Here you would typically send this to an API
      // For now, just show success message
      const button = this.querySelector("button");
      const originalText = button.textContent;

      button.textContent = "Subscribed!";
      button.classList.add("btn-success");
      emailInput.disabled = true;

      // Reset after 3 seconds
      setTimeout(() => {
        emailInput.value = "";
        emailInput.disabled = false;
        button.textContent = originalText;
        button.classList.remove("btn-success");
      }, 3000);
    });
  }
});
