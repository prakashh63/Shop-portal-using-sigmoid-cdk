async function call(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  document.getElementById("out").textContent =
    method + " " + path + " -> " + res.status + "\n" + JSON.stringify(await res.json(), null, 2);
}
