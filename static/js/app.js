/* Small progressive enhancements; every form remains usable without JavaScript. */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });
  document.querySelectorAll("[data-submit-once]").forEach((form) => {
    form.addEventListener("submit", () => {
      const button = form.querySelector("button[type=submit]");
      if (button) button.disabled = true;
    });
  });
});
