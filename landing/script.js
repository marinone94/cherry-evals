/* ============================================================
   Cherry Evals — Landing Page Script
   Scroll animations + smooth scroll + copy button
   ============================================================ */

(function () {
  "use strict";

  /* --- Smooth scroll for anchor links -------------------- */

  document.addEventListener("click", function (e) {
    const link = e.target.closest('a[href^="#"]');
    if (!link) return;

    const id = link.getAttribute("href").slice(1);
    const target = document.getElementById(id);
    if (!target) return;

    e.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });

    // update URL without jump
    history.pushState(null, "", "#" + id);
  });

  /* --- Intersection Observer for fade-in elements -------- */

  const observerOptions = {
    threshold: 0.12,
    rootMargin: "0px 0px -40px 0px",
  };

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        // Once visible, stop observing — no re-animation on scroll back
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Observe all elements with the fade-in class
  document.querySelectorAll(".fade-in").forEach(function (el) {
    observer.observe(el);
  });

  /* --- Copy button for code block ------------------------ */

  const copyBtn = document.getElementById("copy-code");
  const codeEl = document.getElementById("quickstart-code");

  if (copyBtn && codeEl) {
    copyBtn.addEventListener("click", function () {
      const text = codeEl.textContent;

      navigator.clipboard.writeText(text).then(
        function () {
          copyBtn.textContent = "Copied!";
          copyBtn.classList.add("copied");
          setTimeout(function () {
            copyBtn.textContent = "Copy";
            copyBtn.classList.remove("copied");
          }, 2000);
        },
        function () {
          // Fallback for older browsers
          const area = document.createElement("textarea");
          area.value = text;
          area.style.position = "fixed";
          area.style.opacity = "0";
          document.body.appendChild(area);
          area.select();
          document.execCommand("copy");
          document.body.removeChild(area);

          copyBtn.textContent = "Copied!";
          copyBtn.classList.add("copied");
          setTimeout(function () {
            copyBtn.textContent = "Copy";
            copyBtn.classList.remove("copied");
          }, 2000);
        }
      );
    });
  }

  /* --- Sticky nav shadow on scroll ----------------------- */

  const nav = document.querySelector(".nav");
  if (nav) {
    window.addEventListener(
      "scroll",
      function () {
        if (window.scrollY > 8) {
          nav.style.boxShadow = "0 1px 0 rgba(255,255,255,0.04), 0 4px 20px rgba(0,0,0,0.4)";
        } else {
          nav.style.boxShadow = "none";
        }
      },
      { passive: true }
    );
  }
})();
