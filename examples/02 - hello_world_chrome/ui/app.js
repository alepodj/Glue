const report = message => {
  console.log(message);
  const item = document.createElement('li');
  item.textContent = message;
  document.querySelector('#log').appendChild(item);
};

glue.expose(say_hello_js);
function say_hello_js(source) {
  report(`JavaScript received: Hello from ${source}`);
}

say_hello_js('JavaScript World!');
glue.say_hello_py('JavaScript World!');
