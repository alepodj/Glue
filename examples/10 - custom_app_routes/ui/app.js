document.querySelector('#load-route').addEventListener('click', async () => {
  const response = await fetch('/custom');
  const data = await response.json();
  document.querySelector('#result').textContent = data.message;
});
