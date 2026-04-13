function joinUrl(baseUrl, path) {
  return `${baseUrl.replace(/\/$/, "")}${path}`;
}

async function readJsonResponse(response) {
  const text = await response.text();
  let data = {};

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { error: text };
    }
  }

  if (!response.ok) {
    throw new Error(data.error || `Request failed with status ${response.status}`);
  }

  if (data?.error) {
    throw new Error(data.error);
  }

  return data;
}

export async function fetchBackendStatus(apiBaseUrl) {
  const response = await fetch(joinUrl(apiBaseUrl, "/"));
  return readJsonResponse(response);
}

export async function fetchPoseCatalog(apiBaseUrl) {
  const response = await fetch(joinUrl(apiBaseUrl, "/poses/catalog"));
  return readJsonResponse(response);
}

export async function fetchRecommendations(apiBaseUrl, payload) {
  const response = await fetch(joinUrl(apiBaseUrl, "/recommendations"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return readJsonResponse(response);
}

export async function fetchCoachSpeechAudio(apiBaseUrl, payload) {
  const response = await fetch(joinUrl(apiBaseUrl, "/tts"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    let message = `Request failed with status ${response.status}`;
    if (text) {
      try {
        const data = JSON.parse(text);
        message = data.detail || data.error || message;
      } catch {
        message = text;
      }
    }
    throw new Error(message);
  }

  return {
    blob: await response.blob(),
    provider: response.headers.get("X-TTS-Provider") || "unknown",
    model: response.headers.get("X-TTS-Model") || "",
    voice: response.headers.get("X-TTS-Voice") || "",
    cached: response.headers.get("X-TTS-Cached") === "true",
  };
}

export async function analyzeSnapshot(apiBaseUrl, { file, userId, targetPose }) {
  const formData = new FormData();
  formData.append("file", file);
  if (userId) formData.append("user_id", userId);
  if (targetPose) formData.append("target_pose", targetPose);

  const response = await fetch(joinUrl(apiBaseUrl, "/realtime_feedback"), {
    method: "POST",
    body: formData,
  });
  return readJsonResponse(response);
}

export async function analyzeLiveFrame(apiBaseUrl, { file, streamId, userId, targetPose }) {
  const formData = new FormData();
  formData.append("file", file, "live-frame.jpg");
  formData.append("stream_id", streamId);
  if (userId) formData.append("user_id", userId);
  if (targetPose) formData.append("target_pose", targetPose);

  const response = await fetch(joinUrl(apiBaseUrl, "/realtime_frame"), {
    method: "POST",
    body: formData,
  });
  return readJsonResponse(response);
}

export async function resetCoachSession(apiBaseUrl, streamId) {
  const response = await fetch(joinUrl(apiBaseUrl, `/session/${streamId}/reset`), {
    method: "POST",
  });
  return readJsonResponse(response);
}

export function buildRealtimeSocketUrl(apiBaseUrl, { streamId, userId, targetPose }) {
  const wsBase = apiBaseUrl.replace(/^http/i, "ws").replace(/\/$/, "");
  const params = new URLSearchParams();
  if (streamId) params.set("stream_id", streamId);
  if (userId) params.set("user_id", userId);
  if (targetPose) params.set("target_pose", targetPose);
  return `${wsBase}/ws/realtime?${params.toString()}`;
}
