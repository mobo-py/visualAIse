// anim.js
window.addEventListener("load", () => {
    const items = document.querySelectorAll(".fade-up");
    items.forEach((el, i) => {
      el.style.animationDelay = `${i * 0.1}s`; // stagger by 100ms
      el.classList.add("fade-up");
    });
  });
  