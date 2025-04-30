// Initialize animations
AOS.init({
  duration: 800,
  once: true,
  easing: "ease-out-quad",
});

// Update match percentage indicator
document.querySelectorAll(".score-circle").forEach((element) => {
  const percentValue = element.querySelector(".percent-value");
  if (percentValue) {
    const percent = parseFloat(percentValue.textContent);
    element.style.setProperty("--match-percent", `${percent}%`);

    // Add subtle animation
    if (percent > 0) {
      setTimeout(() => {
        element.classList.add("animated");
      }, 300);
    }
  }
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

    card.addEventListener("mouseleave", () => {
      // Reset the glow position when mouse leaves
      card.style.setProperty("--mouse-x", "20%");
      card.style.setProperty("--mouse-y", "20%");
    });
  });

  // Update match percentage indicator
  document.querySelectorAll(".score-circle").forEach((element) => {
    const percentValue = element.querySelector(".percent-value");
    if (percentValue) {
      const percent = parseFloat(percentValue.textContent);
      element.style.setProperty("--match-percent", `${percent}%`);

      // Add subtle animation
      if (percent > 0) {
        setTimeout(() => {
          element.classList.add("animated");
        }, 300);
      }
    }
  });

  // Legacy support for the old method
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

  // Job Filtering System
  const filterPills = document.querySelectorAll(".filter-pill");
  const jobCards = document.querySelectorAll(".job-card");
  const jobGrid = document.querySelector(".job-grid");

  // Function to reset job grid to standard layout
  function resetJobGrid() {
    if (jobGrid) {
      // Remove sort-enabled class to restore grid layout
      jobGrid.classList.remove("sort-enabled");

      // Reset all card styles
      jobCards.forEach((card) => {
        card.style.order = "";
        card.style.width = "";
        card.style.maxWidth = "";
      });
    }
  }

  // Function to show "No jobs found" message
  function showNoJobsMessage(filter) {
    // Get the appropriate message element
    let messageElement;
    if (filter === "bookmarked") {
      messageElement = document.querySelector(".no-bookmarks-message");
    } else {
      messageElement = document.querySelector(".no-jobs-message");
    }

    // Hide the other message if it's visible
    const otherMessage =
      filter === "bookmarked"
        ? document.querySelector(".no-jobs-message")
        : document.querySelector(".no-bookmarks-message");

    if (otherMessage) {
      otherMessage.style.display = "none";
    }

    // Show the appropriate message
    if (messageElement) {
      messageElement.style.display = "block";
    }
  }

  // Function to hide all "No jobs found" messages
  function hideNoJobsMessages() {
    // Hide both message types
    const messages = document.querySelectorAll(
      ".no-jobs-message, .no-bookmarks-message"
    );
    messages.forEach((msg) => {
      msg.style.display = "none";
    });
  }

  // Show More Jobs Functionality
  const showMoreBtn = document.getElementById("showMoreJobs");
  const initialHiddenJobs = document.querySelectorAll(".hidden-job");

  if (showMoreBtn && initialHiddenJobs.length > 0) {
    // Set initial count of visible and hidden jobs
    let visibleJobCount = 10;
    const totalJobs = visibleJobCount + initialHiddenJobs.length;

    // Update button text to show counts
    showMoreBtn.innerHTML = `<i class="fas fa-plus-circle me-2"></i>Show More Jobs (${visibleJobCount}/${totalJobs})`;

    showMoreBtn.addEventListener("click", function () {
      // Get the current hidden jobs (as they may have changed due to filtering)
      const currentHiddenJobs = document.querySelectorAll(".hidden-job");

      // Show next batch of hidden jobs (up to 10 more)
      const jobsToShow = Array.from(currentHiddenJobs).slice(0, 10);
      let newlyShown = 0;

      jobsToShow.forEach((job) => {
        job.classList.remove("hidden-job");

        // Animate the newly visible jobs
        job.style.opacity = "0";
        job.style.transform = "translateY(20px)";

        setTimeout(() => {
          job.style.opacity = "1";
          job.style.transform = "translateY(0)";
        }, 50 * newlyShown);

        newlyShown++;
      });

      // Update visible job count
      visibleJobCount += newlyShown;

      // Update button text
      const remainingHiddenJobs =
        document.querySelectorAll(".hidden-job").length;
      showMoreBtn.innerHTML = `<i class="fas fa-plus-circle me-2"></i>Show More Jobs (${visibleJobCount}/${totalJobs})`;

      // Hide button if all jobs are shown
      if (remainingHiddenJobs === 0) {
        showMoreBtn.style.display = "none";
      }
    });
  }

  // Handle filter buttons with show more functionality
  filterPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      // Update active state
      filterPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");

      const filter = pill.getAttribute("data-filter");
      let jobsArray = Array.from(jobCards);
      let visibleJobCount = 0;

      // Reset grid for proper layout
      resetJobGrid();

      // Hide the show more button when filters are applied
      if (showMoreBtn) {
        showMoreBtn.style.display = "none";
      }

      // Apply filtering logic
      if (filter === "recent" || filter === "match-high") {
        // Add temporary class to job grid for sorting
        if (jobGrid) {
          jobGrid.classList.add("sort-enabled");
        }

        // Sort jobs appropriately
        if (filter === "recent") {
          // Sort by recency
          jobsArray.sort((a, b) => {
            const daysA = parseInt(a.getAttribute("data-days")) || 999;
            const daysB = parseInt(b.getAttribute("data-days")) || 999;
            return daysA - daysB;
          });
        } else if (filter === "match-high") {
          // Sort by match score
          jobsArray.sort((a, b) => {
            const scoreA = parseFloat(a.getAttribute("data-match-score")) || 0;
            const scoreB = parseFloat(b.getAttribute("data-match-score")) || 0;
            return scoreB - scoreA;
          });
        }

        // Show sorted jobs with staggered animation
        jobsArray.forEach((card, index) => {
          let shouldShow = true;

          // For match-high, optionally filter out low matches
          if (filter === "match-high") {
            const score =
              parseFloat(card.getAttribute("data-match-score")) || 0;
            shouldShow = score >= 20;
          }

          if (shouldShow) {
            // Remove hidden-job class when filtering
            card.classList.remove("hidden-job");
            card.style.display = "flex";
            card.style.order = index;
            visibleJobCount++;

            // Staggered animation
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
      } else {
        // Standard filtering (all, source-specific)
        jobCards.forEach((card) => {
          // Default is to show the card
          let shouldShow = true;

          // Apply specific filters
          if (filter === "all") {
            // For "all" filter, only show first 10 and restore hidden-job class for others
            jobCards.forEach((card) => {
              const index = parseInt(card.getAttribute("data-index")) || 0;
              if (index > 10) {
                card.classList.add("hidden-job");
              } else {
                card.classList.remove("hidden-job");
              }
            });

            // Set shouldShow based on index for current card
            const index = parseInt(card.getAttribute("data-index")) || 0;
            shouldShow = index <= 10;

            // Show the show more button again for "all" filter if needed
            if (showMoreBtn) {
              const currentHiddenJobs =
                document.querySelectorAll(".hidden-job");
              if (currentHiddenJobs.length > 0) {
                showMoreBtn.style.display = "block";
                showMoreBtn.innerHTML = `<i class="fas fa-plus-circle me-2"></i>Show More Jobs (10/${jobCards.length})`;
              }
            }
          } else if (filter.startsWith("source-")) {
            // Filter by source - show all matching jobs
            const source = filter.replace("source-", "");
            shouldShow = card.getAttribute("data-job-source") === source;
            // Remove hidden-job class when filtering by source
            card.classList.remove("hidden-job");
          }

          // Apply visibility with animation
          if (shouldShow) {
            card.style.display = "flex";
            visibleJobCount++;
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
      }

      // Show or hide "No jobs found" message
      if (visibleJobCount === 0) {
        showNoJobsMessage(filter);
      } else {
        hideNoJobsMessages();
      }
    });
  });
});
