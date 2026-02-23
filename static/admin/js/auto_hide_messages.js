document.addEventListener("DOMContentLoaded", () => {
  // 🔒 Run ONLY on Add Blog page
  if (!window.location.pathname.endsWith("/add/")) return;

  setTimeout(() => {
    document
      .querySelectorAll(".messagelist li.error")
      .forEach(msg => {
        msg.style.transition = "opacity 0.5s ease";
        msg.style.opacity = "0";
        setTimeout(() => msg.remove(), 500);
      });
  }, 5000);
});