const loadedAt = new Date().toLocaleTimeString();
const message = `app.js loaded at ${loadedAt}`;

console.log(message);
document.querySelector('#cache-proof').textContent = message;
