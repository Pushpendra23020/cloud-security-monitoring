import apiClient from "./client";

export async function getEventQueueStatus() {
  const response = await apiClient.get("/events/queue");
  return response.data;
}

export async function getDeadLetterEvents(params = {}) {
  const response = await apiClient.get("/events/queue/dead-letters", {
    params,
  });
  return response.data;
}

export async function replayDeadLetterEvent(recordId) {
  const response = await apiClient.post(
    `/events/queue/${recordId}/replay`
  );
  return response.data;
}
