glue.expose(say_hello_js);
function say_hello_js(source) {
  console.log(`Hello from ${source}`);
}

glue.expose(js_random);
function js_random() {
  return Math.random();
}

const result = document.querySelector('#result');
if (result) {
  glue.py_random()(value => {
    result.textContent = `Python returned ${value}`;
  });
  say_hello_js('JavaScript World!');
  glue.say_hello_py('JavaScript World!');
}
