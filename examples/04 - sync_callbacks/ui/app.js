glue.expose(js_random);
function js_random() {
  return Math.random();
}

async function run() {
  const value = await glue.py_random()();
  document.querySelector('#result').textContent = `Python returned ${value}`;
  console.log('Got this from Python:', value);
}

run();
