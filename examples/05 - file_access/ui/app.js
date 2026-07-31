document.querySelector('#picker-form').addEventListener('submit', async event => {
  event.preventDefault();
  const folder = document.querySelector('#folder').value;
  document.querySelector('#file-name').textContent = await glue.pick_file(folder)();
});
