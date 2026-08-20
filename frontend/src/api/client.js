import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api/v1",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.response.use(
  (response) => response,

  (error) => {
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
