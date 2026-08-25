import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api/v1",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("cloud-sentinel-token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,

  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("cloud-sentinel-token");
      window.dispatchEvent(new Event("cloud-sentinel-auth-expired"));
    }
    console.error(
      "[Cloud Sentinel API]",
      error.response?.status || "NETWORK",
      error.config?.url,
      error.response?.data || error.message
    );

    return Promise.reject(error);
  }
);

export default apiClient;
