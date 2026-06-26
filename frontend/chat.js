const CHAT_API = "http://localhost:8000/chat";

export async function streamChat(question, onToken, onDone, onError) {
  let response;
  try {
    response = await fetch(CHAT_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
  } catch {
    onError("Network error — is the API running? (task dev)");
    return;
  }

  if (!response.ok) {
    onError(`Server error ${response.status}`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload = line.slice(6).trim();
      if (payload === "[DONE]") { onDone(); return; }
      try {
        const { delta } = JSON.parse(payload);
        if (delta) onToken(delta);
      } catch { /* malformed line */ }
    }
  }
  onDone();
}
