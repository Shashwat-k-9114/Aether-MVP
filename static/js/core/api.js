/**
 * Aether — API client
 * ------------------------------------------------------------------
 * One place that knows how to talk to the Flask backend. Every page
 * script calls through this object instead of using fetch() directly,
 * so error handling and JSON parsing stay consistent everywhere.
 */

const Api = (() => {
  async function request(path, options = {}) {
    const res = await fetch(path, {
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      ...options,
    });

    let data = null;
    try {
      data = await res.json();
    } catch (err) {
      data = null;
    }

    if (!res.ok) {
      const message = (data && data.error) || 'Something went wrong. Please try again.';
      throw new ApiError(message, res.status);
    }
    return data;
  }

  const get = (path) => request(path, { method: 'GET' });
  const post = (path, body) => request(path, { method: 'POST', body: JSON.stringify(body || {}) });

  return {
    // Users / onboarding
    createUser: (payload) => post('/api/users', payload),
    getUser: (id) => get(`/api/users/${id}`),
    submitBirthDetails: (id, payload) => post(`/api/users/${id}/birth-details`, payload),
    getJanampatri: (id) => get(`/api/users/${id}/janampatri`),
    getDashboard: (id) => get(`/api/users/${id}/dashboard`),

    // Chat
    startChat: (userId) => post('/api/chat/start', { user_id: userId }),
    sendMessage: (userId, sessionId, content) =>
      post('/api/chat/message', { user_id: userId, session_id: sessionId, content }),
    getChatHistory: (sessionId) => get(`/api/chat/${sessionId}/history`),

    // Recommendations
    generateRecommendations: (userId, sessionId) =>
      post('/api/recommendations/generate', { user_id: userId, session_id: sessionId }),
    getUserRecommendations: (userId) => get(`/api/recommendations/user/${userId}`),
    toggleSaveRecommendation: (recId) => post(`/api/recommendations/${recId}/save`),

    // Experts
    listExperts: (modality) => get(`/api/experts${modality ? `?modality=${encodeURIComponent(modality)}` : ''}`),
    getExpert: (id) => get(`/api/experts/${id}`),
    bookExpert: (id, userId, sessionDatetime) =>
      post(`/api/experts/${id}/book`, { user_id: userId, session_datetime: sessionDatetime }),
    getUserBookings: (userId) => get(`/api/experts/bookings/${userId}`),

    // Journal
    createJournalEntry: (userId, content, mood) => post('/api/journal', { user_id: userId, content, mood }),
    getJournalEntries: (userId) => get(`/api/journal/user/${userId}`),
  };
})();

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}