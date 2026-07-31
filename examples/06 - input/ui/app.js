document.querySelector('#input-form').addEventListener('submit', async event => {
  event.preventDefault();
  const input = document.querySelector('#value');
  document.querySelector('#result').textContent = await glue.handle_input(input.value)();
  input.value = '';
  input.focus();
});
