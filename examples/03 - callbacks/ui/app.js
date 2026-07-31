const report = (message, error = false) => {
  console.log(message);
  const item = document.createElement('li');
  item.textContent = message;
  item.classList.toggle('error', error);
  document.querySelector('#log').appendChild(item);
};

glue.expose(js_random);
function js_random() {
  return Math.random();
}

glue.expose(js_with_error);
function js_with_error() {
  throw new Error('Deliberate JavaScript error');
}

glue.py_random()(value => report(`Python random callback: ${value}`));
glue.py_random()(value => report(`Inline Python callback: ${value}`));
glue.py_exception(false)()
  .then(result => report(`Python promise resolved: ${result}`))
  .catch(error => report(`Unexpected error: ${error.errorText}`, true));
glue.py_exception(true)()
  .then(() => report('The deliberate exception unexpectedly resolved', true))
  .catch(error => report(`Python promise rejected: ${error.errorText}`, true));
