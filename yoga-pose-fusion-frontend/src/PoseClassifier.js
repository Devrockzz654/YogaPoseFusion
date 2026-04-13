import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  analyzeLiveFrame,
  analyzeSnapshot,
  buildRealtimeSocketUrl,
  fetchBackendStatus,
  fetchCoachSpeechAudio,
  fetchPoseCatalog,
  resetCoachSession,
} from "./services/api";

const JOINT_INDEX = {
  left_elbow: 13,
  right_elbow: 14,
  left_knee: 25,
  right_knee: 26,
  left_hip: 23,
  right_hip: 24,
  left_shoulder: 11,
  right_shoulder: 12,
};

function uniqueMessages(values) {
  const output = [];
  values.forEach((value) => {
    if (value && !output.includes(value)) {
      output.push(value);
    }
  });
  return output;
}

function buildCoachMessages(payload) {
  if (!payload) return [];

  const messages = [];
  if (payload.target_pose?.message && payload.target_pose.status !== "aligned") {
    messages.push(payload.target_pose.message);
  }
  if (Array.isArray(payload.issues)) {
    payload.issues.forEach((issue) => {
      if (issue.message) messages.push(issue.message);
    });
  }
  if (Array.isArray(payload.feedback)) {
    payload.feedback.forEach((message) => messages.push(message));
  }
  if (Array.isArray(payload.recovery_hints)) {
    payload.recovery_hints.forEach((message) => messages.push(message));
  }

  return uniqueMessages(messages);
}

function coachTone(payload) {
  const status = payload?.target_pose?.status;
  if (status === "aligned") return "aligned";
  if (status === "different_pose") return "different";
  if (status === "hold_steady" || status === "awaiting_pose") return "recovery";
  if (status === "needs_correction") return "warning";
  if (payload?.issues?.length) return "warning";
  return "neutral";
}

function toneLabel(payload) {
  const status = payload?.target_pose?.status;
  if (status === "aligned") return "Aligned";
  if (status === "different_pose") return "Wrong pose detected";
  if (status === "hold_steady") return "Hold steady";
  if (status === "awaiting_pose") return "Move into pose";
  if (status === "needs_correction") return "Needs correction";
  return "Live feedback";
}

function buildPoseNarration(pose, mode, poseIndex, totalPoses) {
  if (!pose) return [];

  const intro =
    mode === "routine"
      ? `Pose ${poseIndex + 1} of ${totalPoses}. ${pose.pose_name}. ${
          pose.why_selected || "This pose is part of your personalized routine."
        }`
      : `${pose.pose_name}. ${
          pose.sanskrit_name ? `${pose.sanskrit_name}. ` : ""
        }${pose.why_selected || "Let’s set it up carefully."}`;

  const steps = (pose.instructions || []).map(
    (step, index) => `Step ${index + 1}. ${step}`
  );
  const breath = pose.breath_cues?.[0]
    ? `Breath cue. ${pose.breath_cues[0]}`
    : "";
  const modification = pose.modifications?.[0]
    ? `Modification option. ${pose.modifications[0]}`
    : "";
  const caution = pose.caution ? `Safety note. ${pose.caution}` : "";
  const holdPrompt = `When you are ready, hold ${pose.pose_name} for ${
    pose.hold_seconds || 20
  } seconds.`;

  return [intro, ...steps, breath, modification, caution, holdPrompt].filter(Boolean);
}

function buildReleaseNarration(pose, mode) {
  if (!pose) return [];
  const segments = [`Release ${pose.pose_name} with control.`];
  if (mode === "selected" && pose.repetitions > 1) {
    segments.push(
      `You can repeat this for ${pose.repetitions} total rounds whenever you feel ready.`
    );
  }
  return segments;
}

function voiceScore(voice, voicePersona) {
  const name = `${voice.name} ${voice.voiceURI || ""}`.toLowerCase();
  let score = 0;

  if (voice.default) score += 2;
  if (voice.lang?.toLowerCase().startsWith("en")) score += 2;
  if (voice.localService) score += 1;

  if (voicePersona === "female") {
    const femaleMarkers = [
      "female",
      "woman",
      "samantha",
      "ava",
      "victoria",
      "allison",
      "serena",
      "karen",
      "moira",
      "susan",
      "zira",
      "jenny",
      "aria",
      "siri",
      "zoe",
      "rishi female",
      "google us english",
    ];
    if (femaleMarkers.some((marker) => name.includes(marker))) score += 8;
    if (name.includes("male")) score -= 6;
    if (name.includes("david") || name.includes("alex") || name.includes("daniel")) score -= 4;
  }

  return score;
}

function pickPreferredVoice(voices, voicePersona) {
  if (!voices.length) return null;
  const sorted = [...voices].sort(
    (left, right) => voiceScore(right, voicePersona) - voiceScore(left, voicePersona)
  );
  return sorted[0] || null;
}

export default function PoseClassifier({
  user,
  preferences,
  onUpdatePreferences,
  recommendations,
  featuredRecommendations,
  selectedPose,
  onSelectPose,
}) {
  const [catalog, setCatalog] = useState([]);
  const [apiStatus, setApiStatus] = useState("Checking backend...");
  const [apiOnline, setApiOnline] = useState(false);
  const [ttsStatus, setTtsStatus] = useState({
    available: false,
    provider: "openai",
    configured: false,
    package_installed: false,
    model: "",
    voice: "",
    voice_label: "",
    format: "mp3",
  });
  const [snapshotFile, setSnapshotFile] = useState(null);
  const [snapshotPreview, setSnapshotPreview] = useState("");
  const [snapshotResult, setSnapshotResult] = useState(null);
  const [snapshotError, setSnapshotError] = useState("");
  const [snapshotLoading, setSnapshotLoading] = useState(false);

  const [cameraDevices, setCameraDevices] = useState([]);
  const [selectedCameraId, setSelectedCameraId] = useState("");
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [liveError, setLiveError] = useState("");
  const [streamResult, setStreamResult] = useState(null);
  const [restResult, setRestResult] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isRestStreaming, setIsRestStreaming] = useState(false);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [audioCoachState, setAudioCoachState] = useState({
    running: false,
    mode: "idle",
    poseName: "",
    stage: "Ready",
    message: "Choose a pose and start narrated coaching when you want spoken guidance.",
    poseIndex: 0,
    totalPoses: 0,
  });
  const [holdCountdown, setHoldCountdown] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const wsRef = useRef(null);
  const wsTimerRef = useRef(null);
  const restTimerRef = useRef(null);
  const holdIntervalRef = useRef(null);
  const fileInputRef = useRef(null);
  const lastVoiceRef = useRef({ message: "", time: 0 });
  const audioSessionRef = useRef(0);
  const audioElementRef = useRef(null);
  const audioObjectUrlRef = useRef("");
  const sessionIdRef = useRef(
    `coach_${(user?.email || "guest").replace(/[^a-z0-9]+/gi, "_")}_${Date.now()}`
  );

  const apiBaseUrl = preferences?.apiBaseUrl || "http://localhost:8000";
  const poseOptions = recommendations.length ? recommendations : catalog;
  const routinePoseOptions = featuredRecommendations?.length
    ? featuredRecommendations
    : poseOptions.slice(0, 8);
  const effectiveSelectedPose = selectedPose || poseOptions[0]?.pose_name || "";
  const activeGuide =
    recommendations.find((pose) => pose.pose_name === effectiveSelectedPose) ||
    catalog.find((pose) => pose.pose_name === effectiveSelectedPose) ||
    null;
  const activeGuideReferenceImage = activeGuide?.reference_image_path
    ? `${apiBaseUrl.replace(/\/$/, "")}${activeGuide.reference_image_path}`
    : "";
  const livePayload = isStreaming ? streamResult : isRestStreaming ? restResult : null;
  const latestPayload = livePayload || snapshotResult;
  const voiceEnabled = preferences?.voiceEnabled ?? true;
  const voicePersona = preferences?.voicePersona || "female";
  const practiceMode = preferences?.practiceMode || "guided";
  const guidedMode = practiceMode === "guided";
  const narrationVoiceEnabled = voiceEnabled && guidedMode;
  const correctionVoiceEnabled = voiceEnabled;
  const speechSupported =
    typeof window !== "undefined" &&
    "speechSynthesis" in window &&
    "SpeechSynthesisUtterance" in window;

  useEffect(() => {
    if (!selectedPose && poseOptions.length > 0) {
      onSelectPose?.(poseOptions[0].pose_name);
    }
  }, [onSelectPose, poseOptions, selectedPose]);

  useEffect(() => {
    if (!speechSupported) return undefined;

    const loadVoices = () => {
      setAvailableVoices(window.speechSynthesis.getVoices());
    };

    loadVoices();
    window.speechSynthesis.addEventListener?.("voiceschanged", loadVoices);

    return () => {
      window.speechSynthesis.removeEventListener?.("voiceschanged", loadVoices);
    };
  }, [speechSupported]);

  const preferredVoice = useMemo(
    () => pickPreferredVoice(availableVoices, voicePersona),
    [availableVoices, voicePersona]
  );
  const ttsPlaybackAvailable = ttsStatus.available || speechSupported;
  const voiceProfileLabel = ttsStatus.available
    ? `AI voice: ${ttsStatus.voice_label || ttsStatus.voice || "Marin"}`
    : preferredVoice
      ? `${voicePersona === "female" ? "Browser female voice" : "Browser voice"}: ${preferredVoice.name}`
      : speechSupported
        ? "Browser voice fallback ready"
        : "Voice unavailable";

  const applySpeechPreferences = useCallback(
    (utterance, { rate = 0.96, pitch = 1.02 } = {}) => {
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }
      utterance.rate = rate;
      utterance.pitch = pitch;
    },
    [preferredVoice]
  );

  const stopBackendAudio = useCallback(() => {
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current.src = "";
      audioElementRef.current = null;
    }
    if (audioObjectUrlRef.current) {
      URL.revokeObjectURL(audioObjectUrlRef.current);
      audioObjectUrlRef.current = "";
    }
  }, []);

  const stopSpeechOutput = useCallback(() => {
    stopBackendAudio();
    if (speechSupported) {
      window.speechSynthesis.cancel();
    }
  }, [speechSupported, stopBackendAudio]);

  const playBrowserUtterance = useCallback(
    (text, { sessionId, rate = 0.96, pitch = 1.02 } = {}) =>
      new Promise((resolve) => {
        if (!speechSupported || !text) {
          resolve();
          return;
        }

        const utterance = new SpeechSynthesisUtterance(text);
        applySpeechPreferences(utterance, { rate, pitch });
        utterance.onend = () => resolve();
        utterance.onerror = () => resolve();
        if (audioSessionRef.current !== sessionId) {
          resolve();
          return;
        }
        window.speechSynthesis.speak(utterance);
      }),
    [applySpeechPreferences, speechSupported]
  );

  const playAudioBlob = useCallback(
    (blob, { sessionId } = {}) =>
      new Promise((resolve) => {
        if (!blob) {
          resolve();
          return;
        }

        stopBackendAudio();
        const objectUrl = URL.createObjectURL(blob);
        const audio = new Audio(objectUrl);
        audioObjectUrlRef.current = objectUrl;
        audioElementRef.current = audio;

        const finalize = () => {
          if (audioElementRef.current === audio) {
            audioElementRef.current = null;
          }
          if (audioObjectUrlRef.current === objectUrl) {
            URL.revokeObjectURL(objectUrl);
            audioObjectUrlRef.current = "";
          }
          resolve();
        };

        audio.onended = finalize;
        audio.onerror = finalize;

        if (audioSessionRef.current !== sessionId) {
          finalize();
          return;
        }

        audio.play().catch(finalize);
      }),
    [stopBackendAudio]
  );

  const playSpeechSegment = useCallback(
    async (
      text,
      {
        sessionId,
        cueType = "narration",
        rate = 0.96,
        pitch = 1.02,
        interrupt = false,
      } = {}
    ) => {
      const content = (text || "").trim();
      if (!content) return;
      if (audioSessionRef.current !== sessionId) return;

      if (interrupt) {
        stopSpeechOutput();
      }

      if (ttsStatus.available) {
        try {
          const audioClip = await fetchCoachSpeechAudio(apiBaseUrl, {
            text: content,
            cue_type: cueType,
            voice: ttsStatus.voice || "marin",
            response_format: ttsStatus.format || "mp3",
            voice_persona: voicePersona,
          });
          if (audioSessionRef.current !== sessionId) return;
          await playAudioBlob(audioClip.blob, { sessionId });
          return;
        } catch (error) {
          setLiveError((current) =>
            current || `${error.message || "Backend TTS unavailable."} Falling back to browser voice.`
          );
        }
      }

      await playBrowserUtterance(content, { sessionId, rate, pitch });
    },
    [
      apiBaseUrl,
      playAudioBlob,
      playBrowserUtterance,
      stopSpeechOutput,
      ttsStatus.available,
      ttsStatus.format,
      ttsStatus.voice,
      voicePersona,
    ]
  );

  useEffect(() => {
    let mounted = true;

    async function loadCatalog() {
      try {
        const [statusData, catalogData] = await Promise.all([
          fetchBackendStatus(apiBaseUrl),
          fetchPoseCatalog(apiBaseUrl),
        ]);
        if (!mounted) return;
        setApiOnline(true);
        setApiStatus(`Backend ready on ${statusData.device}`);
        setTtsStatus(statusData.tts || {
          available: false,
          provider: "openai",
          configured: false,
          package_installed: false,
          model: "",
          voice: "",
          voice_label: "",
          format: "mp3",
        });
        setCatalog(catalogData.poses || []);
      } catch (error) {
        if (!mounted) return;
        setApiOnline(false);
        setApiStatus(error.message || "Backend unavailable");
        setTtsStatus((prev) => ({ ...prev, available: false }));
      }
    }

    loadCatalog();
    const interval = setInterval(loadCatalog, 20000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [apiBaseUrl]);

  const refreshCameraDevices = useCallback(async () => {
    if (!navigator.mediaDevices?.enumerateDevices) return;
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videos = devices.filter((device) => device.kind === "videoinput");
      setCameraDevices(videos);
      if (!selectedCameraId && videos.length > 0) {
        setSelectedCameraId(videos[0].deviceId);
      }
    } catch {
      setCameraDevices([]);
    }
  }, [selectedCameraId]);

  useEffect(() => {
    refreshCameraDevices();
    if (!navigator.mediaDevices?.addEventListener) return undefined;
    const handleChange = () => refreshCameraDevices();
    navigator.mediaDevices.addEventListener("devicechange", handleChange);
    return () => navigator.mediaDevices.removeEventListener("devicechange", handleChange);
  }, [refreshCameraDevices]);

  useEffect(() => {
    return () => {
      audioSessionRef.current += 1;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (holdIntervalRef.current) clearInterval(holdIntervalRef.current);
      if (wsTimerRef.current) clearInterval(wsTimerRef.current);
      if (restTimerRef.current) clearInterval(restTimerRef.current);
      if (wsRef.current) wsRef.current.close();
      stopSpeechOutput();
    };
  }, [stopSpeechOutput]);

  useEffect(() => {
    return () => {
      if (snapshotPreview) {
        URL.revokeObjectURL(snapshotPreview);
      }
    };
  }, [snapshotPreview]);

  const drawOverlay = useCallback((payload) => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video || !payload?.landmarks || !payload?.connections) return;
    if (!video.videoWidth || !video.videoHeight) return;

    const ctx = canvas.getContext("2d");
    const width = video.videoWidth;
    const height = video.videoHeight;
    if (canvas.width !== width) canvas.width = width;
    if (canvas.height !== height) canvas.height = height;

    ctx.clearRect(0, 0, width, height);

    const highlightedJoints = new Set(
      (payload.bad_joints || [])
        .map((joint) => JOINT_INDEX[joint])
        .filter((value) => value !== undefined)
    );

    ctx.lineWidth = 2;
    ctx.strokeStyle = "rgba(58, 92, 77, 0.75)";
    payload.connections.forEach(([start, end]) => {
      const first = payload.landmarks[start];
      const second = payload.landmarks[end];
      if (!first || !second) return;
      if ((first.visibility ?? 1) < 0.3 || (second.visibility ?? 1) < 0.3) return;
      ctx.beginPath();
      ctx.moveTo(first.x * width, first.y * height);
      ctx.lineTo(second.x * width, second.y * height);
      ctx.stroke();
    });

    payload.landmarks.forEach((point, index) => {
      if ((point.visibility ?? 1) < 0.3) return;
      const isIssue = highlightedJoints.has(index);
      ctx.fillStyle = isIssue ? "rgba(193, 89, 54, 0.95)" : "rgba(63, 119, 104, 0.95)";
      ctx.beginPath();
      ctx.arc(point.x * width, point.y * height, isIssue ? 6 : 4, 0, Math.PI * 2);
      ctx.fill();
    });
  }, []);

  useEffect(() => {
    drawOverlay(livePayload);
  }, [drawOverlay, livePayload]);

  const clearAudioCoachTimers = useCallback(() => {
    if (holdIntervalRef.current) {
      clearInterval(holdIntervalRef.current);
      holdIntervalRef.current = null;
    }
    setHoldCountdown(null);
  }, []);

  const finishAudioCoach = useCallback(
    (message) => {
      clearAudioCoachTimers();
      setAudioCoachState({
        running: false,
        mode: "idle",
        poseName: "",
        stage: "Complete",
        message,
        poseIndex: 0,
        totalPoses: 0,
      });
    },
    [clearAudioCoachTimers]
  );

  const stopAudioCoach = useCallback(
    (message = "Audio coach stopped.") => {
      audioSessionRef.current += 1;
      clearAudioCoachTimers();
      stopSpeechOutput();
      setAudioCoachState({
        running: false,
        mode: "idle",
        poseName: "",
        stage: "Stopped",
        message,
        poseIndex: 0,
        totalPoses: 0,
      });
    },
    [clearAudioCoachTimers, stopSpeechOutput]
  );

  const speakSegments = useCallback(
    async (segments, { sessionId, rate = 0.98, pitch = 1, onComplete } = {}) => {
      const filteredSegments = segments.filter(Boolean);
      if (!filteredSegments.length) {
        onComplete?.();
        return;
      }

      if (!ttsPlaybackAvailable || !narrationVoiceEnabled) {
        onComplete?.();
        return;
      }

      for (const segment of filteredSegments) {
        if (audioSessionRef.current !== sessionId) return;
        await playSpeechSegment(segment, {
          sessionId,
          cueType: "narration",
          rate,
          pitch,
        });
      }

      if (audioSessionRef.current !== sessionId) return;
      onComplete?.();
    },
    [narrationVoiceEnabled, playSpeechSegment, ttsPlaybackAvailable]
  );

  const startHoldPhase = useCallback(
    (pose, { sessionId, mode, poseIndex, totalPoses, onComplete }) => {
      clearAudioCoachTimers();
      const totalSeconds = Math.max(8, Math.min(Number(pose?.hold_seconds) || 20, 90));
      const midpoint = Math.floor(totalSeconds / 2);
      let remaining = totalSeconds;

      setAudioCoachState({
        running: true,
        mode,
        poseName: pose.pose_name,
        stage: "Hold",
        message: `Holding ${pose.pose_name}. Stay steady and breathe evenly.`,
        poseIndex: poseIndex + 1,
        totalPoses,
      });
      setHoldCountdown(totalSeconds);

      holdIntervalRef.current = setInterval(() => {
        if (audioSessionRef.current !== sessionId) {
          clearAudioCoachTimers();
          return;
        }

        remaining -= 1;
        setHoldCountdown(Math.max(remaining, 0));

        if (remaining === midpoint && totalSeconds >= 16 && pose?.breath_cues?.[1]) {
          speakSegments([pose.breath_cues[1]], { sessionId, rate: 0.95 });
        }

        if (remaining <= 0) {
          clearAudioCoachTimers();
          setAudioCoachState({
            running: true,
            mode,
            poseName: pose.pose_name,
            stage: "Release",
            message: `Releasing ${pose.pose_name}.`,
            poseIndex: poseIndex + 1,
            totalPoses,
          });
          speakSegments(buildReleaseNarration(pose, mode), {
            sessionId,
            rate: 0.96,
            onComplete,
          });
        }
      }, 1000);
    },
    [clearAudioCoachTimers, speakSegments]
  );

  const runPoseNarration = useCallback(
    (pose, { sessionId, mode, poseIndex, totalPoses, onComplete }) => {
      if (!pose) return;

      onSelectPose?.(pose.pose_name);
      setAudioCoachState({
        running: true,
        mode,
        poseName: pose.pose_name,
        stage: "Setup",
        message:
          mode === "routine"
            ? `Guiding ${pose.pose_name}, pose ${poseIndex + 1} of ${totalPoses}.`
            : `Narrating ${pose.pose_name}.`,
        poseIndex: poseIndex + 1,
        totalPoses,
      });

      speakSegments(buildPoseNarration(pose, mode, poseIndex, totalPoses), {
        sessionId,
        rate: 0.98,
        onComplete: () =>
          startHoldPhase(pose, {
            sessionId,
            mode,
            poseIndex,
            totalPoses,
            onComplete,
          }),
      });
    },
    [onSelectPose, speakSegments, startHoldPhase]
  );

  const ensureAudioCoachReady = useCallback(() => {
    if (!activeGuide && !poseOptions.length) {
      setLiveError("Generate a routine or choose a pose before starting the audio coach.");
      return false;
    }
    if (!narrationVoiceEnabled) {
      setLiveError("Enable voice cues in Settings before starting the audio coach.");
      return false;
    }
    if (!ttsPlaybackAvailable) {
      setLiveError("Voice guidance is unavailable. Configure backend TTS or use a supported browser.");
      return false;
    }
    setLiveError("");
    return true;
  }, [activeGuide, narrationVoiceEnabled, poseOptions.length, ttsPlaybackAvailable]);

  const startSelectedAudioCoach = useCallback(() => {
    if (!ensureAudioCoachReady() || !activeGuide) return;

    audioSessionRef.current += 1;
    const sessionId = audioSessionRef.current;
    clearAudioCoachTimers();
    stopSpeechOutput();

    runPoseNarration(activeGuide, {
      sessionId,
      mode: "selected",
      poseIndex: 0,
      totalPoses: 1,
      onComplete: () =>
        finishAudioCoach(`Finished narrated guidance for ${activeGuide.pose_name}.`),
    });
  }, [
    activeGuide,
    clearAudioCoachTimers,
    ensureAudioCoachReady,
    finishAudioCoach,
    runPoseNarration,
    stopSpeechOutput,
  ]);

  const startRoutineAudioCoach = useCallback(() => {
    if (!ensureAudioCoachReady()) return;

    const routine = routinePoseOptions.length
      ? routinePoseOptions
      : activeGuide
        ? [activeGuide]
        : [];
    if (!routine.length) return;

    const selectedIndex = Math.max(
      0,
      routine.findIndex((pose) => pose.pose_name === effectiveSelectedPose)
    );
    const orderedRoutine = [
      ...routine.slice(selectedIndex),
      ...routine.slice(0, selectedIndex),
    ];

    audioSessionRef.current += 1;
    const sessionId = audioSessionRef.current;
    clearAudioCoachTimers();
    stopSpeechOutput();

    const playPoseAtIndex = (index) => {
      if (audioSessionRef.current !== sessionId) return;
      const pose = orderedRoutine[index];
      if (!pose) {
        finishAudioCoach("Guided routine complete.");
        return;
      }

      runPoseNarration(pose, {
        sessionId,
        mode: "routine",
        poseIndex: index,
        totalPoses: orderedRoutine.length,
        onComplete: () => {
          if (index === orderedRoutine.length - 1) {
            finishAudioCoach("Guided routine complete.");
            return;
          }

          const nextPose = orderedRoutine[index + 1];
          setAudioCoachState({
            running: true,
            mode: "routine",
            poseName: nextPose.pose_name,
            stage: "Transition",
            message: `Transitioning to ${nextPose.pose_name}.`,
            poseIndex: index + 1,
            totalPoses: orderedRoutine.length,
          });

          speakSegments(
            [
              `Transition with control. Up next is ${nextPose.pose_name}.`,
              nextPose.why_selected || "",
            ],
            {
              sessionId,
              rate: 0.97,
              onComplete: () => playPoseAtIndex(index + 1),
            }
          );
        },
      });
    };

    setAudioCoachState({
      running: true,
      mode: "routine",
      poseName: orderedRoutine[0].pose_name,
      stage: "Introduction",
      message: `Starting a narrated routine with ${orderedRoutine.length} poses.`,
      poseIndex: 1,
      totalPoses: orderedRoutine.length,
    });

    speakSegments(
      [
        "Starting your personalized yoga routine.",
        `We will practice ${orderedRoutine.length} poses, beginning with ${orderedRoutine[0].pose_name}.`,
        "Keep the live coach running if you want visual correction while I guide the flow.",
      ],
      {
        sessionId,
        rate: 0.98,
        onComplete: () => playPoseAtIndex(0),
      }
    );
  }, [
    activeGuide,
    clearAudioCoachTimers,
    effectiveSelectedPose,
    ensureAudioCoachReady,
    finishAudioCoach,
    routinePoseOptions,
    runPoseNarration,
    speakSegments,
    stopSpeechOutput,
  ]);

  const speakPayload = useCallback(
    async (payload) => {
      if (!correctionVoiceEnabled || !ttsPlaybackAvailable || !payload) return;
      if (audioCoachState.running) return;
      const [message] = buildCoachMessages(payload);
      if (!message) return;
      if (payload.target_pose?.status === "aligned") return;

      const now = Date.now();
      const isSameRecent =
        lastVoiceRef.current.message === message &&
        now - lastVoiceRef.current.time < 4500;
      if (isSameRecent) return;

      stopSpeechOutput();
      await playSpeechSegment(message, {
        sessionId: audioSessionRef.current,
        cueType: "correction",
        rate: guidedMode ? 0.98 : 1.0,
        pitch: guidedMode ? 1.02 : 1.0,
        interrupt: true,
      });
      lastVoiceRef.current = { message, time: now };
    },
    [
      audioCoachState.running,
      correctionVoiceEnabled,
      guidedMode,
      playSpeechSegment,
      stopSpeechOutput,
      ttsPlaybackAvailable,
    ]
  );

  useEffect(() => {
    speakPayload(livePayload);
  }, [livePayload, speakPayload]);

  useEffect(() => {
    if ((!guidedMode || !voiceEnabled) && audioCoachState.running) {
      stopAudioCoach(
        guidedMode
          ? "Audio coach stopped because voice cues were disabled."
          : "Audio coach stopped because silent correction mode was enabled."
      );
    }
  }, [audioCoachState.running, guidedMode, stopAudioCoach, voiceEnabled]);

  const handleSnapshotSelection = (file) => {
    if (!file) return;
    if (snapshotPreview) URL.revokeObjectURL(snapshotPreview);
    setSnapshotFile(file);
    setSnapshotPreview(URL.createObjectURL(file));
    setSnapshotResult(null);
    setSnapshotError("");
  };

  const runSnapshotAnalysis = async (file = snapshotFile) => {
    if (!file) {
      setSnapshotError("Select or capture an image first.");
      return;
    }

    setSnapshotLoading(true);
    setSnapshotError("");

    try {
      const result = await analyzeSnapshot(apiBaseUrl, {
        file,
        userId: user?.email,
        targetPose: effectiveSelectedPose,
      });
      setSnapshotResult(result);
    } catch (error) {
      setSnapshotError(error.message || "Unable to analyze this image.");
    } finally {
      setSnapshotLoading(false);
    }
  };

  const startCamera = async () => {
    setCameraError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: 960,
          height: 720,
          ...(selectedCameraId ? { deviceId: { exact: selectedCameraId } } : {}),
        },
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
      refreshCameraDevices();
    } catch {
      setCameraError("Unable to access the selected camera. Check permissions and try again.");
    }
  };

  const stopRealtime = useCallback(() => {
    if (wsTimerRef.current) {
      clearInterval(wsTimerRef.current);
      wsTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const stopRestRealtime = useCallback(() => {
    if (restTimerRef.current) {
      clearInterval(restTimerRef.current);
      restTimerRef.current = null;
    }
    setIsRestStreaming(false);
  }, []);

  const stopCamera = () => {
    stopRealtime();
    stopRestRealtime();
    setStreamResult(null);
    setRestResult(null);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    const canvas = canvasRef.current;
    if (canvas) {
      const context = canvas.getContext("2d");
      context.clearRect(0, 0, canvas.width, canvas.height);
    }
    setCameraActive(false);
  };

  const captureFrame = useCallback(async () => {
    if (!videoRef.current || !videoRef.current.videoWidth) return null;

    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const context = canvas.getContext("2d");
    context.drawImage(videoRef.current, 0, 0);

    return new Promise((resolve) => {
      canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.85);
    });
  }, []);

  const captureSnapshotFromCamera = async () => {
    const blob = await captureFrame();
    if (!blob) {
      setSnapshotError("Start the camera before capturing a snapshot.");
      return;
    }

    const file = new File([blob], "camera-snapshot.jpg", { type: "image/jpeg" });
    handleSnapshotSelection(file);
    runSnapshotAnalysis(file);
  };

  const startRealtime = () => {
    if (!cameraActive || isStreaming) return;
    setLiveError("");

    const socket = new WebSocket(
      buildRealtimeSocketUrl(apiBaseUrl, {
        streamId: sessionIdRef.current,
        userId: user?.email,
        targetPose: effectiveSelectedPose,
      })
    );
    wsRef.current = socket;

    socket.onopen = () => {
      setIsStreaming(true);

      wsTimerRef.current = setInterval(async () => {
        const blob = await captureFrame();
        if (!blob || socket.readyState !== WebSocket.OPEN) return;

        const reader = new FileReader();
        reader.onload = () => {
          const result = typeof reader.result === "string" ? reader.result : "";
          const base64 = result.split(",")[1];
          socket.send(
            JSON.stringify({
              b64: base64,
              target_pose: effectiveSelectedPose,
            })
          );
        };
        reader.readAsDataURL(blob);
      }, 220);
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        setStreamResult(payload);
        setLiveError("");
      } catch {
        setLiveError("The live coach returned an unreadable response.");
      }
    };

    socket.onerror = () => {
      setLiveError("Realtime socket failed. Try REST mode or restart the session.");
      stopRealtime();
    };

    socket.onclose = () => {
      stopRealtime();
    };
  };

  const startRestCoach = () => {
    if (!cameraActive || isRestStreaming) return;
    setLiveError("");
    setIsRestStreaming(true);

    restTimerRef.current = setInterval(async () => {
      const blob = await captureFrame();
      if (!blob) return;

      try {
        const payload = await analyzeLiveFrame(apiBaseUrl, {
          file: blob,
          streamId: sessionIdRef.current,
          userId: user?.email,
          targetPose: effectiveSelectedPose,
        });
        setRestResult(payload);
        setLiveError("");
      } catch (error) {
        setLiveError(error.message || "Unable to poll live feedback.");
      }
    }, 240);
  };

  const resetSession = async () => {
    try {
      await resetCoachSession(apiBaseUrl, sessionIdRef.current);
      setStreamResult(null);
      setRestResult(null);
      setLiveError("");
    } catch (error) {
      setLiveError(error.message || "Unable to reset the coach session.");
    }
  };

  const coachMessages = useMemo(() => buildCoachMessages(latestPayload), [latestPayload]);
  const quality = latestPayload?.quality || {};
  const metrics = latestPayload?.metrics || null;
  const primaryCoachMessage = guidedMode
    ? latestPayload?.target_pose?.message ||
      coachMessages[0] ||
      "Start the camera and enter the selected pose to receive coaching."
    : latestPayload?.pose_name
      ? `Detected pose: ${latestPayload.pose_name}. ${coachMessages[0] || "Keep holding and I will continue checking your alignment."}`
      : "Start the camera to identify the current pose and receive visual correction only.";

  return (
    <div className="coach-layout">
      <aside className="coach-sidebar">
        <div className="coach-side-card mode-card">
          <div className="section-kicker">Practice mode</div>
          <h3>{guidedMode ? "Guided audio coach" : "Silent correction and identification"}</h3>
          <p className="guide-focus">
            {guidedMode
              ? "Use narration, breath prompts, and spoken coaching while you practice."
              : "Practice on your own while the app quietly identifies the detected pose and shows visual correction only."}
          </p>
          <div className="segmented-row">
            <button
              className={`ghost-pill ${guidedMode ? "active" : ""}`}
              onClick={() =>
                onUpdatePreferences?.((prev) => ({ ...prev, practiceMode: "guided" }))
              }
              type="button"
            >
              Guided
            </button>
            <button
              className={`ghost-pill ${!guidedMode ? "active" : ""}`}
              onClick={() =>
                onUpdatePreferences?.((prev) => ({ ...prev, practiceMode: "silent" }))
              }
              type="button"
            >
              Silent
            </button>
          </div>
          <div className="mode-meta-row">
            <span>{guidedMode ? "Narration active" : "Narration paused"}</span>
            <span>{voiceEnabled ? "Voice cues on" : "Voice cues off"}</span>
            <span>{voiceProfileLabel}</span>
          </div>
        </div>

        <div className="coach-side-card target-pose-card">
          <div className="section-kicker">Target pose</div>
          <h2>Guide the live coach toward the asana you want to practice.</h2>
          <p className="panel-lead">
            Select a pose from the personalized routine, review the setup notes, then move into Live Coach so the backend can confirm and correct that specific asana.
          </p>

          <label className="stacked-field">
            <span>Pose to coach</span>
            <select
              value={effectiveSelectedPose}
              onChange={(event) => onSelectPose?.(event.target.value)}
              disabled={audioCoachState.running}
            >
              {poseOptions.map((pose) => (
                <option key={pose.pose_name} value={pose.pose_name}>
                  {pose.pose_name}
                </option>
              ))}
            </select>
          </label>

          {activeGuide ? (
            <div className="guide-block">
              {activeGuideReferenceImage ? (
                <div className="guide-reference">
                  <img
                    src={activeGuideReferenceImage}
                    alt={`${activeGuide.pose_name} reference`}
                    className="guide-reference-image"
                    loading="lazy"
                  />
                  <div className="guide-reference-caption">Reference pose</div>
                </div>
              ) : null}

              <div className="guide-meta">
                <span>{activeGuide.difficulty || "Coachable pose"}</span>
                {"hold_seconds" in activeGuide ? <span>{activeGuide.hold_seconds}s hold</span> : null}
                {"repetitions" in activeGuide ? <span>{activeGuide.repetitions} rounds</span> : null}
              </div>
              <h3>{activeGuide.pose_name}</h3>
              <p className="guide-focus">
                {activeGuide.coach_focus || "Use the live overlay to keep the strongest alignment points steady."}
              </p>

              {activeGuide.instructions?.length ? (
                <div className="guide-section">
                  <strong>How to do it</strong>
                  <ol>
                    {activeGuide.instructions.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>
                </div>
              ) : null}

              {activeGuide.breath_cues?.length ? (
                <div className="guide-section">
                  <strong>Breath cues</strong>
                  <ul>
                    {activeGuide.breath_cues.map((cue) => (
                      <li key={cue}>{cue}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {activeGuide.common_mistakes?.length ? (
                <div className="guide-section">
                  <strong>Common mistakes</strong>
                  <ul>
                    {activeGuide.common_mistakes.slice(0, 3).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {activeGuide.modifications?.length ? (
                <div className="guide-section">
                  <strong>Easy modifications</strong>
                  <ul>
                    {activeGuide.modifications.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {activeGuide.caution ? (
                <div className="guide-caution">{activeGuide.caution}</div>
              ) : null}
            </div>
          ) : null}
        </div>

      </aside>

      <section className="studio-panel coach-stage-panel">
        <div className="coach-stage-head">
          <div>
            <div className="section-kicker">Live coach</div>
            <h2>Practice with camera feedback that knows the target pose.</h2>
          </div>
          <div className={`status-chip ${apiOnline ? "online" : "offline"}`}>
            {apiStatus}
          </div>
        </div>

        <div className="live-dynamic-bar">
          <span className={`live-dot ${cameraActive ? "active" : ""}`} />
          <span>{cameraActive ? "Camera live" : "Camera idle"}</span>
          <span>{guidedMode ? "Guided mode" : "Silent mode"}</span>
          <span>{isStreaming || isRestStreaming ? "Realtime coaching active" : "Realtime coaching paused"}</span>
          <span>{ttsStatus.available ? `AI voice ${ttsStatus.voice_label || ttsStatus.voice}` : voiceProfileLabel}</span>
        </div>

        <div className={`camera-shell ${cameraActive ? "active" : ""}`}>
          <video ref={videoRef} autoPlay playsInline className="coach-video" />
          <canvas ref={canvasRef} className="coach-canvas" />
          {!cameraActive ? <div className="camera-overlay">Camera offline</div> : null}
        </div>

        <div className="control-grid">
          <label className="stacked-field">
            <span>Camera source</span>
            <select
              value={selectedCameraId}
              onChange={(event) => setSelectedCameraId(event.target.value)}
              disabled={cameraActive}
            >
              {cameraDevices.length === 0 ? <option value="">No camera found</option> : null}
              {cameraDevices.map((device, index) => (
                <option key={device.deviceId || index} value={device.deviceId}>
                  {device.label || `Camera ${index + 1}`}
                </option>
              ))}
            </select>
          </label>

          <button
            className="primary-button"
            type="button"
            onClick={cameraActive ? stopCamera : startCamera}
          >
            {cameraActive ? "Stop camera" : "Start camera"}
          </button>

          <button className="outline-button" type="button" onClick={captureSnapshotFromCamera}>
            Snapshot from live view
          </button>

          <button
            className="outline-button"
            type="button"
            onClick={() =>
              onUpdatePreferences?.((prev) => ({
                ...prev,
                voiceEnabled: !(prev?.voiceEnabled ?? true),
              }))
            }
          >
            Voice {voiceEnabled ? "on" : "off"}
          </button>

          <button
            className="outline-button"
            type="button"
            onClick={() => {
              if (preferences?.preferredRealtimeMode === "rest") {
                isRestStreaming ? stopRestRealtime() : startRestCoach();
              } else {
                isStreaming ? stopRealtime() : startRealtime();
              }
            }}
          >
            {preferences?.preferredRealtimeMode === "rest"
              ? isRestStreaming
                ? "Stop preferred stream"
                : "Start preferred stream"
              : isStreaming
                ? "Stop preferred stream"
                : "Start preferred stream"}
          </button>

          <button
            className="outline-button"
            type="button"
            onClick={isStreaming ? stopRealtime : startRealtime}
          >
            {isStreaming ? "Stop WebSocket" : "Start WebSocket"}
          </button>

          <button
            className="outline-button"
            type="button"
            onClick={isRestStreaming ? stopRestRealtime : startRestCoach}
          >
            {isRestStreaming ? "Stop REST" : "Start REST"}
          </button>

          <button className="outline-button" type="button" onClick={resetSession}>
            Reset session
          </button>
        </div>

        {cameraError ? <div className="form-error">{cameraError}</div> : null}
        {liveError ? <div className="form-error">{liveError}</div> : null}

        <div className="coach-feedback-grid">
          <article className={`coach-state ${coachTone(latestPayload)}`}>
            <div className="coach-state-head">
              <span>{guidedMode ? toneLabel(latestPayload) : "Pose identification"}</span>
              <strong>{latestPayload?.pose_name || effectiveSelectedPose || "Waiting for pose"}</strong>
            </div>
            <p>{primaryCoachMessage}</p>
            <div className="coach-cues">
              {coachMessages
                .slice(0, guidedMode ? 3 : 4)
                .map((message) => (
                <span key={message}>{message}</span>
              ))}
            </div>
          </article>

          <article className="coach-metrics">
            <div className="metric-block">
              <span>Confidence</span>
              <strong>
                {latestPayload?.confidence
                  ? `${(latestPayload.confidence * 100).toFixed(1)}%`
                  : "--"}
              </strong>
            </div>
            <div className="metric-block">
              <span>Latency</span>
              <strong>{metrics?.avg_latency_ms ? `${metrics.avg_latency_ms} ms` : "--"}</strong>
            </div>
            <div className="metric-block">
              <span>Time to correct</span>
              <strong>
                {metrics?.avg_time_to_correct_s
                  ? `${metrics.avg_time_to_correct_s}s`
                  : "--"}
              </strong>
            </div>
            <div className="metric-block">
              <span>False alerts / min</span>
              <strong>
                {metrics?.false_alerts_per_min !== undefined
                  ? metrics.false_alerts_per_min
                  : "--"}
              </strong>
            </div>
          </article>

          <article className="quality-panel">
            <div className="quality-line">
              <span>Full body visible</span>
              <strong>{quality.full_body_visible ? "Yes" : "No"}</strong>
            </div>
            <div className="quality-line">
              <span>Visibility score</span>
              <strong>{quality.visibility_score ?? "--"}</strong>
            </div>
            <div className="quality-line">
              <span>Center offset</span>
              <strong>{quality.center_offset ?? "--"}</strong>
            </div>
            <div className="quality-line">
              <span>Lighting</span>
              <strong>{quality.lighting_score ?? "--"}</strong>
            </div>
          </article>
        </div>

        <div className="coach-secondary-grid">
          {guidedMode ? (
            <div className="audio-coach-card coach-tool-card">
              <div className="section-kicker">Audio coach</div>
              <h3>Personalized narration</h3>
              <p className="guide-focus">
                Hear setup steps, breath cues, hold prompts, and routine transitions read aloud like a guided coach.
              </p>

              <div className="audio-status-row">
                <span>{audioCoachState.stage}</span>
                <span>
                  {audioCoachState.running
                    ? `${audioCoachState.poseIndex}/${audioCoachState.totalPoses || 1}`
                    : ttsPlaybackAvailable
                      ? ttsStatus.available
                        ? "AI voice ready"
                        : "Browser fallback ready"
                      : "Voice unavailable"}
                </span>
                {holdCountdown !== null ? <span>{holdCountdown}s left</span> : null}
              </div>

              <div className="audio-progress-note">{audioCoachState.message}</div>

              <div className="audio-button-grid">
                <button
                  className="primary-button"
                  type="button"
                  onClick={startSelectedAudioCoach}
                  disabled={!activeGuide}
                >
                  Narrate selected pose
                </button>
                <button
                  className="outline-button"
                  type="button"
                  onClick={startRoutineAudioCoach}
                  disabled={!routinePoseOptions.length}
                >
                  Play guided routine
                </button>
                <button
                  className="outline-button"
                  type="button"
                  onClick={() => stopAudioCoach()}
                  disabled={!audioCoachState.running}
                >
                  Stop audio coach
                </button>
              </div>

              <div className="audio-coach-note">
                While narrated guidance is running, live correction stays visible on screen and spoken correction resumes after the guide stops. The routine narration follows the best-fit subset, while the pose picker still lets you target any ranked dataset pose.
              </div>
            </div>
          ) : (
            <div className="audio-coach-card coach-tool-card silent-mode-card">
              <div className="section-kicker">Silent mode</div>
              <h3>Correction and pose ID only</h3>
              <p className="guide-focus">
                Audio narration is skipped here. The app will identify the detected pose, show corrections, and keep the overlay active while you practice independently.
              </p>
              <div className="audio-status-row">
                <span>Visual correction only</span>
                <span>{latestPayload?.pose_name || "Pose not detected yet"}</span>
              </div>
              <div className="audio-progress-note">
                Keep the camera running and watch the detected pose name, confidence, and correction messages update in real time.
              </div>
            </div>
          )}

          <div className="snapshot-block coach-tool-card">
            <div className="section-kicker">Snapshot analysis</div>
            <h3>Check a still frame before going live.</h3>
            <div
              className="upload-surface"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                const file = event.dataTransfer.files?.[0];
                if (file) handleSnapshotSelection(file);
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                hidden
                onChange={(event) => handleSnapshotSelection(event.target.files?.[0])}
              />
              <span>Drop an image here or click to upload.</span>
            </div>

            {snapshotPreview ? (
              <img className="snapshot-preview" src={snapshotPreview} alt="Pose preview" />
            ) : null}

            <div className="inline-actions">
              <button
                className="primary-button"
                type="button"
                onClick={() => runSnapshotAnalysis()}
                disabled={snapshotLoading}
              >
                {snapshotLoading ? "Analyzing..." : "Analyze snapshot"}
              </button>
              <button className="outline-button" type="button" onClick={captureSnapshotFromCamera}>
                Capture from camera
              </button>
            </div>

            {snapshotError ? <div className="form-error">{snapshotError}</div> : null}
          </div>
        </div>
      </section>
    </div>
  );
}
