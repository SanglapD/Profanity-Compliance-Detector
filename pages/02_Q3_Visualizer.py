
import io
import os
import json
import zipfile
import unicodedata
from typing import List, Tuple, Dict

import streamlit as st
import matplotlib.pyplot as plt

try:
    import yaml
    HAS_YAML = True
except Exception:
    HAS_YAML = False

def nfkc(s: str) -> str:
    t = unicodedata.normalize("NFKC", s or "")
    return " ".join(t.split())

def norm_speaker(s: str) -> str:
    s = (s or "").strip().lower()
    if s == "agent":
        return "agent"
    if s in ("customer", "borrower"):
        return "customer"
    return "unknown"

Interval = Tuple[int, int]

def merge_intervals(iv: List[Interval]) -> List[Interval]:
    if not iv:
        return []
    iv = sorted(iv, key=lambda x: (x[0], x[1]))
    out = [iv[0]]
    for s, e in iv[1:]:
        ps, pe = out[-1]
        if s <= pe:
            out[-1] = (ps, max(pe, e))
        else:
            out.append((s, e))
    return out

def union_length(iv: List[Interval]) -> int:
    merged = merge_intervals(iv)
    return sum(e - s for s, e in merged)

def intersect_two_sets(a: List[Interval], b: List[Interval]) -> List[Interval]:
    a = merge_intervals(a)
    b = merge_intervals(b)
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        s1, e1 = a[i]; s2, e2 = b[j]
        s = max(s1, s2); e = min(e1, e2)
        if s < e:
            out.append((s, e))
        if e1 <= e2:
            i += 1
        else:
            j += 1
    return out

def load_call_from_bytes(file_name: str, file_bytes: bytes) -> Dict:
    call_id, ext = os.path.splitext(os.path.basename(file_name))
    ext = ext.lower()
    if ext == ".json":
        data = json.loads(file_bytes.decode("utf-8", errors="ignore"))
    elif ext in (".yaml", ".yml"):
        if not HAS_YAML:
            raise RuntimeError("PyYAML is required to parse YAML files. Please add pyyaml to requirements.")
        data = yaml.safe_load(file_bytes.decode("utf-8", errors="ignore"))
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    turns_raw = data["turns"] if isinstance(data, dict) and "turns" in data else data
    turns = []
    for i, t in enumerate(turns_raw or []):
        sp = norm_speaker(t.get("speaker", ""))
        stime = t.get("stime", 0)
        etime = t.get("etime", 0)
        try:
            stime = int(stime)
        except Exception:
            stime = 0
        try:
            etime = int(etime)
        except Exception:
            etime = stime
        if etime < stime:
            etime = stime
        txt = t.get("text", "")
        turns.append({
            "idx": i,
            "speaker": sp,
            "stime": stime,
            "etime": etime,
            "text_raw": txt,
            "text_norm": nfkc(txt),
        })
    return {"call_id": call_id, "turns": turns}

def load_call_from_prompt(call_id: str, prompt_text: str) -> Dict:
    data = json.loads(prompt_text)
    turns_raw = data["turns"] if isinstance(data, dict) and "turns" in data else data
    if not isinstance(turns_raw, list):
        raise ValueError("JSON prompt must be a list of utterances or an object with a 'turns' list.")
    turns = []
    for i, t in enumerate(turns_raw):
        if not isinstance(t, dict):
            continue
        sp = norm_speaker(t.get("speaker", ""))
        stime = t.get("stime", 0)
        etime = t.get("etime", 0)
        try:
            stime = int(stime)
        except Exception:
            stime = 0
        try:
            etime = int(etime)
        except Exception:
            etime = stime
        if etime < stime:
            etime = stime
        txt = t.get("text", "")
        turns.append({
            "idx": i,
            "speaker": sp,
            "stime": stime,
            "etime": etime,
            "text_raw": txt,
            "text_norm": nfkc(txt),
        })
    return {"call_id": call_id or "PROMPT_1", "turns": turns}

def intervals_from_turns(turns: List[Dict], who: str) -> List[Interval]:
    return [(t["stime"], t["etime"]) for t in turns if t["speaker"] == who and t["etime"] > t["stime"]]

def compute_q3_metrics(call: Dict) -> Dict:
    cid = call["call_id"]
    ts = call["turns"]
    if not ts:
        return {"call_id": cid, "duration_sec": 0, "overtalk_sec": 0, "overtalk_pct": 0.0, "silence_sec": 0, "silence_pct": 0.0}
    start = min(t["stime"] for t in ts)
    end = max(t["etime"] for t in ts)
    dur = max(0, end - start)
    a_iv = intervals_from_turns(ts, "agent")
    c_iv = intervals_from_turns(ts, "customer")
    any_len = union_length(a_iv + c_iv)
    over_iv = intersect_two_sets(a_iv, c_iv)
    over_len = sum(e - s for s, e in over_iv)
    silence_len = max(0, dur - any_len)
    over_pct = (over_len / dur) if dur > 0 else 0.0
    silence_pct = (silence_len / dur) if dur > 0 else 0.0
    return {
        "call_id": cid,
        "duration_sec": dur,
        "overtalk_sec": over_len,
        "overtalk_pct": over_pct,
        "silence_sec": silence_len,
        "silence_pct": silence_pct,
    }

def make_call_figure(call_id: str, metrics_map: Dict[str, Dict]):
    m = metrics_map[call_id]
    labels = ["Overtalk %", "Silence %"]
    vals = [m["overtalk_pct"] * 100.0, m["silence_pct"] * 100.0]
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, vals)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Percentage (%)")
    ax.set_title(f"Call {call_id}: Overtalk and Silence")
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 1, f"{h:.1f}%", ha="center", va="bottom", fontsize=10)
    info = (
        f"Duration: {m['duration_sec']} s\n"
        f"Overtalk: {m['overtalk_sec']} s ({m['overtalk_pct']*100:.1f}%)\n"
        f"Silence:  {m['silence_sec']} s ({m['silence_pct']*100:.1f}%)"
    )
    ax.text(1.05, 0.5, info, transform=ax.transAxes, va="center",
            bbox=dict(boxstyle="round", alpha=0.1, pad=0.5), fontsize=10)
    plt.tight_layout()
    return fig

st.title("Q3: Overtalk and Silence Visualizer")

mode = st.radio(
    "Choose input mode",
    ["Upload ZIP of calls (multiple)", "Paste JSON prompt (single)"],
    index=0
)

if "calls" not in st.session_state:
    st.session_state.calls = {}
if "metrics" not in st.session_state:
    st.session_state.metrics = {}
if "call_ids" not in st.session_state:
    st.session_state.call_ids = []

if mode == "Upload ZIP of calls (multiple)":
    st.markdown("Upload a ZIP with JSON or YAML files. The filename without extension is used as call_id.")
    zip_file = st.file_uploader("Upload calls ZIP", type=["zip"])
    if zip_file is not None:
        with zipfile.ZipFile(io.BytesIO(zip_file.read()), "r") as zf:
            loaded = {}
            for name in zf.namelist():
                if name.lower().endswith((".json", ".yaml", ".yml")) and not name.endswith("/"):
                    try:
                        with zf.open(name) as f:
                            file_bytes = f.read()
                        c = load_call_from_bytes(name, file_bytes)
                        loaded[c["call_id"]] = c
                    except Exception as e:
                        st.warning(f"Skipped {name}: {e}")
        st.session_state.calls = loaded
        st.session_state.metrics = {cid: compute_q3_metrics(c) for cid, c in loaded.items()}
        st.session_state.call_ids = sorted(st.session_state.metrics.keys())

    if st.session_state.call_ids:
        st.subheader("Select or search for a Call ID")
        selected_id = st.selectbox(
            "Browse and search call_ids",
            options=st.session_state.call_ids,
            index=0,
            key="select_call_id_zip",
            help="Click to see all IDs. Type to filter."
        )
        pasted_id = st.text_input(
            "Or paste a call_id",
            value="",
            key="paste_call_id_zip",
            placeholder="e.g., CALL_0001"
        )
        chosen_id = pasted_id.strip() if pasted_id.strip() else selected_id
        if st.button("Generate visualization", key="viz_zip"):
            if chosen_id in st.session_state.metrics:
                fig = make_call_figure(chosen_id, st.session_state.metrics)
                st.pyplot(fig)
            else:
                st.error(f"call_id '{chosen_id}' not found. Try selecting from the list above.")
    else:
        st.info("Upload a ZIP to populate call_ids.")

else:
    st.markdown("Paste a JSON prompt representing a single call. Accepts either a list of utterances or an object with a 'turns' list. Each item must have: speaker, text, stime, etime.")
    example = [
        {"speaker": "agent", "text": "Hello, thanks for calling.", "stime": 0, "etime": 3},
        {"speaker": "customer", "text": "Hi, I have a question.", "stime": 3, "etime": 7},
        {"speaker": "agent", "text": "Sure, go ahead.", "stime": 7, "etime": 10}
    ]
    st.caption("Example JSON prompt")
    st.code(json.dumps(example, indent=2))
    call_id_input = st.text_input("Call ID to label this prompt", value="PROMPT_1")
    prompt_text = st.text_area("Paste JSON prompt here", height=220, placeholder="Paste a JSON list or an object with 'turns' here")
    if st.button("Generate visualization", key="viz_prompt"):
        if not prompt_text.strip():
            st.error("Please paste a valid JSON prompt.")
        else:
            try:
                single_call = load_call_from_prompt(call_id_input.strip() or "PROMPT_1", prompt_text)
                metrics = compute_q3_metrics(single_call)
                metrics_map = {metrics["call_id"]: metrics}
                fig = make_call_figure(metrics["call_id"], metrics_map)
                st.pyplot(fig)
            except Exception as e:
                st.error(f"Failed to parse or visualize the JSON prompt: {e}")

st.caption("Times are assumed to be integer seconds. Speakers are normalized to 'agent' and 'customer' (borrower maps to customer).")
