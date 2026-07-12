/**
 * Aether — Chat
 */
document.addEventListener('DOMContentLoaded', async () => {
  const userId = AetherSession.requireUser();
  if (!userId) return;

  const messagesEl = document.getElementById('chat-messages');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const statusEl = document.getElementById('chat-status');
  const topicPill = document.getElementById('chat-topic-pill');
  const readyBanner = document.getElementById('chat-ready-banner');

  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
  });

  async function bootstrap() {
    let sessionId = AetherSession.getChatSessionId();

    if (sessionId) {
      try {
        const history = await Api.getChatHistory(sessionId);
        if (history.length) {
          history.forEach((m) => appendMessage(m.role, m.content, m.created_at));
          scrollToBottom();
          return;
        }
      } catch (err) {
        // fall through to starting a new session
      }
    }

    const result = await Api.startChat(userId);
    AetherSession.setChatSessionId(result.session_id);
    appendMessage('ai', result.message.content, result.message.created_at);
    updateTopic(result.topic, result.ready_for_analysis);
  }

  function appendMessage(role, content, timestamp) {
    const el = document.createElement('div');
    el.className = `msg ${role}`;
    const avatar = role === 'ai' ? '✦' : (AetherSession.getUserName() || 'You')[0].toUpperCase();
    const rendered = role === 'ai' && typeof marked !== 'undefined'
      ? marked.parse(content)
      : `<p>${escapeHtml(content)}</p>`;

    el.innerHTML = `
      <span class="msg-avatar">${avatar}</span>
      <div class="msg-bubble">${rendered}<span class="msg-time">${formatTime(timestamp)}</span></div>
    `;
    messagesEl.appendChild(el);
  }

  function showTyping() {
    const el = document.createElement('div');
    el.className = 'msg ai msg-typing';
    el.id = 'typing-indicator';
    el.innerHTML = `<span class="msg-avatar">✦</span><div class="msg-bubble"><span></span><span></span><span></span></div>`;
    messagesEl.appendChild(el);
    scrollToBottom();
  }

  function hideTyping() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
  }

  function updateTopic(topic, readyForAnalysis) {
    topicPill.textContent = topic.replace('_', ' ');
    statusEl.textContent = readyForAnalysis ? 'Ready for your reflections' : 'Listening';
    readyBanner.hidden = !readyForAnalysis;
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function formatTime(iso) {
    if (!iso) return '';
    const d = new Date(iso.endsWith('Z') ? iso : `${iso}Z`);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const content = input.value.trim();
    if (!content) return;

    appendMessage('user', content, new Date().toISOString());
    input.value = '';
    input.style.height = 'auto';
    scrollToBottom();
    showTyping();

    try {
      const sessionId = AetherSession.getChatSessionId();
      const result = await Api.sendMessage(userId, sessionId, content);
      hideTyping();
      appendMessage('ai', result.ai_message.content, result.ai_message.created_at);
      updateTopic(result.topic, result.ready_for_analysis);
      scrollToBottom();
    } catch (err) {
      hideTyping();
      notify(err.message || 'Aether could not respond just now.', 'error');
    }
  });

  await bootstrap();
  scrollToBottom();
});