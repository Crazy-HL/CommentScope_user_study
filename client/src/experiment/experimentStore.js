import { reactive } from "vue";
import experimentApi from "./experimentApi";

const CLIENT_KEY = "commentscope.client-instance";
const SESSION_KEY = "commentscope.session-id";

function persistentId() {
  let value = localStorage.getItem(CLIENT_KEY);
  if (!value) {
    value = globalThis.crypto?.randomUUID?.() || `client-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    localStorage.setItem(CLIENT_KEY, value);
  }
  return value;
}

export function createExperimentStore() {
  const state = reactive({
    loading: false,
    error: "",
    clientInstanceId: persistentId(),
    session: null,
    articles: [],
    responses: []
  });

  function hydrate(payload) {
    state.session = payload.session;
    state.articles = payload.articles || [];
    state.responses = payload.progress?.responses || [];
    if (state.session?.session_id) localStorage.setItem(SESSION_KEY, state.session.session_id);
    return payload;
  }

  async function resumeSaved() {
    const sessionId = localStorage.getItem(SESSION_KEY);
    if (!sessionId) return null;
    try {
      state.loading = true;
      return hydrate(await experimentApi.getSession(sessionId));
    } catch (error) {
      localStorage.removeItem(SESSION_KEY);
      state.error = error.message;
      return null;
    } finally {
      state.loading = false;
    }
  }

  async function start(participantId) {
    state.loading = true;
    state.error = "";
    try {
      return hydrate(await experimentApi.startSession(participantId, state.clientInstanceId));
    } finally {
      state.loading = false;
    }
  }

  function clearLocalSession() {
    localStorage.removeItem(SESSION_KEY);
    state.session = null;
    state.articles = [];
    state.responses = [];
  }

  return { state, hydrate, resumeSaved, start, clearLocalSession };
}
