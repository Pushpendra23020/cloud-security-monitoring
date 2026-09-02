import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api/v1",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

let accessToken = null;
let refreshPromise = null;

export const setAccessToken = (token) => {
  accessToken = token || null;
};

export const refreshAccessToken = async () => {
  if (!refreshPromise) {
    refreshPromise = axios.post(
      "/api/v1/auth/refresh",
      null,
      { withCredentials: true }
    ).then((response) => {
      setAccessToken(response.data.access_token);
      return response.data;
    }).finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
};

apiClient.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest = error.config;
    const path = originalRequest?.url || "";
    const canRefresh = !path.includes("/auth/login")
      && !path.includes("/auth/refresh")
      && !path.includes("/auth/logout");
    if (error.response?.status === 401 && !originalRequest?._retry && canRefresh) {
      originalRequest._retry = true;
      try {
        const token = await refreshAccessToken();
        originalRequest.headers.Authorization = `Bearer ${token.access_token}`;
        return apiClient(originalRequest);
      } catch {
        setAccessToken(null);
        window.dispatchEvent(new Event("cloud-sentinel-auth-expired"));
      }
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
