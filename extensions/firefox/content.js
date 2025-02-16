function showModal(content) {
  fetch(browser.runtime.getURL("modal.html"))
    .then(response => response.text())
    .then(html => {
      const modal = document.createElement("div");
      modal.innerHTML = html;
      document.body.appendChild(modal);

      const modalElement = document.getElementById("modal");
      const modalBody = document.getElementById("modal-body");
      const modalClose = document.getElementById("modal-close");

      modalBody.innerHTML = content;
      modalElement.style.display = "block";

      modalClose.addEventListener("click", () => {
        document.body.removeChild(modal);
      });

      modalElement.addEventListener('click', function(event) {
        console.log(event.target);
        if (event.target === modalElement) {
          modalElement.style.display = 'none';
        }
      });

      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = browser.runtime.getURL("modal.css");
      document.head.appendChild(link);
    });
}

browser.runtime.onMessage.addListener((message) => {
  if (message.action === "showPopup") {
    showPopup(message.content, message.x, message.y);
  } else if (message.action === "showModal") {
    showModal(message.content);
  }
});
