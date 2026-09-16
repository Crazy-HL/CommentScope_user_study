import axios from "axios";

const baseURL = (process.env.VUE_APP_API_BASE_URL || "").replace(/\/$/, "");
const http = axios.create({ baseURL, timeout: 15000 });

function unwrap(request) {
  return request.then(response => response.data).catch(error => {
    const message = error.response?.data?.message || error.response?.data?.error || "网络请求失败，请稍后重试。";
    const wrapped = new Error(message);
    wrapped.code = error.response?.data?.error;
    wrapped.status = error.response?.status;
    throw wrapped;
  });
}

export function createEventId(prefix = "event") {
  if (globalThis.crypto?.randomUUID) return `${prefix}-${globalThis.crypto.randomUUID()}`;
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export const experimentApi = {
  listParticipants(clientInstanceId) {
    return unwrap(http.get("/api/participants", {
      params: { client_instance_id: clientInstanceId }
    }));
  },
  startSession(participantId, clientInstanceId) {
    return unwrap(http.post("/api/sessions", {
      participant_id: participantId,
      client_instance_id: clientInstanceId
    }));
  },
  getSession(sessionId) {
    return unwrap(http.get(`/api/sessions/${sessionId}`));
  },
  advance(sessionId, stage, articleOrder = 0) {
    return unwrap(http.post(`/api/sessions/${sessionId}`, { stage, article_order: articleOrder }));
  },
  logEvent(sessionId, articleId, eventType, payload = {}, occurredAt = Date.now(), eventId = createEventId(eventType)) {
    return unwrap(http.post(`/api/sessions/${sessionId}/events`, {
      article_id: articleId,
      event_type: eventType,
      payload,
      occurred_at: occurredAt,
      event_id: eventId
    }));
  },
  finishReading(sessionId, data) {
    return unwrap(http.post(`/api/sessions/${sessionId}/reading`, data));
  },
  submitResponse(sessionId, data) {
    return unwrap(http.post(`/api/sessions/${sessionId}/responses`, data));
  },
  submitWorkload(sessionId, articleOrder, values) {
    return unwrap(http.post(`/api/sessions/${sessionId}/workload`, { article_order: articleOrder, values }));
  },
  submitPreference(sessionId, ranking, preferredCondition, reason) {
    return unwrap(http.post(`/api/sessions/${sessionId}/preference`, {
      ranking,
      preferred_condition: preferredCondition,
      reason
    }));
  },
  submitInterview(sessionId, answers, startedAt) {
    return unwrap(http.post(`/api/sessions/${sessionId}/interview`, {
      answers,
      started_at: startedAt
    }));
  }
};

export default experimentApi;
