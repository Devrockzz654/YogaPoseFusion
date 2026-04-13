import json
import os
import re
from typing import Optional

from models.pose_correction import normalize_pose_name


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", normalize_pose_name(value)).strip("_")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSE_MAPPING_PATH = os.path.join(BASE_DIR, "data", "processed", "idx_to_pose.json")
REFERENCE_IMAGE_DIR = os.path.join(BASE_DIR, "data", "reference_images")


HEALTH_FACTOR_LABELS = {
    "stress_relief": "Stress relief",
    "back_pain": "Back comfort",
    "knee_sensitivity": "Knee sensitivity",
    "shoulder_tightness": "Shoulder tightness",
    "poor_posture": "Posture support",
    "balance_support": "Balance support",
    "core_strength": "Core strength",
    "low_energy": "Low energy",
    "stiff_hamstrings": "Hamstring mobility",
    "hip_tightness": "Hip mobility",
}


GOAL_LABELS = {
    "mobility": "Mobility",
    "strength": "Strength",
    "balance": "Balance",
    "posture": "Posture",
    "relaxation": "Relaxation",
    "energy": "Energy",
}


DIFFICULTY_ORDER = {
    "Beginner": 0,
    "Intermediate": 1,
    "Advanced": 2,
}


EXPERIENCE_ORDER = {
    "beginner": 0,
    "intermediate": 1,
    "advanced": 2,
}


CURATED_POSES = [
    {
        "pose_name": "Child Pose",
        "sanskrit_name": "Balasana",
        "difficulty": "Beginner",
        "intensity": "Low",
        "aliases": [
            "child pose",
            "balasana",
            "child pose or balasana",
            "child_pose_or_balasana_",
        ],
        "goal_tags": ["mobility", "relaxation", "posture"],
        "health_support": ["stress_relief", "back_pain", "poor_posture", "hip_tightness"],
        "caution_tags": ["knee_sensitivity"],
        "movement_families": ["restorative", "kneeling", "hip_opener"],
        "benefits": [
            "Settles the nervous system",
            "Gently opens the hips and low back",
            "Creates a safe reset between stronger poses",
        ],
        "instructions": [
            "Start on all fours with knees slightly apart and big toes touching.",
            "Send your hips back toward your heels and lengthen your arms forward.",
            "Rest your forehead down and let your breath widen the back ribs.",
        ],
        "breath_cues": [
            "Inhale into the back body.",
            "Exhale and soften the shoulders and jaw.",
        ],
        "common_mistakes": [
            "Holding tension in the shoulders",
            "Forcing hips to heels instead of using support",
            "Shrinking the breath",
        ],
        "modifications": [
            "Place a folded blanket under the knees.",
            "Rest the chest on a bolster if the hips do not comfortably reach back.",
        ],
        "coach_focus": "Hip fold and relaxed shoulder line",
        "base_hold_seconds": 45,
        "repetitions": 2,
        "caution": "Use extra padding if your knees are sensitive.",
    },
    {
        "pose_name": "Cobra Pose",
        "sanskrit_name": "Bhujangasana",
        "difficulty": "Beginner",
        "intensity": "Low",
        "aliases": [
            "cobra pose",
            "bhujangasana",
            "cobra pose or bhujangasana",
            "cobra_pose_or_bhujangasana_",
        ],
        "goal_tags": ["mobility", "posture", "energy"],
        "health_support": ["back_pain", "poor_posture", "low_energy", "shoulder_tightness"],
        "caution_tags": [],
        "movement_families": ["backbend", "prone", "posture"],
        "benefits": [
            "Encourages thoracic extension",
            "Opens the chest after long sitting",
            "Builds awareness through the spine and shoulders",
        ],
        "instructions": [
            "Lie on your belly with hands beside the lower ribs and legs pressing into the mat.",
            "Draw the shoulders back and lift the chest using light support from the hands.",
            "Keep the neck long and the pubic bone grounded as you breathe steadily.",
        ],
        "breath_cues": [
            "Inhale to lengthen through the crown of the head.",
            "Exhale to soften the shoulders down the back.",
        ],
        "common_mistakes": [
            "Dumping into the low back",
            "Locking the elbows",
            "Shrugging the shoulders toward the ears",
        ],
        "modifications": [
            "Lift only to baby cobra height if the low back feels compressed.",
        ],
        "coach_focus": "Chest opening and shoulder position",
        "base_hold_seconds": 30,
        "repetitions": 3,
        "caution": "Stay in a smaller lift if your lower back feels pinchy.",
    },
    {
        "pose_name": "Bridge Pose",
        "sanskrit_name": "Setu Bandha Sarvangasana",
        "difficulty": "Beginner",
        "intensity": "Moderate",
        "aliases": [
            "bridge pose",
            "setu bandha sarvangasana",
            "bridge pose or setu bandha sarvangasana",
            "bridge_pose_or_setu_bandha_sarvangasana_",
        ],
        "goal_tags": ["strength", "posture", "mobility"],
        "health_support": ["back_pain", "poor_posture", "core_strength", "low_energy"],
        "caution_tags": ["knee_sensitivity"],
        "movement_families": ["backbend", "supine", "posture"],
        "benefits": [
            "Strengthens the posterior chain",
            "Supports a more open chest posture",
            "Builds glute and hamstring engagement",
        ],
        "instructions": [
            "Lie on your back, bend both knees, and place feet hip-width apart.",
            "Press through the feet and lift the hips until knees track over ankles.",
            "Keep the chest broad and lower slowly with control.",
        ],
        "breath_cues": [
            "Inhale as the hips lift.",
            "Exhale and keep the ribs steady instead of flaring.",
        ],
        "common_mistakes": [
            "Feet too far from the hips",
            "Knees splaying wide",
            "Overarching the lower back",
        ],
        "modifications": [
            "Place a yoga block under the sacrum for a supported bridge.",
        ],
        "coach_focus": "Hip lift and knee tracking",
        "base_hold_seconds": 35,
        "repetitions": 3,
        "caution": "Keep weight evenly distributed through both feet if the knees feel unstable.",
    },
    {
        "pose_name": "Chair Pose",
        "sanskrit_name": "Utkatasana",
        "difficulty": "Beginner",
        "intensity": "Moderate",
        "aliases": [
            "chair pose",
            "utkatasana",
            "chair pose or utkatasana",
            "chair_pose_or_utkatasana_",
        ],
        "goal_tags": ["strength", "posture", "energy"],
        "health_support": ["poor_posture", "core_strength", "low_energy"],
        "caution_tags": ["knee_sensitivity"],
        "movement_families": ["standing", "strength", "posture"],
        "benefits": [
            "Strengthens the legs and trunk",
            "Trains upright posture under load",
            "Creates full-body heat quickly",
        ],
        "instructions": [
            "Stand tall with feet hip-width apart and sit the hips back like you are reaching for a chair.",
            "Lift both arms overhead while keeping the ribs softly contained.",
            "Keep weight balanced through the heels and mid-foot as the knees bend.",
        ],
        "breath_cues": [
            "Inhale to lengthen the spine upward.",
            "Exhale to sit slightly deeper without collapsing the chest.",
        ],
        "common_mistakes": [
            "Knees drifting too far forward",
            "Arms dropping or shoulders hiking up",
            "Torso collapsing onto the thighs",
        ],
        "modifications": [
            "Keep hands at the heart if shoulders are tight.",
            "Reduce the depth if the knees are uncomfortable.",
        ],
        "coach_focus": "Knee bend depth and overhead reach",
        "base_hold_seconds": 25,
        "repetitions": 3,
        "caution": "Use a shallower squat range if your knees are sensitive.",
    },
    {
        "pose_name": "Tree Pose",
        "sanskrit_name": "Vrksasana",
        "difficulty": "Beginner",
        "intensity": "Low",
        "aliases": [
            "tree pose",
            "vrksasana",
            "tree pose or vrksasana",
            "tree_pose_or_vrksasana_",
        ],
        "goal_tags": ["balance", "posture", "relaxation"],
        "health_support": ["balance_support", "poor_posture", "stress_relief"],
        "caution_tags": ["knee_sensitivity"],
        "movement_families": ["standing", "balance", "posture"],
        "benefits": [
            "Improves single-leg balance",
            "Builds focus and postural control",
            "Strengthens the standing leg and hip stabilizers",
        ],
        "instructions": [
            "Stand tall and shift weight into one foot.",
            "Place the other foot to the inner ankle or inner calf and press foot and leg together.",
            "Bring hands to prayer or overhead while keeping the chest upright and gaze steady.",
        ],
        "breath_cues": [
            "Keep the breath slow and even to steady balance.",
        ],
        "common_mistakes": [
            "Foot pressing into the side of the knee joint",
            "Locking the standing knee",
            "Leaning the torso sideways",
        ],
        "modifications": [
            "Keep toes of the lifted foot lightly on the floor for support.",
            "Practice near a wall or chair for balance.",
        ],
        "coach_focus": "Hip opening and stacked standing posture",
        "base_hold_seconds": 30,
        "repetitions": 2,
        "caution": "Use wall support if balance feels uncertain.",
    },
    {
        "pose_name": "Warrior I Pose",
        "sanskrit_name": "Virabhadrasana I",
        "difficulty": "Beginner",
        "intensity": "Moderate",
        "aliases": [
            "warrior i pose",
            "virabhadrasana i",
            "warrior i pose or virabhadrasana i",
            "warrior_i_pose_or_virabhadrasana_i_",
        ],
        "goal_tags": ["strength", "balance", "posture"],
        "health_support": ["poor_posture", "balance_support", "low_energy"],
        "caution_tags": ["knee_sensitivity", "hip_tightness"],
        "movement_families": ["standing", "balance", "strength"],
        "benefits": [
            "Builds leg strength and pelvic stability",
            "Encourages an upright chest and strong reach",
            "Improves coordination between lower and upper body",
        ],
        "instructions": [
            "Step one foot back and turn the back toes slightly out.",
            "Bend the front knee while reaching both arms overhead.",
            "Square the chest forward as much as comfortable and press through the back leg.",
        ],
        "breath_cues": [
            "Inhale through the fingertips.",
            "Exhale to root through both feet.",
        ],
        "common_mistakes": [
            "Front knee collapsing inward",
            "Back heel losing pressure",
            "Overarching the low back to reach higher",
        ],
        "modifications": [
            "Shorten the stance if the hips feel strained.",
            "Keep hands at heart center if shoulders fatigue.",
        ],
        "coach_focus": "Front knee angle and overhead arm reach",
        "base_hold_seconds": 30,
        "repetitions": 2,
        "caution": "Shorten the stance if the hips or front knee feel overloaded.",
    },
    {
        "pose_name": "Warrior II Pose",
        "sanskrit_name": "Virabhadrasana II",
        "difficulty": "Beginner",
        "intensity": "Moderate",
        "aliases": [
            "warrior ii pose",
            "virabhadrasana ii",
            "warrior ii pose or virabhadrasana ii",
            "warrior_ii_pose_or_virabhadrasana_ii_",
        ],
        "goal_tags": ["strength", "balance", "posture"],
        "health_support": ["balance_support", "poor_posture", "core_strength"],
        "caution_tags": ["knee_sensitivity", "hip_tightness"],
        "movement_families": ["standing", "balance", "strength"],
        "benefits": [
            "Strengthens the front leg and trunk",
            "Improves spatial awareness through the shoulders and hips",
            "Supports confident standing posture",
        ],
        "instructions": [
            "Take a wide stance with front foot turned out and back foot slightly angled in.",
            "Bend the front knee over the ankle and stretch both arms long at shoulder height.",
            "Keep the torso centered between both legs and gaze softly over the front hand.",
        ],
        "breath_cues": [
            "Inhale to lengthen from fingertip to fingertip.",
            "Exhale to deepen into the front leg without gripping the shoulders.",
        ],
        "common_mistakes": [
            "Front knee drifting inside the big toe",
            "Arms dropping below shoulder height",
            "Torso leaning over the front thigh",
        ],
        "modifications": [
            "Reduce stance width if the legs fatigue too early.",
        ],
        "coach_focus": "Front knee bend and side-arm extension",
        "base_hold_seconds": 30,
        "repetitions": 2,
        "caution": "Work at a shorter stance if the knee or groin feels strained.",
    },
    {
        "pose_name": "Triangle Pose",
        "sanskrit_name": "Utthita Trikonasana",
        "difficulty": "Intermediate",
        "intensity": "Moderate",
        "aliases": [
            "triangle pose",
            "extended revolved triangle pose",
            "utthita trikonasana",
            "extended revolved triangle pose or utthita trikonasana",
            "extended_revolved_triangle_pose_or_utthita_trikonasana_",
        ],
        "goal_tags": ["mobility", "balance", "posture"],
        "health_support": ["stiff_hamstrings", "hip_tightness", "poor_posture"],
        "caution_tags": ["back_pain"],
        "movement_families": ["standing", "forward_fold", "balance"],
        "benefits": [
            "Opens the hamstrings and side body",
            "Builds stacked alignment awareness",
            "Strengthens through the legs while lengthening the torso",
        ],
        "instructions": [
            "Stand in a wide stance and straighten both legs without locking the knees.",
            "Reach forward from the front hip and lower one hand to shin or a block.",
            "Stack the shoulders and lift the top arm toward the ceiling while keeping the chest broad.",
        ],
        "breath_cues": [
            "Inhale to lengthen both sides of the waist.",
            "Exhale to root through both feet.",
        ],
        "common_mistakes": [
            "Collapsing onto the lower hand",
            "Rounding through the chest",
            "Hyperextending the knees",
        ],
        "modifications": [
            "Use a yoga block under the lower hand.",
            "Keep a small bend in the front knee if hamstrings are tight.",
        ],
        "coach_focus": "Straight legs and vertical shoulder stacking",
        "base_hold_seconds": 25,
        "repetitions": 2,
        "caution": "Use a block and keep the torso long if the back feels sensitive.",
    },
    {
        "pose_name": "Downward-Facing Dog",
        "sanskrit_name": "Adho Mukha Svanasana",
        "difficulty": "Beginner",
        "intensity": "Moderate",
        "aliases": [
            "downward facing dog",
            "downward-facing dog",
            "adho mukha svanasana",
            "downward facing dog pose or adho mukha svanasana",
            "downward-facing_dog_pose_or_adho_mukha_svanasana_",
        ],
        "goal_tags": ["mobility", "strength", "energy"],
        "health_support": ["stiff_hamstrings", "shoulder_tightness", "low_energy", "poor_posture"],
        "caution_tags": ["shoulder_tightness"],
        "movement_families": ["standing", "forward_fold", "shoulder_opener"],
        "benefits": [
            "Lengthens the back body",
            "Strengthens the shoulders and arms",
            "Resets the spine between stronger standing poses",
        ],
        "instructions": [
            "Start on hands and knees with fingers spread wide.",
            "Tuck the toes, lift the knees, and send the hips high to form an inverted V-shape.",
            "Press evenly through the hands, soften the knees if needed, and lengthen the spine.",
        ],
        "breath_cues": [
            "Inhale to lengthen the spine.",
            "Exhale to press the hips upward and back.",
        ],
        "common_mistakes": [
            "Rounded upper back from pushing too close to the hands",
            "Locked knees that shorten the spine",
            "Weight dumping into the wrists",
        ],
        "modifications": [
            "Bend the knees generously to prioritize a long spine.",
            "Elevate the hands on blocks if the shoulders need space.",
        ],
        "coach_focus": "Arm extension and hip lift",
        "base_hold_seconds": 30,
        "repetitions": 2,
        "caution": "Keep a bend in the knees and elevate the hands if shoulders feel crowded.",
    },
    {
        "pose_name": "Plank Pose",
        "sanskrit_name": "Kumbhakasana",
        "difficulty": "Intermediate",
        "intensity": "Moderate",
        "aliases": [
            "plank pose",
            "kumbhakasana",
            "plank pose or kumbhakasana",
            "plank_pose_or_kumbhakasana_",
        ],
        "goal_tags": ["strength", "posture"],
        "health_support": ["core_strength", "poor_posture", "low_energy"],
        "caution_tags": ["shoulder_tightness"],
        "movement_families": ["core", "strength", "shoulder_opener"],
        "benefits": [
            "Builds whole-body tension and core control",
            "Improves shoulder stability",
            "Supports trunk endurance for daily posture",
        ],
        "instructions": [
            "Set hands under shoulders and extend both legs back.",
            "Press the floor away and create one straight line from shoulders through heels.",
            "Keep the belly gently lifted so the hips do not sag or pike.",
        ],
        "breath_cues": [
            "Take short steady breaths without holding the breath.",
        ],
        "common_mistakes": [
            "Hips dropping below shoulder line",
            "Piking the hips too high",
            "Collapsing between the shoulder blades",
        ],
        "modifications": [
            "Lower the knees to the mat while keeping a straight line from head to knees.",
        ],
        "coach_focus": "Straight arm support and hip alignment",
        "base_hold_seconds": 20,
        "repetitions": 3,
        "caution": "Use knees-down plank if wrists or shoulders tire quickly.",
    },
    {
        "pose_name": "Boat Pose",
        "sanskrit_name": "Paripurna Navasana",
        "difficulty": "Intermediate",
        "intensity": "Moderate",
        "aliases": [
            "boat pose",
            "paripurna navasana",
            "boat pose or paripurna navasana",
            "boat_pose_or_paripurna_navasana_",
        ],
        "goal_tags": ["strength", "balance", "energy"],
        "health_support": ["core_strength", "low_energy"],
        "caution_tags": ["back_pain", "hip_tightness"],
        "movement_families": ["core", "seated", "balance"],
        "benefits": [
            "Challenges the deep core",
            "Improves seated balance and postural endurance",
            "Builds focus and steady breathing under effort",
        ],
        "instructions": [
            "Sit tall with knees bent and hands behind the thighs.",
            "Lean back slightly, lift the feet, and balance on the sitting bones.",
            "Optionally straighten the legs while keeping the chest lifted.",
        ],
        "breath_cues": [
            "Inhale to lengthen the chest.",
            "Exhale to draw the navel inward without rounding deeply.",
        ],
        "common_mistakes": [
            "Collapsing the chest backward",
            "Locking the knees before stabilizing the torso",
            "Holding the breath",
        ],
        "modifications": [
            "Keep knees bent and fingertips on the floor for light balance support.",
        ],
        "coach_focus": "Leg extension and chest lift",
        "base_hold_seconds": 20,
        "repetitions": 2,
        "caution": "Skip straight legs and hold the thighs if your low back feels strained.",
    },
]


ROMAN_NUMERAL_FIXES = {
    " Ii ": " II ",
    " Iii ": " III ",
    " Iv ": " IV ",
    " Vi ": " VI ",
    " Vii ": " VII ",
    " Viii ": " VIII ",
    " Ix ": " IX ",
    " Xi ": " XI ",
}


LOWERCASE_WORDS = {
    "or",
    "and",
    "of",
    "the",
    "to",
    "for",
    "with",
    "up",
}


def _listify(values):
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    return [value for value in values if value]


def _normalize_tags(values):
    return {_slug(str(value)) for value in _listify(values)}


def _age_band(age: int) -> str:
    if age < 18:
        return "teen"
    if age >= 60:
        return "senior"
    return "adult"


def _format_matches(values: list[str], label_map: dict[str, str]) -> list[str]:
    return [label_map.get(value, value.replace("_", " ").title()) for value in values]


def _hold_seconds(pose: dict, age: int, experience_level: str) -> int:
    hold = int(pose["base_hold_seconds"])
    if age >= 60:
        hold = max(15, hold - 5)
    if EXPERIENCE_ORDER.get(experience_level, 0) >= DIFFICULTY_ORDER.get(pose["difficulty"], 0):
        hold += 5
    return hold


def _repetitions(pose: dict, session_minutes: int) -> int:
    reps = int(pose["repetitions"])
    if session_minutes >= 35:
        return reps + 1
    if session_minutes <= 15:
        return max(1, reps - 1)
    return reps


def _load_dataset_pose_labels():
    if not os.path.exists(POSE_MAPPING_PATH):
        return []

    with open(POSE_MAPPING_PATH, "r", encoding="utf-8") as handle:
        mapping = json.load(handle)

    return [
        {"dataset_index": int(index), "dataset_label": label}
        for index, label in sorted(mapping.items(), key=lambda item: int(item[0]))
    ]


def _prettify_phrase(value: str) -> str:
    text = value.strip("_").replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    text = text.title()
    text = text.replace("( ", "(").replace(" )", ")")
    text = text.replace("-Facing", "-Facing")
    for source, target in ROMAN_NUMERAL_FIXES.items():
        text = text.replace(source, target)
    if text in {"I", "Ii", "Iii", "Iv", "V", "Vi", "Vii", "Viii", "Ix"}:
        return text.upper()

    words = []
    for index, word in enumerate(text.split(" ")):
        if word.lower() in LOWERCASE_WORDS and index != 0:
            words.append(word.lower())
        else:
            words.append(word)
    return " ".join(words)


def _split_display_names(raw_label: str):
    raw_parts = [part for part in raw_label.strip("_").split("_or_") if part]
    pretty_parts = [_prettify_phrase(part) for part in raw_parts]

    if not pretty_parts:
        return "Unknown Pose", ""
    if len(pretty_parts) == 1:
        return pretty_parts[0], ""

    left, right = pretty_parts[0], pretty_parts[1]
    left_has_pose = "pose" in normalize_pose_name(left)
    right_has_pose = "pose" in normalize_pose_name(right)

    if right_has_pose and not left_has_pose:
        return right, left
    return left, right


def _contains(text: str, *patterns: str) -> bool:
    return any(pattern in text for pattern in patterns)


def _movement_families(pose_name: str, sanskrit_name: str, raw_label: str):
    text = normalize_pose_name(" ".join([pose_name, sanskrit_name, raw_label]))
    families = []

    def add_family(name: str):
        if name not in families:
            families.append(name)

    if _contains(
        text,
        "child pose",
        "corpse pose",
        "legs up the wall",
        "yogic sleep",
        "happy baby",
        "wind relieving",
        "supta baddha konasana",
    ):
        add_family("restorative")

    if _contains(
        text,
        "twist",
        "revolved",
        "parivrtta",
        "bharadvaja",
        "matsyendrasana",
        "noose pose",
        "pasasana",
    ):
        add_family("twist")

    if _contains(
        text,
        "forward bend",
        "uttanasana",
        "paschimottanasana",
        "janu sirsasana",
        "parsvottanasana",
        "prasarita",
        "upavistha",
        "tortoise pose",
        "big toe hold",
        "split pose",
        "standing split",
        "heron pose",
        "akarna dhanurasana",
    ):
        add_family("forward_fold")

    if _contains(
        text,
        "bow pose",
        "cobra pose",
        "camel pose",
        "bridge pose",
        "fish pose",
        "locust pose",
        "wheel pose",
        "upward bow",
        "dwi pada viparita dandasana",
        "rajakapotasana",
        "pigeon pose",
        "natarajasana",
        "frog pose",
        "bhujangasana",
        "dhanurasana",
        "ustrasana",
        "matsyasana",
        "salabhasana",
    ):
        add_family("backbend")

    if _contains(
        text,
        "warrior",
        "chair pose",
        "triangle",
        "side angle",
        "half moon",
        "tree pose",
        "eagle pose",
        "lord of the dance",
        "standing forward bend",
        "standing split",
        "standing big toe hold",
        "reverse warrior",
        "intense side stretch",
        "low lunge",
        "garland pose",
        "parighasana",
    ):
        add_family("standing")

    if _contains(
        text,
        "tree pose",
        "eagle pose",
        "half moon",
        "warrior iii",
        "lord of the dance",
        "standing split",
        "big toe hold",
        "side plank",
        "anantasana",
    ):
        add_family("balance")

    if _contains(
        text,
        "plank pose",
        "boat pose",
        "scale pose",
        "cockerel pose",
        "side plank",
        "upward plank",
        "dolphin plank",
        "makara adho mukha svanasana",
    ):
        add_family("core")

    if _contains(
        text,
        "crow",
        "crane",
        "bakasana",
        "firefly",
        "tittibhasana",
        "peacock pose",
        "mayurasana",
        "cockerel pose",
        "scale pose",
        "tolasana",
        "eight angle",
        "astavakrasana",
        "koundinya",
        "bhujapidasana",
    ):
        add_family("arm_balance")

    if _contains(
        text,
        "handstand",
        "headstand",
        "shoulderstand",
        "feathered peacock",
        "scorpion",
        "pincha mayurasana",
        "sirsasana",
        "sarvangasana",
    ):
        add_family("inversion")

    if _contains(
        text,
        "pigeon pose",
        "kapotasana",
        "bound angle",
        "frog pose",
        "garland pose",
        "happy baby",
        "cow face pose",
        "gomukhasana",
        "split pose",
        "low lunge",
        "virasana",
        "vajrasana",
        "supta baddha konasana",
        "malasana",
        "baddha konasana",
    ):
        add_family("hip_opener")

    if _contains(
        text,
        "downward facing dog",
        "dolphin pose",
        "extended puppy",
        "cow face pose",
        "upward plank",
        "handstand",
        "feathered peacock",
    ):
        add_family("shoulder_opener")

    if _contains(
        text,
        "cat cow",
        "bridge pose",
        "cobra pose",
        "fish pose",
        "camel pose",
        "staff pose",
        "warrior i",
        "locust pose",
    ):
        add_family("posture")

    if _contains(
        text,
        "supta",
        "corpse pose",
        "legs up the wall",
        "happy baby",
        "wind relieving",
        "plow pose",
        "shoulderstand",
        "reclining",
        "yogic sleep",
    ):
        add_family("supine")

    if _contains(
        text,
        "cobra pose",
        "bow pose",
        "locust pose",
        "frog pose",
        "bhujangasana",
        "dhanurasana",
        "salabhasana",
    ):
        add_family("prone")

    if _contains(
        text,
        "child pose",
        "camel pose",
        "low lunge",
        "gate pose",
        "extended puppy",
        "virasana",
        "vajrasana",
    ):
        add_family("kneeling")

    if _contains(
        text,
        "seated",
        "staff pose",
        "boat pose",
        "bound angle",
        "cow face pose",
        "half lord",
        "janu sirsasana",
        "bharadvaja",
        "dandasana",
        "upavistha",
        "tortoise pose",
        "heron pose",
        "scale pose",
        "akarna dhanurasana",
    ):
        add_family("seated")

    return families or ["general"]


def _difficulty_for_pose(text: str, families: list[str]) -> str:
    if _contains(
        text,
        "handstand",
        "headstand",
        "scorpion",
        "peacock pose",
        "firefly",
        "eight angle",
        "koundinya",
        "bhujapidasana",
        "side crane",
        "feathered peacock",
        "split pose",
        "upward facing two foot staff",
        "cockerel pose",
    ):
        return "Advanced"
    if "inversion" in families or "arm_balance" in families:
        return "Advanced"
    if _contains(
        text,
        "warrior iii",
        "half moon",
        "eagle pose",
        "triangle",
        "reverse warrior",
        "side plank",
        "plank pose",
        "boat pose",
        "bow pose",
        "camel pose",
        "pigeon pose",
        "dolphin pose",
        "dolphin plank",
        "locust pose",
        "rajakapotasana",
        "akarna dhanurasana",
    ):
        return "Intermediate"
    return "Beginner"


def _intensity_for_pose(families: list[str]) -> str:
    if "inversion" in families or "arm_balance" in families:
        return "High"
    if "restorative" in families or "supine" in families:
        return "Low"
    if "backbend" in families or "standing" in families or "core" in families:
        return "Moderate"
    return "Low"


def _goal_tags_for_pose(families: list[str]):
    goals = []

    def add_goal(name: str):
        if name not in goals:
            goals.append(name)

    if any(
        family in families
        for family in ["forward_fold", "hip_opener", "twist", "shoulder_opener", "kneeling", "seated"]
    ):
        add_goal("mobility")
    if any(family in families for family in ["core", "arm_balance", "inversion", "standing", "backbend"]):
        add_goal("strength")
    if any(family in families for family in ["balance", "standing", "arm_balance", "inversion"]):
        add_goal("balance")
    if any(family in families for family in ["posture", "standing", "backbend", "core"]):
        add_goal("posture")
    if any(family in families for family in ["restorative", "supine", "twist", "seated"]):
        add_goal("relaxation")
    if any(family in families for family in ["standing", "core", "backbend", "inversion"]):
        add_goal("energy")
    return goals or ["mobility"]


def _health_support_for_pose(text: str, families: list[str]):
    support = []

    def add_support(name: str):
        if name not in support:
            support.append(name)

    if any(family in families for family in ["restorative", "supine", "twist", "seated"]):
        add_support("stress_relief")
    if any(family in families for family in ["posture", "backbend", "standing", "core"]):
        add_support("poor_posture")
    if any(family in families for family in ["standing", "balance"]) or _contains(text, "warrior", "tree pose", "eagle pose"):
        add_support("balance_support")
    if any(family in families for family in ["core", "arm_balance"]) or _contains(text, "plank pose", "boat pose"):
        add_support("core_strength")
    if any(family in families for family in ["standing", "backbend", "core", "inversion"]):
        add_support("low_energy")
    if any(family in families for family in ["forward_fold", "standing"]) or _contains(text, "downward facing dog"):
        add_support("stiff_hamstrings")
    if any(family in families for family in ["hip_opener", "kneeling"]) or _contains(text, "tree pose"):
        add_support("hip_tightness")
    if any(family in families for family in ["shoulder_opener", "posture"]) and "inversion" not in families:
        add_support("shoulder_tightness")
    if _contains(text, "child pose", "cat cow", "bridge pose", "legs up the wall", "wind relieving"):
        add_support("back_pain")
    if any(family in families for family in ["restorative", "supine", "seated"]) and "kneeling" not in families:
        add_support("knee_sensitivity")
    return support


def _caution_tags_for_pose(text: str, families: list[str]):
    cautions = []

    def add_caution(name: str):
        if name not in cautions:
            cautions.append(name)

    if _contains(
        text,
        "chair pose",
        "warrior",
        "low lunge",
        "garland pose",
        "noose pose",
        "eagle pose",
        "tree pose",
        "half moon",
        "split pose",
        "virasana",
        "vajrasana",
        "camel pose",
        "frog pose",
        "pigeon pose",
        "bound angle",
        "child pose",
    ):
        add_caution("knee_sensitivity")

    if any(family in families for family in ["arm_balance", "inversion", "shoulder_opener"]) or _contains(
        text,
        "plank pose",
        "cobra pose",
        "wheel pose",
        "bow pose",
        "camel pose",
    ):
        add_caution("shoulder_tightness")

    if any(family in families for family in ["backbend", "inversion"]) or _contains(
        text,
        "forward bend",
        "split pose",
        "plow pose",
        "shoulderstand",
    ):
        add_caution("back_pain")

    if any(family in families for family in ["hip_opener", "standing"]) or _contains(
        text,
        "warrior",
        "low lunge",
        "pigeon pose",
        "frog pose",
        "split pose",
    ):
        add_caution("hip_tightness")

    return cautions


def _benefits_for_pose(families: list[str], goals: list[str]):
    benefit_map = {
        "mobility": "Improves controlled mobility through the major joints used in the pose",
        "strength": "Builds muscular support so the shape stays stable under load",
        "balance": "Develops balance, focus, and spatial body awareness",
        "posture": "Encourages better stacking through the spine, ribs, and shoulders",
        "relaxation": "Helps settle the breath and reduce unnecessary tension",
        "energy": "Creates alertness and healthy full-body engagement",
    }

    benefits = []
    if "backbend" in families:
        benefits.append("Opens the front body while training controlled spinal extension")
    if "forward_fold" in families:
        benefits.append("Lengthens the back body without needing to force the range")
    if "twist" in families:
        benefits.append("Improves rotational awareness through the ribs and spine")

    for goal in goals:
        if benefit_map.get(goal) and benefit_map[goal] not in benefits:
            benefits.append(benefit_map[goal])
        if len(benefits) == 3:
            break

    while len(benefits) < 3:
        benefits.append("Reinforces patient, breath-led alignment instead of rushing the shape")
    return benefits[:3]


def _base_position(text: str, families: list[str]) -> str:
    if "inversion" in families:
        return "inversion"
    if "arm_balance" in families:
        return "arm_balance"
    if "standing" in families or "balance" in families:
        return "standing"
    if "supine" in families or _contains(text, "reclining", "corpse pose", "legs up the wall"):
        return "supine"
    if "prone" in families:
        return "prone"
    if "kneeling" in families:
        return "kneeling"
    if "seated" in families:
        return "seated"
    return "general"


def _instructions_for_pose(pose_name: str, text: str, families: list[str]):
    position = _base_position(text, families)

    if position == "inversion":
        return [
            "Warm up the shoulders, wrists, and core before moving into the full inversion.",
            f"Set the hands or forearms firmly, then enter {pose_name} with active shoulders and a braced trunk.",
            "Only hold the shape while breath stays smooth and you can exit with control.",
        ]
    if position == "arm_balance":
        return [
            "Place the hands solidly on the floor and spread the fingers to create a stable base.",
            f"Move into {pose_name} by leaning weight forward gradually instead of jumping into the balance.",
            "Keep the core engaged and come out early if the shoulders or wrists stop feeling supported.",
        ]
    if position == "standing" and "balance" in families:
        return [
            "Start from a steady standing base and organize the feet before shaping the rest of the pose.",
            f"Move into {pose_name} with a long spine and controlled hip positioning rather than chasing depth.",
            "Keep the gaze steady, breathe evenly, and use wall support if balance becomes shaky.",
        ]
    if position == "standing":
        return [
            "Root through both feet first so the lower body feels stable before deepening the pose.",
            f"Enter {pose_name} by moving from the hips and ribs while keeping the chest broad and the breath steady.",
            "Stay in the range where knees, hips, and shoulders still feel organized instead of forced.",
        ]
    if position == "prone" and "backbend" in families:
        return [
            "Lie on the belly and anchor the legs and pelvis into the mat before lifting.",
            f"Build {pose_name} by lengthening through the spine first, then opening the chest gradually.",
            "Back off slightly if the neck shortens or the lower back feels pinchy.",
        ]
    if position == "supine":
        return [
            "Lie on the back and settle the ribs and pelvis before entering the shape.",
            f"Guide the legs or arms into {pose_name} with a calm breath and no forcing.",
            "Keep the jaw soft and stay in the version where the lower back and hips remain comfortable.",
        ]
    if position == "kneeling":
        return [
            "Come onto the knees with padding if needed and stack the body over a stable base.",
            f"Move into {pose_name} slowly, keeping the core lightly active and the breath smooth.",
            "Adjust the depth or hand position if the knees, hips, or lower back feel overloaded.",
        ]
    if position == "seated":
        return [
            "Sit tall on the sitting bones or a folded support so the spine can lengthen easily.",
            f"Organize the legs for {pose_name} before deepening any fold, lift, or twist.",
            "Use each inhale to create length and only deepen on an easy exhale.",
        ]
    return [
        f"Enter {pose_name} slowly with a steady base and even breath.",
        "Lengthen through the spine before trying to deepen the shape.",
        "Stay in the version you can control without strain or breath-holding.",
    ]


def _breath_cues_for_pose(families: list[str]):
    if "restorative" in families or "supine" in families:
        return [
            "Inhale softly through the nose and let the ribs widen.",
            "Exhale longer than the inhale to settle deeper without forcing the shape.",
        ]
    if "backbend" in families:
        return [
            "Inhale to create length before opening the chest.",
            "Exhale and soften the shoulders so the backbend stays spacious.",
        ]
    if "forward_fold" in families or "twist" in families:
        return [
            "Inhale to lengthen the spine.",
            "Exhale to deepen only as far as the breath stays smooth.",
        ]
    return [
        "Keep the breath slow and even while you organize the shape.",
        "Use the exhale to steady the core and relax unnecessary tension.",
    ]


def _common_mistakes_for_pose(families: list[str]):
    mistakes = []
    if "balance" in families:
        mistakes.append("Rushing into the balance before the base is steady")
    if "forward_fold" in families:
        mistakes.append("Pulling for depth instead of hinging with a long spine")
    if "backbend" in families:
        mistakes.append("Pushing into the lower back instead of lengthening first")
    if "arm_balance" in families or "inversion" in families:
        mistakes.append("Throwing weight into the wrists and shoulders without core support")
    if "standing" in families:
        mistakes.append("Letting the knees and hips drift out of alignment")
    if not mistakes:
        mistakes.append("Holding the breath while trying to deepen the pose")
    while len(mistakes) < 3:
        mistakes.append("Adding range before the base of the pose feels stable")
    return mistakes[:3]


def _modifications_for_pose(families: list[str], caution_tags: list[str]):
    modifications = []
    if "knee_sensitivity" in caution_tags:
        modifications.append("Use a folded blanket or extra padding under the knees.")
    if "shoulder_tightness" in caution_tags:
        modifications.append("Work in a smaller range and keep the shoulders away from the ears.")
    if "back_pain" in caution_tags:
        modifications.append("Reduce the depth and prioritize spinal length over the full expression.")
    if "hip_tightness" in caution_tags or "forward_fold" in families:
        modifications.append("Use a block, strap, or bent-knee variation to keep the shape accessible.")
    if "balance" in families:
        modifications.append("Practice beside a wall or chair for extra balance support.")
    if "arm_balance" in families or "inversion" in families:
        modifications.append("Practice near a wall and use preparation drills before the full pose.")
    if not modifications:
        modifications.append("Choose the smallest version of the pose that still feels stable and breathable.")
    return modifications[:3]


def _coach_focus_for_pose(families: list[str]):
    if "inversion" in families:
        return "Shoulder stacking, core control, and a steady line through the body"
    if "arm_balance" in families:
        return "Hand pressure, shoulder support, and calm forward weight shift"
    if "balance" in families or "standing" in families:
        return "Foot grounding, hip stability, and a long stacked spine"
    if "forward_fold" in families:
        return "Hip hinge, spinal length, and soft knee control"
    if "twist" in families:
        return "Length before rotation and even movement through the ribs"
    if "backbend" in families:
        return "Chest opening, lower-back space, and steady glute support"
    if "restorative" in families:
        return "Supported joints, relaxed shoulders, and slow breath"
    return "Stable base, clear alignment, and easy breathing"


def _hold_seconds_for_pose(intensity: str, families: list[str]) -> int:
    if "restorative" in families:
        return 45
    if intensity == "High":
        return 15
    if intensity == "Moderate":
        return 25
    return 35


def _repetitions_for_pose(intensity: str, families: list[str]) -> int:
    if "restorative" in families:
        return 2
    if intensity == "High":
        return 1
    if intensity == "Moderate":
        return 2
    return 2


def _caution_text(caution_tags: list[str]):
    if not caution_tags:
        return "Practice within a pain-free range and step out early if breath becomes strained."

    caution_bits = _format_matches(caution_tags, HEALTH_FACTOR_LABELS)
    if len(caution_bits) == 1:
        return f"Use extra support and a smaller range if you have {caution_bits[0].lower()}."
    return f"Use extra support and keep the range smaller if you have {', '.join(bit.lower() for bit in caution_bits[:2])}."


def _build_auto_pose(dataset_index: int, raw_label: str):
    pose_name, sanskrit_name = _split_display_names(raw_label)
    text = normalize_pose_name(" ".join([pose_name, sanskrit_name, raw_label]))
    families = _movement_families(pose_name, sanskrit_name, raw_label)
    difficulty = _difficulty_for_pose(text, families)
    intensity = _intensity_for_pose(families)
    goal_tags = _goal_tags_for_pose(families)
    health_support = _health_support_for_pose(text, families)
    caution_tags = _caution_tags_for_pose(text, families)

    aliases = {
        raw_label,
        raw_label.strip("_"),
        raw_label.replace("_", " "),
        pose_name,
        sanskrit_name,
    }
    parts = [part for part in raw_label.strip("_").split("_or_") if part]
    aliases.update(part.replace("_", " ") for part in parts)

    return {
        "dataset_index": dataset_index,
        "dataset_label": raw_label,
        "pose_name": pose_name,
        "sanskrit_name": sanskrit_name,
        "difficulty": difficulty,
        "intensity": intensity,
        "aliases": sorted(alias for alias in aliases if alias),
        "goal_tags": goal_tags,
        "health_support": health_support,
        "caution_tags": caution_tags,
        "movement_families": families,
        "benefits": _benefits_for_pose(families, goal_tags),
        "instructions": _instructions_for_pose(pose_name, text, families),
        "breath_cues": _breath_cues_for_pose(families),
        "common_mistakes": _common_mistakes_for_pose(families),
        "modifications": _modifications_for_pose(families, caution_tags),
        "coach_focus": _coach_focus_for_pose(families),
        "base_hold_seconds": _hold_seconds_for_pose(intensity, families),
        "repetitions": _repetitions_for_pose(intensity, families),
        "caution": _caution_text(caution_tags),
    }


def _prepare_pose_entry(pose: dict):
    prepared = dict(pose)
    aliases = set(_listify(prepared.get("aliases")))
    aliases.add(prepared["pose_name"])
    aliases.add(prepared.get("sanskrit_name", ""))
    if prepared.get("dataset_label"):
        aliases.add(prepared["dataset_label"])
        aliases.add(prepared["dataset_label"].replace("_", " "))

    prepared["slug"] = _slug(prepared["pose_name"])
    prepared["normalized_pose_name"] = normalize_pose_name(prepared["pose_name"])
    prepared["normalized_aliases"] = sorted(
        normalize_pose_name(alias)
        for alias in aliases
        if alias
    )
    prepared["movement_families"] = list(prepared.get("movement_families", []))
    return prepared


CURATED_POSES = [_prepare_pose_entry(pose) for pose in CURATED_POSES]


def reference_image_path_for_pose(pose: Optional[dict]):
    if not pose or not pose.get("slug"):
        return None
    for extension in (".jpg", ".jpeg", ".png", ".webp"):
        candidate = os.path.join(REFERENCE_IMAGE_DIR, f"{pose['slug']}{extension}")
        if os.path.exists(candidate):
            return candidate
    return None


def reference_image_route_for_pose(pose: Optional[dict]):
    if not pose or not pose.get("slug"):
        return None
    if not reference_image_path_for_pose(pose):
        return None
    return f"/poses/reference-image/{pose['slug']}"


def _matching_curated_pose(auto_pose: dict):
    auto_aliases = set(auto_pose["normalized_aliases"])
    for curated_pose in CURATED_POSES:
        if auto_aliases.intersection(curated_pose["normalized_aliases"]):
            return curated_pose
    return None


def _merge_pose_entry(auto_pose: dict, curated_pose: Optional[dict]):
    if curated_pose is None:
        return auto_pose

    merged = dict(auto_pose)
    merged.update({key: value for key, value in curated_pose.items() if key not in {"normalized_aliases", "normalized_pose_name", "slug"}})
    merged["aliases"] = sorted(set(_listify(auto_pose.get("aliases"))) | set(_listify(curated_pose.get("aliases"))))
    merged["movement_families"] = list(
        dict.fromkeys(_listify(curated_pose.get("movement_families")) + _listify(auto_pose.get("movement_families")))
    )
    return _prepare_pose_entry(merged)


def _build_pose_library():
    dataset_poses = _load_dataset_pose_labels()
    if not dataset_poses:
        return CURATED_POSES

    library = []
    for item in dataset_poses:
        auto_pose = _prepare_pose_entry(_build_auto_pose(item["dataset_index"], item["dataset_label"]))
        library.append(_merge_pose_entry(auto_pose, _matching_curated_pose(auto_pose)))
    return library


POSE_LIBRARY = _build_pose_library()
POSE_INDEX = {pose["normalized_pose_name"]: pose for pose in POSE_LIBRARY}


def resolve_pose_by_slug(pose_slug: Optional[str]):
    if not pose_slug:
        return None
    for pose in POSE_LIBRARY:
        if pose.get("slug") == pose_slug:
            return pose
    return None


def pose_catalog():
    return [
        {
            "dataset_index": pose.get("dataset_index"),
            "dataset_label": pose.get("dataset_label"),
            "pose_name": pose["pose_name"],
            "sanskrit_name": pose["sanskrit_name"],
            "difficulty": pose["difficulty"],
            "intensity": pose["intensity"],
            "slug": pose["slug"],
            "coach_focus": pose["coach_focus"],
            "benefits": pose["benefits"],
            "instructions": pose["instructions"],
            "breath_cues": pose["breath_cues"],
            "common_mistakes": pose["common_mistakes"],
            "modifications": pose["modifications"],
            "caution": pose["caution"],
            "movement_families": pose.get("movement_families", []),
            "reference_image_path": reference_image_route_for_pose(pose),
        }
        for pose in POSE_LIBRARY
    ]


def resolve_pose(target_pose: Optional[str]):
    if not target_pose:
        return None
    normalized = normalize_pose_name(target_pose)
    for pose in POSE_LIBRARY:
        if normalized in pose["normalized_aliases"]:
            return pose
    for pose in POSE_LIBRARY:
        if any(
            normalized in alias or alias in normalized
            for alias in pose["normalized_aliases"]
        ):
            return pose
    return None


def _score_pose(pose: dict, age: int, experience_level: str, goals: set[str], health_factors: set[str]):
    score = 1.0
    matches = {
        "goals": sorted(goals.intersection(pose.get("goal_tags", []))),
        "health": sorted(health_factors.intersection(pose.get("health_support", []))),
        "cautions": sorted(health_factors.intersection(pose.get("caution_tags", []))),
    }

    score += 2.6 * len(matches["health"])
    score += 1.8 * len(matches["goals"])
    score -= 1.45 * len(matches["cautions"])

    level_gap = DIFFICULTY_ORDER.get(pose["difficulty"], 0) - EXPERIENCE_ORDER.get(experience_level, 0)
    if level_gap > 0:
        score -= 1.8 * level_gap
    elif level_gap < 0:
        score += 0.45

    intensity = pose.get("intensity")
    age_band = _age_band(age)
    if age_band == "senior":
        if intensity == "Low":
            score += 1.4
        if intensity == "High":
            score -= 1.2
        if pose["difficulty"] == "Advanced":
            score -= 1.0
    elif age_band == "teen":
        if "balance" in pose.get("goal_tags", []) or "energy" in pose.get("goal_tags", []):
            score += 0.35

    if not matches["goals"] and not matches["health"]:
        score -= 0.35

    if "restorative" in pose.get("movement_families", []) and "relaxation" in goals:
        score += 0.6
    if "core" in pose.get("movement_families", []) and "strength" in goals:
        score += 0.45
    if "balance" in pose.get("movement_families", []) and "balance" in goals:
        score += 0.45

    return score, matches


def _primary_family(pose: dict) -> str:
    priority = [
        "restorative",
        "balance",
        "standing",
        "forward_fold",
        "twist",
        "backbend",
        "hip_opener",
        "core",
        "arm_balance",
        "inversion",
        "seated",
        "supine",
        "kneeling",
        "prone",
        "shoulder_opener",
        "posture",
    ]
    families = pose.get("movement_families", [])
    for family in priority:
        if family in families:
            return family
    return families[0] if families else "general"


def _featured_count_for_session(session_minutes: int) -> int:
    if session_minutes <= 15:
        return 5
    if session_minutes <= 25:
        return 6
    return 8


def _select_featured_recommendations(ranked: list[tuple], desired_count: int):
    selected = []
    selected_slugs = set()
    family_counts = {}

    for score, pose, matches in ranked:
        family = _primary_family(pose)
        if family_counts.get(family, 0) >= 2:
            continue
        selected.append((score, pose, matches))
        selected_slugs.add(pose["slug"])
        family_counts[family] = family_counts.get(family, 0) + 1
        if len(selected) >= desired_count:
            break

    if len(selected) < desired_count:
        for score, pose, matches in ranked:
            if pose["slug"] in selected_slugs:
                continue
            selected.append((score, pose, matches))
            selected_slugs.add(pose["slug"])
            if len(selected) >= desired_count:
                break

    return selected


def _serialize_recommendation(
    pose: dict,
    score: float,
    matches: dict,
    age: int,
    experience_level: str,
    session_minutes: int,
    ranking_position: int,
):
    matched_goals = _format_matches(matches["goals"], GOAL_LABELS)
    matched_health = _format_matches(matches["health"], HEALTH_FACTOR_LABELS)
    caution_labels = _format_matches(matches["cautions"], HEALTH_FACTOR_LABELS)
    why_bits = matched_health + matched_goals

    if why_bits:
        why_selected = f"Matched for {', '.join(bit.lower() for bit in why_bits[:3])}."
    else:
        why_selected = "Included as a lower-priority option after stronger profile matches."

    return {
        "dataset_index": pose.get("dataset_index"),
        "dataset_label": pose.get("dataset_label"),
        "pose_name": pose["pose_name"],
        "sanskrit_name": pose["sanskrit_name"],
        "difficulty": pose["difficulty"],
        "intensity": pose["intensity"],
        "slug": pose["slug"],
        "ranking_position": ranking_position,
        "movement_families": pose.get("movement_families", []),
        "hold_seconds": _hold_seconds(pose, age, experience_level),
        "repetitions": _repetitions(pose, session_minutes),
        "benefits": pose["benefits"],
        "instructions": pose["instructions"],
        "breath_cues": pose["breath_cues"],
        "common_mistakes": pose["common_mistakes"],
        "modifications": pose["modifications"],
        "coach_focus": pose["coach_focus"],
        "reference_image_path": reference_image_route_for_pose(pose),
        "why_selected": why_selected,
        "matched_goals": matched_goals,
        "matched_health_factors": matched_health,
        "caution_factors": caution_labels,
        "caution": pose["caution"],
        "score": round(score, 2),
    }


def build_recommendation_plan(payload: Optional[dict]):
    payload = payload or {}
    age = int(payload.get("age") or 30)
    experience_level = _slug(str(payload.get("experience_level") or "beginner"))
    if experience_level not in EXPERIENCE_ORDER:
        experience_level = "beginner"

    session_minutes = int(payload.get("session_minutes") or 20)
    session_minutes = min(60, max(10, session_minutes))

    health_factors = _normalize_tags(payload.get("health_factors"))
    goals = _normalize_tags(payload.get("goals"))
    if not goals:
        goals = {"mobility", "relaxation"}

    ranked = []
    for pose in POSE_LIBRARY:
        score, matches = _score_pose(
            pose=pose,
            age=age,
            experience_level=experience_level,
            goals=goals,
            health_factors=health_factors,
        )
        ranked.append((score, pose, matches))

    ranked.sort(
        key=lambda item: (
            -item[0],
            DIFFICULTY_ORDER.get(item[1]["difficulty"], 0),
            item[1]["pose_name"],
        )
    )

    featured_selected = _select_featured_recommendations(
        ranked=ranked,
        desired_count=_featured_count_for_session(session_minutes),
    )

    recommendations = [
        _serialize_recommendation(
            pose=pose,
            score=score,
            matches=matches,
            age=age,
            experience_level=experience_level,
            session_minutes=session_minutes,
            ranking_position=index + 1,
        )
        for index, (score, pose, matches) in enumerate(ranked)
    ]

    featured_recommendations = [
        _serialize_recommendation(
            pose=pose,
            score=score,
            matches=matches,
            age=age,
            experience_level=experience_level,
            session_minutes=session_minutes,
            ranking_position=next(
                ranked_index + 1
                for ranked_index, (_, ranked_pose, _) in enumerate(ranked)
                if ranked_pose["slug"] == pose["slug"]
            ),
        )
        for score, pose, matches in featured_selected
    ]

    safety_notes = []
    for item in featured_recommendations:
        if item["caution_factors"]:
            safety_notes.append(f"{item['pose_name']}: {item['caution']}")

    focus_goal = next(iter(goals), "mobility")
    goal_label = GOAL_LABELS.get(focus_goal, focus_goal.replace("_", " ").title())
    health_summary = _format_matches(sorted(health_factors), HEALTH_FACTOR_LABELS)

    return {
        "summary": {
            "age": age,
            "age_band": _age_band(age),
            "experience_level": experience_level.title(),
            "session_minutes": session_minutes,
            "goals": _format_matches(sorted(goals), GOAL_LABELS),
            "health_factors": health_summary,
            "focus_message": f"A {goal_label.lower()}-first routine with the full Yoga-82 catalog ranked to your profile.",
        },
        "featured_recommendations": featured_recommendations,
        "recommendations": recommendations,
        "safety_notes": safety_notes[:6],
        "disclaimer": "This guidance is educational and not a medical diagnosis. Users with pain, injury, or ongoing health concerns should work within clinician-approved limits.",
        "available_pose_count": len(POSE_LIBRARY),
        "featured_pose_count": len(featured_recommendations),
    }


def build_target_pose_guidance(
    target_pose: Optional[str],
    detected_pose: Optional[str],
    issues: Optional[list[dict]],
    confidence_suppressed: bool = False,
):
    pose = resolve_pose(target_pose)
    if pose is None:
        if target_pose:
            return {
                "requested_pose": target_pose,
                "available": False,
                "status": "unsupported",
                "message": "That target pose is not in the guided coaching library yet.",
            }
        return None

    detected_normalized = normalize_pose_name(detected_pose) if detected_pose else None
    matched = bool(
        detected_normalized
        and any(
            detected_normalized == alias
            or detected_normalized in alias
            or alias in detected_normalized
            for alias in pose["normalized_aliases"]
        )
    )
    issues = issues or []

    if confidence_suppressed:
        status = "hold_steady"
        message = f"Hold {pose['pose_name']} steadily so I can verify your alignment."
    elif not detected_pose:
        status = "awaiting_pose"
        message = f"Move into {pose['pose_name']} and keep your full body visible in the frame."
    elif matched and issues:
        status = "needs_correction"
        message = issues[0]["message"]
    elif matched:
        status = "aligned"
        message = f"You are holding {pose['pose_name']} well. Maintain steady breath and stay for {pose['base_hold_seconds']} seconds."
    else:
        status = "different_pose"
        message = f"I am currently detecting {detected_pose}. Return to {pose['pose_name']} to continue this guided step."

    return {
        "requested_pose": target_pose,
        "pose_name": pose["pose_name"],
        "sanskrit_name": pose["sanskrit_name"],
        "slug": pose["slug"],
        "available": True,
        "status": status,
        "matched_detected_pose": matched,
        "message": message,
        "coach_focus": pose["coach_focus"],
        "instructions": pose["instructions"],
        "breath_cues": pose["breath_cues"],
        "common_mistakes": pose["common_mistakes"],
        "modifications": pose["modifications"],
        "caution": pose["caution"],
    }
