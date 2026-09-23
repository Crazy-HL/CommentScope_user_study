import axios from "axios";

const baseURL = (process.env.VUE_APP_API_BASE_URL || "").replace(/\/$/, "");
const http = axios.create({ baseURL, timeout: 15000, withCredentials: true });

function unwrap(request) {
  return request.then(response => response.data).catch(error => {
    const message = error.response?.data?.message || error.response?.data?.error || "网络请求失败，请稍后重试。";
    const wrapped = new Error(message);
    wrapped.code = error.response?.data?.error;
    wrapped.status = error.response?.status;
    throw wrapped;
  });
}

function query(filters = {}) {
  return Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
}

const adminApi = {
  login(username, password) {
    return unwrap(http.post("api/admin/login", { username, password }));
  },
  me() {
    return unwrap(http.get("api/admin/me"));
  },
  logout() {
    return unwrap(http.post("api/admin/logout", {}));
  },
  summary(filters) {
    return unwrap(http.get("api/admin/summary", { params: query(filters) }));
  },
  analysis(filters) {
    return unwrap(http.get("api/admin/analysis", { params: query(filters) }));
  },
  dataQuality(filters) {
    return unwrap(http.get("api/admin/data-quality", { params: query(filters) }));
  },
  exportData(format = "csv", dataset = "analysis") {
    const params = new URLSearchParams({ format, dataset });
    return unwrap(http.get(`api/admin/export?${params.toString()}`, { responseType: "blob" }));
  },
  resetParticipant(participantId) {
    return unwrap(http.post(`api/admin/reset/${encodeURIComponent(participantId)}`, {}));
  }
};

export default adminApi;
