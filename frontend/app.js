import { streamChat } from "./chat.js";

const form = document.getElementById("chat-form");
const input = document.getElementById("question-input");
const submitBtn = document.getElementById("submit-btn");
const messagesEl = document.getElementById("chat-messages");

function appendMessage(text, role) {
  const el = document.createElement("article");
  el.className = `message ${role}`;
  el.textContent = text;
  messagesEl.appendChild(el);
  el.scrollIntoView({ behavior: "smooth", block: "end" });
  return el;
}

function setLoading(loading) {
  submitBtn.disabled = loading;
  input.disabled = loading;
  submitBtn.setAttribute("aria-busy", loading ? "true" : "false");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question) return;

  input.value = "";
  appendMessage(question, "user");
  setLoading(true);

  const assistantEl = appendMessage("", "assistant streaming");

  await streamChat(
    question,
    (token) => {
      assistantEl.textContent += token;
      assistantEl.scrollIntoView({ behavior: "smooth", block: "end" });
    },
    () => { assistantEl.classList.remove("streaming"); setLoading(false); input.focus(); },
    (errMsg) => { assistantEl.remove(); appendMessage(errMsg, "error"); setLoading(false); input.focus(); },
  );
});
