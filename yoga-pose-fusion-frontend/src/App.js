import React, {
  startTransition,
  useDeferredValue,
  useEffect,
  useMemo,
  useState,
} from "react";
import PoseClassifier from "./PoseClassifier";
import {
  isFirebaseConfigured,
  signInWithGoogle,
  signOutUser,
  subscribeToAuthChanges,
} from "./firebase";
import { fetchRecommendations } from "./services/api";
import "./App.css";

const USERS_KEY = "ypf_users_v2";
const SESSION_KEY = "ypf_session_v2";
const PREFS_KEY = "ypf_prefs_v2";
const DEFAULT_API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL?.trim() || "http://localhost:8000";

const defaultPrefs = {
  apiBaseUrl: DEFAULT_API_BASE_URL,
  voiceEnabled: true,
  voicePersona: "female",
  practiceMode: "guided",
  preferredRealtimeMode: "ws",
};

const defaultWellnessProfile = {
  age: "",
  experienceLevel: "beginner",
  sessionMinutes: 20,
  goals: ["mobility", "relaxation"],
  healthFactors: ["stress_relief"],
};

const HEALTH_OPTIONS = [
  { value: "stress_relief", label: "Stress relief" },
  { value: "back_pain", label: "Back comfort" },
  { value: "knee_sensitivity", label: "Knee sensitivity" },
  { value: "shoulder_tightness", label: "Shoulder tightness" },
  { value: "poor_posture", label: "Posture support" },
  { value: "balance_support", label: "Balance support" },
  { value: "core_strength", label: "Core strength" },
  { value: "low_energy", label: "Low energy" },
  { value: "stiff_hamstrings", label: "Hamstring mobility" },
  { value: "hip_tightness", label: "Hip mobility" },
];

const GOAL_OPTIONS = [
  { value: "mobility", label: "Mobility" },
  { value: "strength", label: "Strength" },
  { value: "balance", label: "Balance" },
  { value: "posture", label: "Posture" },
  { value: "relaxation", label: "Relaxation" },
  { value: "energy", label: "Energy" },
];

const EXPERIENCE_OPTIONS = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

const TABS = [
  { id: "journey", label: "Journey" },
  { id: "routine", label: "Routine" },
  { id: "live", label: "Live Coach" },
  { id: "settings", label: "Settings" },
];

function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

function createUserProfile() {
  return {
    wellnessProfile: { ...defaultWellnessProfile },
    recommendationPlan: null,
    selectedPose: "",
  };
}

function formatPlanTime(timestamp) {
  if (!timestamp) return "Not generated yet";
  return new Date(timestamp).toLocaleString();
}

function toggleChoice(values, nextValue) {
  if (values.includes(nextValue)) {
    return values.filter((value) => value !== nextValue);
  }
  return [...values, nextValue];
}

function normalizeAuthMessage(error) {
  switch (error?.code) {
    case "auth/popup-closed-by-user":
      return "Google sign-in was closed before it finished.";
    case "auth/popup-blocked":
      return "Your browser blocked the Google sign-in popup.";
    case "auth/cancelled-popup-request":
      return "A sign-in popup is already open.";
    default:
      return error?.message || "Unable to sign in right now.";
  }
}

function ChoiceGrid({ options, selectedValues, onToggle }) {
  return (
    <div className="choice-grid">
      {options.map((option) => {
        const selected = selectedValues.includes(option.value);
        return (
          <button
            key={option.value}
            className={`choice-pill ${selected ? "selected" : ""}`}
            type="button"
            onClick={() => onToggle(option.value)}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

function PublicSection({
  authMode,
  setAuthMode,
  loginForm,
  setLoginForm,
  registerForm,
  setRegisterForm,
  onLogin,
  onRegister,
  onGoogleAuth,
  authError,
  authLoading,
}) {
  return (
    <div className="public-shell">
      <header className="site-nav">
        <div className="brand-lockup">
          <span className="brand-mark">YPF</span>
          <div>
            <div className="brand-name">YogaPoseFusion</div>
            <div className="brand-tag">Personalized yoga planning and live correction</div>
          </div>
        </div>
        <div className="nav-actions">
          <button
            className={`ghost-pill ${authMode === "login" ? "active" : ""}`}
            onClick={() => setAuthMode("login")}
            type="button"
          >
            Login
          </button>
          <button
            className={`ghost-pill ${authMode === "register" ? "active" : ""}`}
            onClick={() => setAuthMode("register")}
            type="button"
          >
            Create account
          </button>
        </div>
      </header>

      <main className="public-main">
        <section className="hero-stage">
          <div className="hero-copy">
            <div className="eyebrow">Yoga coaching that starts with your body, not a generic routine</div>
            <h1>Get age-aware asana recommendations and real-time correction in one flow.</h1>
            <p className="hero-description">
              Build a routine from your age, energy, posture needs, and mobility limits, then step into live coaching that tells you what to change and whether you are actually holding the intended pose.
            </p>
            <div className="hero-proof">
              <span>Age and health-factor intake</span>
              <span>Step-by-step asana instructions</span>
              <span>Live pose validation and correction</span>
            </div>
            <div className="hero-storyline">
              <div>
                <strong>01</strong>
                <p>Capture health factors, goals, and practice level.</p>
              </div>
              <div>
                <strong>02</strong>
                <p>Generate a coachable routine with hold times and modifications.</p>
              </div>
              <div>
                <strong>03</strong>
                <p>Use the live coach to confirm the pose and correct alignment.</p>
              </div>
            </div>
          </div>

          <div className="hero-visual">
            <div className="hero-orbit">
              <div className="orbit-disc orbit-primary" />
              <div className="orbit-disc orbit-secondary" />
              <div className="orbit-center">
                <span>Assess</span>
                <span>Recommend</span>
                <span>Correct</span>
              </div>
              <div className="orbit-note orbit-note-top">Live alignment cues</div>
              <div className="orbit-note orbit-note-right">Pose-specific instructions</div>
              <div className="orbit-note orbit-note-bottom">Age-aware routine shaping</div>
            </div>

            <div className="auth-panel">
              <div className="panel-kicker">Start your guided practice</div>
              <div className="panel-switch">
                <button
                  className={`ghost-pill ${authMode === "login" ? "active" : ""}`}
                  onClick={() => setAuthMode("login")}
                  type="button"
                >
                  Login
                </button>
                <button
                  className={`ghost-pill ${authMode === "register" ? "active" : ""}`}
                  onClick={() => setAuthMode("register")}
                  type="button"
                >
                  Register
                </button>
              </div>

              <div className="auth-form">
                {authMode === "login" ? (
                  <form className="auth-form" onSubmit={onLogin}>
                    <label>Email</label>
                    <input
                      type="email"
                      value={loginForm.email}
                      onChange={(event) =>
                        setLoginForm((prev) => ({ ...prev, email: event.target.value }))
                      }
                      required
                    />
                    <label>Password</label>
                    <input
                      type="password"
                      value={loginForm.password}
                      onChange={(event) =>
                        setLoginForm((prev) => ({ ...prev, password: event.target.value }))
                      }
                      required
                    />
                    <button className="primary-button" type="submit">
                      Enter dashboard
                    </button>
                  </form>
                ) : (
                  <form className="auth-form" onSubmit={onRegister}>
                    <label>Name</label>
                    <input
                      type="text"
                      value={registerForm.name}
                      onChange={(event) =>
                        setRegisterForm((prev) => ({ ...prev, name: event.target.value }))
                      }
                      required
                    />
                    <label>Email</label>
                    <input
                      type="email"
                      value={registerForm.email}
                      onChange={(event) =>
                        setRegisterForm((prev) => ({ ...prev, email: event.target.value }))
                      }
                      required
                    />
                    <label>Password</label>
                    <input
                      type="password"
                      value={registerForm.password}
                      onChange={(event) =>
                        setRegisterForm((prev) => ({ ...prev, password: event.target.value }))
                      }
                      required
                    />
                    <label>Confirm password</label>
                    <input
                      type="password"
                      value={registerForm.confirmPassword}
                      onChange={(event) =>
                        setRegisterForm((prev) => ({
                          ...prev,
                          confirmPassword: event.target.value,
                        }))
                      }
                      required
                    />
                    <button className="primary-button" type="submit">
                      Create account
                    </button>
                  </form>
                )}

                <div className="auth-divider">
                  <span>or</span>
                </div>

                <div className="auth-intro">
                  <strong>
                    {authMode === "login"
                      ? "Use Google for a faster sign-in."
                      : "Create your account with Google in one step."}
                  </strong>
                  <p>
                    Google sign-in keeps sessions more reliable than local passwords and
                    makes it easier to move between devices.
                  </p>
                </div>

                <button
                  className="primary-button google-auth-button"
                  onClick={onGoogleAuth}
                  type="button"
                  disabled={authLoading || !isFirebaseConfigured}
                >
                  <span className="google-mark" aria-hidden="true">
                    G
                  </span>
                  {authLoading
                    ? "Connecting to Google..."
                    : authMode === "login"
                      ? "Continue with Google"
                      : "Register with Google"}
                </button>

                {!isFirebaseConfigured ? (
                  <div className="auth-helper">
                    Firebase is not configured yet. Add the Firebase environment variables
                    to enable Google sign-in.
                  </div>
                ) : null}
              </div>

              {authError ? <div className="form-error">{authError}</div> : null}
            </div>
          </div>
        </section>

        <section className="insight-strip">
          <article>
            <h2>Recommendation engine</h2>
            <p>Chooses coachable poses that match posture, mobility, balance, energy, and joint sensitivity needs.</p>
          </article>
          <article>
            <h2>Instruction-first practice</h2>
            <p>Every suggested asana includes setup steps, breath cues, mistakes to avoid, and easy modifications.</p>
          </article>
          <article>
            <h2>Target-aware correction</h2>
            <p>The live coach can tell whether you are in the intended pose, need alignment fixes, or need to switch back.</p>
          </article>
        </section>
      </main>
    </div>
  );
}

function RecommendationDeck({ plan, selectedPose, onSelectPose, onStartLive }) {
  const [searchValue, setSearchValue] = useState("");
  const [libraryScope, setLibraryScope] = useState("all");
  const deferredSearch = useDeferredValue(searchValue);

  const featuredRecommendations = useMemo(
    () => plan?.featured_recommendations || [],
    [plan]
  );
  const allRecommendations = useMemo(
    () => plan?.recommendations || [],
    [plan]
  );

  const visibleRecommendations = useMemo(() => {
    const query = deferredSearch.trim().toLowerCase();
    const source =
      libraryScope === "featured" ? featuredRecommendations : allRecommendations;

    if (!query) {
      return source;
    }

    return source.filter((pose) => {
      const haystack = [
        pose.pose_name,
        pose.sanskrit_name,
        pose.difficulty,
        pose.intensity,
        ...(pose.movement_families || []),
        ...(pose.matched_goals || []),
        ...(pose.matched_health_factors || []),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [allRecommendations, deferredSearch, featuredRecommendations, libraryScope]);

  if (!allRecommendations.length) {
    return (
      <section className="empty-state">
        <h2>No routine yet</h2>
        <p>Fill out your practice profile in Journey to generate an age-aware routine.</p>
      </section>
    );
  }

  return (
    <section className="routine-grid">
      <div className="routine-head">
        <div>
          <div className="section-kicker">Your guided plan</div>
          <h2>{plan.summary.focus_message}</h2>
          <p>Last updated {formatPlanTime(plan.generatedAt)}</p>
        </div>
        <div className="routine-meta">
          <span>{plan.summary.session_minutes} minute session</span>
          <span>{featuredRecommendations.length} best-fit routine poses</span>
          <span>{allRecommendations.length} ranked dataset poses</span>
        </div>
      </div>

      <div className="routine-section-head">
        <div>
          <div className="section-kicker">Best-fit routine</div>
          <h3>These are the strongest matches for guided practice right now.</h3>
        </div>
        <p>The highlighted routine stays manageable for live practice, while the full ranked library below still includes the complete Yoga-82 catalog.</p>
      </div>

      <div className="pose-deck">
        {featuredRecommendations.map((pose, index) => {
          const active = selectedPose === pose.pose_name;
          return (
            <article
              key={`featured-${pose.pose_name}`}
              className={`pose-card ${active ? "active" : ""}`}
            >
              <div className="pose-card-head">
                <div>
                  <span className="pose-sequence">{String(index + 1).padStart(2, "0")}</span>
                  <h3>{pose.pose_name}</h3>
                  <p>{pose.sanskrit_name}</p>
                </div>
                <button
                  className="outline-button"
                  type="button"
                  onClick={() => onSelectPose(pose.pose_name)}
                >
                  {active ? "Selected" : "Select"}
                </button>
              </div>

              <div className="pose-meta-row">
                <span>{pose.difficulty}</span>
                <span>{pose.hold_seconds}s hold</span>
                <span>{pose.repetitions} rounds</span>
                <span>Rank #{pose.ranking_position}</span>
              </div>

              <p className="pose-why">{pose.why_selected}</p>

              {(pose.matched_goals?.length || pose.matched_health_factors?.length) ? (
                <div className="match-chip-row">
                  {pose.matched_goals.map((goal) => (
                    <span key={`${pose.pose_name}-${goal}`}>{goal}</span>
                  ))}
                  {pose.matched_health_factors.map((factor) => (
                    <span key={`${pose.pose_name}-${factor}`}>{factor}</span>
                  ))}
                </div>
              ) : null}

              <div className="pose-columns">
                <div>
                  <strong>Instructions</strong>
                  <ol>
                    {pose.instructions.map((instruction) => (
                      <li key={instruction}>{instruction}</li>
                    ))}
                  </ol>
                </div>
                <div>
                  <strong>Coach looks for</strong>
                  <p>{pose.coach_focus}</p>
                  <strong>Common slips</strong>
                  <ul>
                    {pose.common_mistakes.slice(0, 3).map((mistake) => (
                      <li key={mistake}>{mistake}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="pose-actions">
                <button
                  className="primary-button"
                  type="button"
                  onClick={() => {
                    onSelectPose(pose.pose_name);
                    onStartLive();
                  }}
                >
                  Practice in Live Coach
                </button>
              </div>
            </article>
          );
        })}
      </div>

      <div className="routine-section-head library-head">
        <div>
          <div className="section-kicker">Full ranked library</div>
          <h3>Browse every pose from the Yoga-82 dataset, ranked to the current user profile.</h3>
        </div>
        <p>Search by pose, goal, health factor, movement family, or difficulty. Select any pose to send it to Live Coach.</p>
      </div>

      <div className="library-toolbar">
        <label className="stacked-field library-search">
          <span>Search poses</span>
          <input
            type="text"
            value={searchValue}
            onChange={(event) => setSearchValue(event.target.value)}
            placeholder="Try: balance, back comfort, warrior, hamstring..."
          />
        </label>

        <div className="library-filter-block">
          <span>Library scope</span>
          <div className="segmented-row">
            <button
              className={`ghost-pill ${libraryScope === "all" ? "active" : ""}`}
              onClick={() => setLibraryScope("all")}
              type="button"
            >
              All {allRecommendations.length}
            </button>
            <button
              className={`ghost-pill ${libraryScope === "featured" ? "active" : ""}`}
              onClick={() => setLibraryScope("featured")}
              type="button"
            >
              Best-fit {featuredRecommendations.length}
            </button>
          </div>
        </div>
      </div>

      <div className="pose-library">
        {visibleRecommendations.map((pose) => {
          const active = selectedPose === pose.pose_name;
          return (
            <article
              key={`library-${pose.pose_name}`}
              className={`pose-library-row ${active ? "active" : ""}`}
            >
              <div className="pose-library-main">
                <div className="pose-library-title">
                  <span className="pose-sequence">
                    #{String(pose.ranking_position).padStart(2, "0")}
                  </span>
                  <div>
                    <h4>{pose.pose_name}</h4>
                    <p>{pose.sanskrit_name || "Dataset pose"}</p>
                  </div>
                </div>

                <div className="pose-library-meta">
                  <span>{pose.difficulty}</span>
                  <span>{pose.intensity}</span>
                  <span>{pose.hold_seconds}s hold</span>
                  {(pose.movement_families || []).slice(0, 2).map((family) => (
                    <span key={`${pose.pose_name}-${family}`}>{family.replace(/_/g, " ")}</span>
                  ))}
                </div>
              </div>

              <div className="pose-library-actions">
                <button
                  className="outline-button"
                  type="button"
                  onClick={() => onSelectPose(pose.pose_name)}
                >
                  {active ? "Selected" : "Select"}
                </button>
                <button
                  className="primary-button"
                  type="button"
                  onClick={() => {
                    onSelectPose(pose.pose_name);
                    onStartLive();
                  }}
                >
                  Live Coach
                </button>
              </div>

              <p className="pose-why">{pose.why_selected}</p>

              {(pose.matched_goals?.length || pose.matched_health_factors?.length) ? (
                <div className="match-chip-row">
                  {pose.matched_goals.map((goal) => (
                    <span key={`${pose.pose_name}-goal-${goal}`}>{goal}</span>
                  ))}
                  {pose.matched_health_factors.map((factor) => (
                    <span key={`${pose.pose_name}-health-${factor}`}>{factor}</span>
                  ))}
                </div>
              ) : null}

              {active ? (
                <div className="pose-library-details">
                  <div className="pose-columns">
                    <div>
                      <strong>Instructions</strong>
                      <ol>
                        {pose.instructions.map((instruction) => (
                          <li key={instruction}>{instruction}</li>
                        ))}
                      </ol>
                    </div>
                    <div>
                      <strong>Coach looks for</strong>
                      <p>{pose.coach_focus}</p>
                      <strong>Common slips</strong>
                      <ul>
                        {pose.common_mistakes.slice(0, 3).map((mistake) => (
                          <li key={mistake}>{mistake}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ) : null}
            </article>
          );
        })}

        {visibleRecommendations.length === 0 ? (
          <div className="empty-state">
            <h2>No matches</h2>
            <p>Try a broader search term or switch back to the full ranked library.</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}

export default function App() {
  const [users, setUsers] = useState(() => readJson(USERS_KEY, []));
  const [session, setSession] = useState(() => readJson(SESSION_KEY, null));
  const [prefs, setPrefs] = useState(() => ({ ...defaultPrefs, ...readJson(PREFS_KEY, {}) }));
  const [authMode, setAuthMode] = useState("login");
  const [activeTab, setActiveTab] = useState("journey");
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [recommendationError, setRecommendationError] = useState("");
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [registerForm, setRegisterForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  useEffect(() => {
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
  }, [users]);

  useEffect(() => {
    if (session) {
      localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    } else {
      localStorage.removeItem(SESSION_KEY);
    }
  }, [session]);

  useEffect(() => {
    localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
  }, [prefs]);

  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges((firebaseUser) => {
      setSession((prev) => {
        if (!firebaseUser?.email) {
          return prev?.authProvider === "google" ? null : prev;
        }

        const nextSession = {
          email: firebaseUser.email,
          name: firebaseUser.displayName || firebaseUser.email.split("@")[0],
          photoURL: firebaseUser.photoURL || "",
          authProvider: "google",
        };

        if (
          prev?.email === nextSession.email &&
          prev?.name === nextSession.name &&
          prev?.photoURL === nextSession.photoURL
        ) {
          return prev;
        }

        return nextSession;
      });

      if (!firebaseUser?.email) {
        return;
      }

      setUsers((prevUsers) => {
        const existingUser = prevUsers.find(
          (user) => user.email.toLowerCase() === firebaseUser.email.toLowerCase()
        );

        if (existingUser) {
          return prevUsers.map((user) =>
            user.email.toLowerCase() === firebaseUser.email.toLowerCase()
              ? {
                  ...user,
                  name:
                    firebaseUser.displayName ||
                    user.name ||
                    firebaseUser.email.split("@")[0],
                  photoURL: firebaseUser.photoURL || user.photoURL || "",
                }
              : user
          );
        }

        return [
          ...prevUsers,
          {
            name: firebaseUser.displayName || firebaseUser.email.split("@")[0],
            email: firebaseUser.email,
            createdAt: Date.now(),
            photoURL: firebaseUser.photoURL || "",
            authProvider: "google",
            ...createUserProfile(),
          },
        ];
      });
    });

    return unsubscribe;
  }, []);

  const currentUser = useMemo(() => {
    if (!session?.email) return null;
    return users.find((user) => user.email === session.email) || null;
  }, [session, users]);

  useEffect(() => {
    if (session?.email && !currentUser) {
      setSession(null);
    }
  }, [currentUser, session]);

  const wellnessProfile = currentUser?.wellnessProfile || defaultWellnessProfile;
  const recommendationPlan = currentUser?.recommendationPlan || null;
  const selectedPose =
    currentUser?.selectedPose ||
    recommendationPlan?.featured_recommendations?.[0]?.pose_name ||
    recommendationPlan?.recommendations?.[0]?.pose_name ||
    "";

  const updateCurrentUser = (updater) => {
    if (!currentUser) return;
    setUsers((prevUsers) =>
      prevUsers.map((user) => {
        if (user.email !== currentUser.email) return user;
        return typeof updater === "function" ? updater(user) : { ...user, ...updater };
      })
    );
  };

  const handleRegister = (event) => {
    event.preventDefault();
    setAuthError("");

    const { name, email, password, confirmPassword } = registerForm;
    if (!name || !email || !password || !confirmPassword) {
      setAuthError("Please complete every registration field.");
      return;
    }
    if (password !== confirmPassword) {
      setAuthError("Passwords do not match.");
      return;
    }
    if (users.some((user) => user.email.toLowerCase() === email.toLowerCase())) {
      setAuthError("That email is already in use.");
      return;
    }

    const createdUser = {
      name,
      email,
      password,
      createdAt: Date.now(),
      authProvider: "local",
      ...createUserProfile(),
    };

    setUsers((prev) => [...prev, createdUser]);
    setSession({ email, name, authProvider: "local" });
    setActiveTab("journey");
    setRegisterForm({
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
    });
  };

  const handleLogin = (event) => {
    event.preventDefault();
    setAuthError("");

    const matchedUser = users.find(
      (user) =>
        user.email.toLowerCase() === loginForm.email.toLowerCase() &&
        user.password === loginForm.password
    );

    if (!matchedUser) {
      setAuthError("Invalid email or password.");
      return;
    }

    setSession({
      email: matchedUser.email,
      name: matchedUser.name,
      photoURL: matchedUser.photoURL || "",
      authProvider: matchedUser.authProvider || "local",
    });
    setActiveTab("journey");
    setLoginForm({ email: "", password: "" });
  };

  const handleGoogleAuth = async () => {
    setAuthError("");
    setAuthLoading(true);

    try {
      await signInWithGoogle();
      setActiveTab("journey");
    } catch (error) {
      setAuthError(normalizeAuthMessage(error));
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = async () => {
    await signOutUser();
    setSession(null);
    setActiveTab("journey");
    setRecommendationError("");
  };

  const updateWellnessProfile = (patch) => {
    updateCurrentUser((user) => ({
      ...user,
      wellnessProfile: {
        ...defaultWellnessProfile,
        ...(user.wellnessProfile || {}),
        ...patch,
      },
    }));
  };

  const handleGenerateRecommendations = async () => {
    if (!currentUser) return;
    if (!wellnessProfile.age) {
      setRecommendationError("Add your age before generating a plan.");
      return;
    }

    setRecommendationError("");
    setRecommendationLoading(true);

    try {
      const payload = {
        age: Number(wellnessProfile.age),
        experience_level: wellnessProfile.experienceLevel,
        session_minutes: Number(wellnessProfile.sessionMinutes),
        goals: wellnessProfile.goals,
        health_factors: wellnessProfile.healthFactors,
      };

      const plan = await fetchRecommendations(prefs.apiBaseUrl, payload);
      const firstPose =
        plan.featured_recommendations?.[0]?.pose_name ||
        plan.recommendations?.[0]?.pose_name ||
        "";

      startTransition(() => {
        updateCurrentUser((user) => ({
          ...user,
          recommendationPlan: {
            ...plan,
            generatedAt: Date.now(),
          },
          selectedPose: user.selectedPose || firstPose,
        }));
        setActiveTab("routine");
      });
    } catch (error) {
      setRecommendationError(error.message);
    } finally {
      setRecommendationLoading(false);
    }
  };

  const handleSelectPose = (poseName) => {
    updateCurrentUser({ selectedPose: poseName });
  };

  if (!session || !currentUser) {
    return (
      <PublicSection
        authMode={authMode}
        setAuthMode={setAuthMode}
        loginForm={loginForm}
        setLoginForm={setLoginForm}
        registerForm={registerForm}
        setRegisterForm={setRegisterForm}
        onLogin={handleLogin}
        onRegister={handleRegister}
        onGoogleAuth={handleGoogleAuth}
        authError={authError}
        authLoading={authLoading}
      />
    );
  }

  return (
    <div className="dashboard-shell">
      <header className="dashboard-topbar">
        <div className="brand-lockup">
          <span className="brand-mark">YPF</span>
          <div>
            <div className="brand-name">YogaPoseFusion</div>
            <div className="brand-tag">Welcome back, {currentUser.name}</div>
          </div>
        </div>

        <nav className="workspace-nav">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`ghost-pill ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
              type="button"
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <button className="outline-button" onClick={handleLogout} type="button">
          Logout
        </button>
      </header>

      <section className="dashboard-hero">
        <div>
          <div className="section-kicker">Practice dashboard</div>
          <h1>Plan your practice, then let the camera coach the pose you actually want to hold.</h1>
          <p>
            Build a personalized routine around your age, current needs, and energy level, then move into Live Coach for target-aware posture correction.
          </p>
        </div>

        <div className="hero-summary">
          <div>
            <span>Selected pose</span>
            <strong>{selectedPose || "Choose from your routine"}</strong>
          </div>
          <div>
            <span>Routine updated</span>
            <strong>{formatPlanTime(recommendationPlan?.generatedAt)}</strong>
          </div>
          <div>
            <span>Session length</span>
            <strong>{wellnessProfile.sessionMinutes} min</strong>
          </div>
        </div>
      </section>

      <main className="dashboard-main">
        {activeTab === "journey" ? (
          <section className="workspace-grid">
            <article className="studio-panel">
              <div className="section-kicker">Profile intake</div>
              <h2>Shape the practice around the user, not the average session.</h2>
              <p className="panel-lead">
                These details drive recommendation ranking and help the live coach stay relevant to what the user is trying to practice.
              </p>

              <div className="form-grid">
                <label>
                  Age
                  <input
                    type="number"
                    min="5"
                    max="100"
                    value={wellnessProfile.age}
                    onChange={(event) => updateWellnessProfile({ age: event.target.value })}
                  />
                </label>

                <label>
                  Session length
                  <input
                    type="number"
                    min="10"
                    max="45"
                    step="5"
                    value={wellnessProfile.sessionMinutes}
                    onChange={(event) =>
                      updateWellnessProfile({ sessionMinutes: event.target.value })
                    }
                  />
                </label>
              </div>

              <div className="field-block">
                <strong>Experience level</strong>
                <div className="segmented-row">
                  {EXPERIENCE_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      className={`ghost-pill ${
                        wellnessProfile.experienceLevel === option.value ? "active" : ""
                      }`}
                      type="button"
                      onClick={() => updateWellnessProfile({ experienceLevel: option.value })}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="field-block">
                <strong>Current health factors</strong>
                <ChoiceGrid
                  options={HEALTH_OPTIONS}
                  selectedValues={wellnessProfile.healthFactors}
                  onToggle={(value) =>
                    updateWellnessProfile({
                      healthFactors: toggleChoice(wellnessProfile.healthFactors, value),
                    })
                  }
                />
              </div>

              <div className="field-block">
                <strong>Practice goals</strong>
                <ChoiceGrid
                  options={GOAL_OPTIONS}
                  selectedValues={wellnessProfile.goals}
                  onToggle={(value) =>
                    updateWellnessProfile({
                      goals: toggleChoice(wellnessProfile.goals, value),
                    })
                  }
                />
              </div>

              <div className="panel-actions">
                <button
                  className="primary-button"
                  type="button"
                  onClick={handleGenerateRecommendations}
                  disabled={recommendationLoading}
                >
                  {recommendationLoading ? "Building plan..." : "Generate personalized routine"}
                </button>
                {recommendationError ? <div className="form-error">{recommendationError}</div> : null}
              </div>
            </article>

            <aside className="studio-panel accent-panel">
              <div className="section-kicker">Readiness</div>
              <h2>What the system will use</h2>
              <ul className="signal-list">
                <li>Age band for intensity and hold-time shaping</li>
                <li>Health-factor matching for safer pose prioritization</li>
                <li>Goal tags for mobility, balance, posture, energy, or strength</li>
                <li>Live coach target pose so correction matches the intended asana</li>
              </ul>

              <div className="quick-summary">
                <span>{wellnessProfile.healthFactors.length} health factors selected</span>
                <span>{wellnessProfile.goals.length} goals selected</span>
                <span>{recommendationPlan?.available_pose_count || 0} dataset poses ranked</span>
              </div>

              <button
                className="outline-button"
                type="button"
                onClick={() => setActiveTab("routine")}
              >
                Review current routine
              </button>
            </aside>
          </section>
        ) : null}

        {activeTab === "routine" ? (
          <RecommendationDeck
            plan={recommendationPlan}
            selectedPose={selectedPose}
            onSelectPose={handleSelectPose}
            onStartLive={() => setActiveTab("live")}
          />
        ) : null}

        {activeTab === "live" ? (
          <PoseClassifier
            user={currentUser}
            preferences={prefs}
            onUpdatePreferences={setPrefs}
            recommendations={recommendationPlan?.recommendations || []}
            featuredRecommendations={recommendationPlan?.featured_recommendations || []}
            selectedPose={selectedPose}
            onSelectPose={handleSelectPose}
          />
        ) : null}

        {activeTab === "settings" ? (
          <section className="workspace-grid">
            <article className="studio-panel">
              <div className="section-kicker">Account</div>
              <h2>Profile and environment settings</h2>
              <div className="form-grid">
                <label>
                  Display name
                  <input
                    type="text"
                    value={currentUser.name}
                    onChange={(event) => updateCurrentUser({ name: event.target.value })}
                  />
                </label>
                <label>
                  Email
                  <input type="text" value={currentUser.email} disabled />
                </label>
              </div>

              <div className="field-block">
                <strong>API base URL</strong>
                <input
                  type="text"
                  value={prefs.apiBaseUrl}
                  onChange={(event) =>
                    setPrefs((prev) => ({ ...prev, apiBaseUrl: event.target.value }))
                  }
                />
              </div>

              <div className="field-block">
                <strong>Realtime mode</strong>
                <div className="segmented-row">
                  <button
                    className={`ghost-pill ${prefs.preferredRealtimeMode === "ws" ? "active" : ""}`}
                    onClick={() =>
                      setPrefs((prev) => ({ ...prev, preferredRealtimeMode: "ws" }))
                    }
                    type="button"
                  >
                    WebSocket
                  </button>
                  <button
                    className={`ghost-pill ${
                      prefs.preferredRealtimeMode === "rest" ? "active" : ""
                    }`}
                    onClick={() =>
                      setPrefs((prev) => ({ ...prev, preferredRealtimeMode: "rest" }))
                    }
                    type="button"
                  >
                    REST polling
                  </button>
                </div>
              </div>
            </article>

            <aside className="studio-panel accent-panel">
              <div className="section-kicker">Coaching preferences</div>
              <h2>Live feedback behavior</h2>
              <div className="field-block">
                <strong>Practice mode</strong>
                <div className="segmented-row">
                  <button
                    className={`ghost-pill ${prefs.practiceMode === "guided" ? "active" : ""}`}
                    onClick={() =>
                      setPrefs((prev) => ({ ...prev, practiceMode: "guided" }))
                    }
                    type="button"
                  >
                    Guided audio coach
                  </button>
                  <button
                    className={`ghost-pill ${prefs.practiceMode === "silent" ? "active" : ""}`}
                    onClick={() =>
                      setPrefs((prev) => ({ ...prev, practiceMode: "silent" }))
                    }
                    type="button"
                  >
                    Silent correction
                  </button>
                </div>
              </div>
              <div className="toggle-row">
                <span>Voice cues</span>
                <button
                  className={`ghost-pill ${prefs.voiceEnabled ? "active" : ""}`}
                  type="button"
                  onClick={() =>
                    setPrefs((prev) => ({ ...prev, voiceEnabled: !prev.voiceEnabled }))
                  }
                >
                  {prefs.voiceEnabled ? "Enabled" : "Disabled"}
                </button>
              </div>
              <div className="field-block">
                <strong>Voice style</strong>
                <div className="segmented-row">
                  <button
                    className={`ghost-pill ${prefs.voicePersona === "female" ? "active" : ""}`}
                    onClick={() =>
                      setPrefs((prev) => ({ ...prev, voicePersona: "female" }))
                    }
                    type="button"
                  >
                    Prefer female voice
                  </button>
                  <button
                    className={`ghost-pill ${prefs.voicePersona === "default" ? "active" : ""}`}
                    onClick={() =>
                      setPrefs((prev) => ({ ...prev, voicePersona: "default" }))
                    }
                    type="button"
                  >
                    System default
                  </button>
                </div>
              </div>
              <p className="panel-lead">
                Guided audio coach enables narration plus spoken correction cues. Silent correction keeps pose identification and visual correction only, unless voice cues are turned on. Female voice preference now targets the dedicated AI voice backend first, and falls back to a browser voice only if backend TTS is unavailable.
              </p>
            </aside>
          </section>
        ) : null}
      </main>
    </div>
  );
}
