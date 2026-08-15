#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluate 3 MeetingToM tasks from merged prediction jsonl files (stdlib-only, no sklearn).

Tasks:
1) state  (merged Task1):
   - window_index=0 aligns to GT.answers.Q1
   - window_index=1 aligns to GT.answers.Q2
   - prediction label is always extracted from model output's "Q1" (because many runs only output {"Q1": "..."} even for window1)
   - metrics computed on aligned (bundle, window_index) pairs

2) you (Q1/Q2 separate):
   - evaluate Q1 and Q2 separately by bundle (no gating)

3) consensus:
   - Q1 evaluated normally
   - Q2 uses a "two-step / points" rule:
        score = 1 if Q1 correct
              + 1 if (Q1 correct AND Q2 correct)
     This matches: Q1错 => Q2也拿不到分；Q1对Q2错 => 只算Q1；Q1Q2都对 => 都得分
   - additionally report Q2 conditional metrics on the subset where Q1 is correct (common diagnostic)

Prediction parsing:
- Supports OpenAI Responses API output blocks and OpenAI-compatible choices/message/content.
- Reads only actual output/result/response fields.
- Never scans prompt messages or metadata for answers.

Outputs:
- out_dir/state_task1_merged/summary.csv + per-file metrics json + combined.metrics.json
- out_dir/you_q1q2_separate/summary.csv + per-file metrics json + combined.metrics.json
- out_dir/consensus_q2_points/summary.csv + per-file metrics json + combined.metrics.json
- out_dir/overall_summary.csv  (one wide table merged by (model, variant))
"""

import argparse
import ast
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import shutil


STATE_LABELS = [
    "DISENGAGED_WITHDRAWAL",
    "HESITATION",
    "CONFUSED_BEWILDERMENT",
    "COGNITIVE_CONFLICT",
    "SUPPORTIVE_ENDORSEMENT",
    "FOCUSED_LISTENING",
    "ACTIVE_ENGAGEMENT",
]

CONSENSUS_Q1_LABELS = [
    "NO_CONSENSUS",
    "PSEUDO_CONSENSUS",
    "TRUE_CONSENSUS",
    "UNCERTAIN",
]

CONSENSUS_Q2_LABELS = ["A", "B", "C", "D", "NONE"]

# Known annotation typo/legacy spelling. Applied to both gold and predictions.
LABEL_ALIASES = {
    "PSEUDO_CONSENSU": "PSEUDO_CONSENSUS",
}


# ---------------- IO ----------------

def read_jsonl(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield i, json.loads(line)
            except Exception as e:
                raise RuntimeError(f"[{path}] JSON decode failed at line {i}: {e}")


# ---------------- Parsing helpers ----------------

def normalize_quotes(s: str) -> str:
    return (
        s.replace("“", '"').replace("”", '"')
         .replace("‘", "'").replace("’", "'")
    )


def extract_last_json_object(text: str) -> Optional[str]:
    """Extract last {...} by bracket counting."""
    if not text:
        return None
    text = normalize_quotes(text)
    end = text.rfind("}")
    if end == -1:
        return None
    depth = 0
    for i in range(end, -1, -1):
        ch = text[i]
        if ch == "}":
            depth += 1
        elif ch == "{":
            depth -= 1
            if depth == 0:
                return text[i:end + 1]
    return None


def safe_parse_obj(s: str) -> Optional[Dict[str, Any]]:
    if not s:
        return None
    s = normalize_quotes(s).strip()
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        try:
            obj = ast.literal_eval(s)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None


def is_label_like(s: str) -> bool:
    if not isinstance(s, str):
        return False
    t = s.strip()
    if not (2 <= len(t) <= 120):
        return False
    if any(ch.isspace() for ch in t):
        return False
    return re.fullmatch(r"[A-Z0-9_]+", t) is not None


def parse_bundle_only(row: Dict[str, Any]) -> Optional[str]:
    """
    For non-window tasks (you/consensus): bundle_name from metadata/bundle_name/id/custom_id.
    """
    b = row.get("bundle_name")
    if b:
        return str(b)

    md = row.get("metadata") or {}
    if isinstance(md, dict):
        if md.get("bundle_name"):
            return str(md["bundle_name"])

    rid = row.get("id")
    if isinstance(rid, str) and ":" in rid:
        # id like "consensus:ES2002d_consensus0040"
        return rid.split(":", 1)[1]

    cid = row.get("custom_id")
    if isinstance(cid, str) and "::" in cid:
        parts = cid.split("::")
        # e.g. consensus::BUNDLE::Q1Q2::cot
        if len(parts) >= 2 and parts[1]:
            return parts[1]

    return None


def parse_bundle_and_window(row: Dict[str, Any]) -> Tuple[Optional[str], Optional[int]]:
    """
    Strict for window tasks (state):
    trust window_index / transcript window(\\d+) / custom_id parts[3].
    """
    md = row.get("metadata") or {}
    bundle = None
    widx = None

    if isinstance(md, dict):
        if md.get("bundle_name") is not None:
            bundle = str(md["bundle_name"])
        if md.get("window_index") is not None:
            try:
                widx = int(md["window_index"])
            except Exception:
                widx = None

        if widx is None:
            t = md.get("transcript_txt")
            if isinstance(t, str):
                m = re.search(r"window(\d+)\.txt", t)
                if m:
                    try:
                        widx = int(m.group(1))
                    except Exception:
                        pass

    cid = row.get("custom_id")
    if (bundle is None or widx is None) and isinstance(cid, str) and "::" in cid:
        parts = cid.split("::")
        if bundle is None and len(parts) >= 2 and parts[1]:
            bundle = parts[1]
        if widx is None and len(parts) >= 4:
            try:
                widx = int(parts[3])
            except Exception:
                pass

    return bundle, widx


def normalize_label(v: Any, allowed: Optional[set] = None) -> Optional[str]:
    """Normalize one extracted label and optionally validate it."""
    if v is None:
        return None

    s = str(v).strip().strip('`').strip().strip('"').strip("'")
    if not s:
        return None

    bad = {
        "<OPTION>", "OPTION", "<LABEL>", "LABEL",
        "<ANSWER>", "ANSWER", "YOUR_ANSWER",
        "YOUR ANSWER", "<YOUR_ANSWER>",
        "CONSENSUS_TYPE", "DISSENTER",
    }

    # Canonical label form used throughout MeetingToM.
    s = re.sub(r"[\s\-]+", "_", s.upper())
    s = s.strip(".,;:()[]{}")
    s = LABEL_ALIASES.get(s, s)

    if s in bad:
        return None
    if allowed is not None and s not in allowed:
        return None
    return s


def extract_q_from_text(
    text: str,
    qkey: str,
    allowed: Optional[set] = None,
    allow_single_label: bool = True,
) -> Optional[str]:
    """Extract Q1/Q2 from model OUTPUT text only."""
    if not isinstance(text, str) or not text.strip():
        return None

    t = normalize_quotes(text).strip()
    qkey_u = qkey.upper()
    qkey_l = qkey.lower()

    # Prefer the last JSON object because model wrappers may prepend text.
    for candidate in (extract_last_json_object(t), t):
        if not candidate:
            continue
        obj = safe_parse_obj(candidate)
        if not obj:
            continue
        value = obj.get(qkey_u) if qkey_u in obj else obj.get(qkey_l)
        label = normalize_label(value, allowed)
        if label is not None:
            return label

    # Some runners save only the selected label rather than JSON.
    if allow_single_label:
        label = normalize_label(t, allowed)
        if label is not None and is_label_like(label):
            return label

    return None


def extract_pred_q1q2_from_row(
    row: Dict[str, Any],
    task_name: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """
    Extract model answers from OUTPUT fields only.

    Deliberately ignored:
      - messages / prompt / input / request
      - metadata (including metadata.window_qids)

    This prevents prompt schemas such as {"Q1":"<OPTION>"} and metadata values
    such as {"Q1":"consensus_type"} from being mistaken for predictions.
    """
    task = (task_name or "").lower()
    q1_allowed: Optional[set] = None
    q2_allowed: Optional[set] = None

    if task.startswith("state"):
        q1_allowed = set(STATE_LABELS)
    elif task == "consensus":
        q1_allowed = set(CONSENSUS_Q1_LABELS)
        q2_allowed = set(CONSENSUS_Q2_LABELS)

    out: Dict[str, Optional[str]] = {"Q1": None, "Q2": None}

    def fill_direct(obj: Dict[str, Any]) -> None:
        if out["Q1"] is None:
            for key in ("Q1", "q1"):
                if key in obj:
                    out["Q1"] = normalize_label(obj.get(key), q1_allowed)
                    if out["Q1"] is not None:
                        break
        if out["Q2"] is None:
            for key in ("Q2", "q2"):
                if key in obj:
                    out["Q2"] = normalize_label(obj.get(key), q2_allowed)
                    if out["Q2"] is not None:
                        break

    def fill_text(value: str) -> None:
        if out["Q1"] is None:
            out["Q1"] = extract_q_from_text(value, "Q1", q1_allowed, allow_single_label=True)
        if out["Q2"] is None:
            # A bare single label is ambiguous for Q2, so require JSON/Q2 key.
            out["Q2"] = extract_q_from_text(value, "Q2", q2_allowed, allow_single_label=False)

    # Direct answers at the top level are valid outputs.
    fill_direct(row)

    # Direct scalar OUTPUT fields. Do not inspect prompt/message fields.
    for key in (
        "prediction", "pred", "pred_label", "model_pred", "answer", "label",
        "output_text", "response_text", "generated_text", "completion_text",
    ):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            fill_text(value)

    # Only recurse through known response/result containers.
    output_roots = []
    for key in (
        "output", "result", "parsed", "completion", "response",
        "choices", "candidates", "body", "response_body",
    ):
        if key in row:
            output_roots.append(row[key])

    SKIP_KEYS = {
        "messages", "message_history", "prompt", "prompts", "input", "inputs",
        "request", "request_body", "metadata", "window_qids", "schema",
        "tools", "system", "user",
    }

    def walk_output(x: Any, depth: int = 0) -> None:
        if depth > 10:
            return
        if out["Q1"] is not None and out["Q2"] is not None:
            return

        if isinstance(x, dict):
            fill_direct(x)

            # Common textual response fields.
            for key in ("text", "content", "output_text", "response_text", "generated_text"):
                value = x.get(key)
                if isinstance(value, str) and value.strip():
                    fill_text(value)

            # Traverse response objects, excluding request/prompt echoes.
            for key, value in x.items():
                if key in SKIP_KEYS or key in {"Q1", "q1", "Q2", "q2"}:
                    continue
                walk_output(value, depth + 1)
            return

        if isinstance(x, list):
            for item in x:
                walk_output(item, depth + 1)
            return

        if isinstance(x, str) and x.strip():
            fill_text(x)

    for root in output_roots:
        walk_output(root)

    return out


def extract_pred_label_from_row_state(row: Dict[str, Any]) -> Optional[str]:
    """For state, read Q1 only from actual model-output fields."""
    return extract_pred_q1q2_from_row(row, task_name="state").get("Q1")


# ---------------- Metrics ----------------

def safe_div(n: float, d: float) -> float:
    return 0.0 if d == 0 else (n / d)


def prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    p = safe_div(tp, tp + fp)
    r = safe_div(tp, tp + fn)
    f1 = 0.0 if (p + r) == 0 else (2 * p * r / (p + r))
    return p, r, f1


def compute_metrics(y_true: List[str], y_pred: List[str], labels: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Compute the original classification metrics and add confusion diagnostics.

    Important:
    - Rows are gold labels and columns are predicted labels.
    - Row-normalized values answer: "Of all gold A instances, what fraction
      were predicted as B?"
    - Labels that are never predicted are retained as all-zero columns.
    - Missing/unparseable predictions are NOT inserted here, so the original
      evaluation semantics remain unchanged. They are still reported through
      the existing missing-prediction counters in each task report.
    """
    assert len(y_true) == len(y_pred)
    if labels is None:
        labels = sorted(set(y_true) | set(y_pred))
    else:
        # Keep the user-provided order and remove accidental duplicates.
        labels = list(dict.fromkeys(labels))

    conf = defaultdict(lambda: Counter())
    for t, p in zip(y_true, y_pred):
        conf[t][p] += 1

    total = len(y_true)
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    acc = safe_div(correct, total)

    supports = Counter(y_true)
    predicted_supports = Counter(y_pred)
    per_class = {}

    TP = FP = FN = 0
    for lab in labels:
        tp = conf[lab][lab]
        fp = sum(conf[t][lab] for t in labels if t != lab)
        fn = sum(conf[lab][p] for p in labels if p != lab)

        p, r, f1 = prf(tp, fp, fn)
        per_class[lab] = {
            "precision": p,
            "recall": r,
            "f1": f1,
            "support": supports.get(lab, 0),
            "predicted_support": predicted_supports.get(lab, 0),
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }
        TP += tp
        FP += fp
        FN += fn

    micro_p, micro_r, micro_f1 = prf(TP, FP, FN)
    macro_p = sum(per_class[l]["precision"] for l in labels) / len(labels) if labels else 0.0
    macro_r = sum(per_class[l]["recall"] for l in labels) / len(labels) if labels else 0.0
    macro_f1 = sum(per_class[l]["f1"] for l in labels) / len(labels) if labels else 0.0

    # Full raw matrix. Keeping every label as a column makes classes that the
    # model never predicts visible as all-zero columns.
    confusion_raw = {
        gold: {pred: int(conf[gold][pred]) for pred in labels}
        for gold in labels
    }

    # Normalize each gold-label row independently. Each non-empty row sums to 1.
    confusion_row_normalized = {}
    for gold in labels:
        denom = supports.get(gold, 0)
        confusion_row_normalized[gold] = {
            pred: safe_div(conf[gold][pred], denom)
            for pred in labels
        }

    # Directional off-diagonal errors, e.g. gold HESITATION -> predicted FOCUSED_LISTENING.
    confusion_pairs = []
    for gold in labels:
        support = supports.get(gold, 0)
        if support <= 0:
            continue
        for pred in labels:
            if pred == gold:
                continue
            count = int(conf[gold][pred])
            if count <= 0:
                continue
            confusion_pairs.append({
                "gold_label": gold,
                "predicted_as": pred,
                "count": count,
                "support": support,
                "rate": safe_div(count, support),
            })

    # Sort primarily by within-gold-class error rate, then by count.
    confusion_pairs.sort(
        key=lambda x: (-x["rate"], -x["count"], x["gold_label"], x["predicted_as"])
    )

    # One dominant confusion destination for each gold label.
    top_confusion_by_gold = []
    for gold in labels:
        candidates = [x for x in confusion_pairs if x["gold_label"] == gold]
        if candidates:
            top_confusion_by_gold.append(candidates[0])

    return {
        "n": total,
        "correct": correct,
        "acc": acc,
        "micro": {"precision": micro_p, "recall": micro_r, "f1": micro_f1},
        "macro": {"precision": macro_p, "recall": macro_r, "f1": macro_f1},
        "labels": labels,
        "per_class": per_class,
        "confusion_raw": confusion_raw,
        "confusion_row_normalized": confusion_row_normalized,
        "confusion_pairs": confusion_pairs,
        "top_confusion_by_gold": top_confusion_by_gold,
        "never_predicted_labels": [
            lab for lab in labels if predicted_supports.get(lab, 0) == 0
        ],
    }


def detect_task_from_gt_row(row: Dict[str, Any]) -> Optional[str]:
    t = row.get("task")
    if isinstance(t, str) and t.strip():
        return t.strip()

    rid = row.get("id")
    if isinstance(rid, str) and ":" in rid:
        return rid.split(":", 1)[0].strip()

    return None


def load_gold_multi(gt_paths: List[Path]) -> Dict[str, Any]:
    """
    Return:
      gold_state: Dict[(bundle,widx)->label]  (widx 0/1)
      gold_you:   Dict[bundle->{"Q1":..,"Q2":..}]
      gold_cons:  Dict[bundle->{"Q1":..,"Q2":..}]
    """
    gold_state: Dict[Tuple[str, int], str] = {}
    gold_you: Dict[str, Dict[str, str]] = {}
    gold_cons: Dict[str, Dict[str, str]] = {}

    for gt_path in gt_paths:
        for _, row in read_jsonl(gt_path):
            task = detect_task_from_gt_row(row)
            if not task:
                continue

            bundle = row.get("bundle_name")
            if not bundle:
                rid = row.get("id")
                if isinstance(rid, str) and ":" in rid:
                    bundle = rid.split(":", 1)[1]
            if not bundle:
                continue
            bundle = str(bundle)

            ans = row.get("answers") or {}
            if not isinstance(ans, dict):
                continue

            tnorm = task.lower()

            if tnorm.startswith("state"):
                if ans.get("Q1") is not None:
                    gold_state[(bundle, 0)] = normalize_label(ans["Q1"], set(STATE_LABELS)) or str(ans["Q1"])
                if ans.get("Q2") is not None:
                    gold_state[(bundle, 1)] = normalize_label(ans["Q2"], set(STATE_LABELS)) or str(ans["Q2"])

            elif tnorm == "you":
                d = gold_you.setdefault(bundle, {})
                if ans.get("Q1") is not None:
                    d["Q1"] = str(ans["Q1"])
                if ans.get("Q2") is not None:
                    d["Q2"] = str(ans["Q2"])

            elif tnorm == "consensus":
                d = gold_cons.setdefault(bundle, {})
                if ans.get("Q1") is not None:
                    d["Q1"] = normalize_label(ans["Q1"], set(CONSENSUS_Q1_LABELS)) or str(ans["Q1"])
                if ans.get("Q2") is not None:
                    d["Q2"] = normalize_label(ans["Q2"], set(CONSENSUS_Q2_LABELS)) or str(ans["Q2"])

    return {"state": gold_state, "you": gold_you, "consensus": gold_cons}


# ---------------- Pred loading ----------------

def load_pred_state_windows(
    pred_path: Path,
    keep_only_widx: Optional[set],
    dump_missing_n: int,
    dump_dir: Path
) -> Tuple[Dict[Tuple[str, int], str], Dict[str, int]]:
    """
    Return pred[(bundle,widx)] = label
    label always extracted from row's Q1 field (even for window1)
    """
    pred: Dict[Tuple[str, int], str] = {}
    stats = Counter()
    dumped = 0
    dump_fp = dump_dir / f"{pred_path.stem}.label_missing_examples.jsonl"

    for line_no, row in read_jsonl(pred_path):
        stats["rows_total"] += 1

        bundle, widx = parse_bundle_and_window(row)
        if bundle is None or widx is None:
            stats["rows_missing_key_or_widx"] += 1
            continue
        stats["rows_key_ok"] += 1

        if keep_only_widx is not None and widx not in keep_only_widx:
            stats["rows_widx_filtered_out"] += 1
            continue

        label = extract_pred_label_from_row_state(row)
        if label is None:
            stats["rows_missing_label"] += 1
            if dumped < dump_missing_n:
                dumped += 1
                with dump_fp.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(
                        {"line_no": line_no, "bundle_name": bundle, "window_index": widx, "row": row},
                        ensure_ascii=False
                    ) + "\n")
            continue

        stats["rows_label_ok"] += 1
        key = (bundle, widx)
        if key in pred:
            stats["rows_duplicate_key_overwrite"] += 1
        pred[key] = label
        stats["rows_used"] += 1

    if dumped == 0 and dump_fp.exists():
        dump_fp.unlink(missing_ok=True)

    return pred, dict(stats)


def load_pred_q1q2_by_bundle(
    pred_path: Path,
    dump_missing_n: int,
    dump_dir: Path,
    task_name: str
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, int]]:
    """
    For you/consensus: usually one row per bundle.
    Return pred_q1[bundle], pred_q2[bundle], stats
    """
    pred_q1: Dict[str, str] = {}
    pred_q2: Dict[str, str] = {}
    stats = Counter()
    dumped_q1 = 0
    dumped_q2 = 0
    dump_fp_q1 = dump_dir / f"{pred_path.stem}.Q1_missing_examples.jsonl"
    dump_fp_q2 = dump_dir / f"{pred_path.stem}.Q2_missing_examples.jsonl"

    for line_no, row in read_jsonl(pred_path):
        stats["rows_total"] += 1

        bundle = parse_bundle_only(row)
        if not bundle:
            stats["rows_missing_bundle"] += 1
            continue
        bundle = str(bundle)
        stats["rows_bundle_ok"] += 1

        labs = extract_pred_q1q2_from_row(row, task_name=task_name)
        q1 = labs.get("Q1")
        q2 = labs.get("Q2")

        if q1 is None:
            stats["rows_missing_Q1"] += 1
            if dumped_q1 < dump_missing_n:
                dumped_q1 += 1
                with dump_fp_q1.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"line_no": line_no, "bundle_name": bundle, "row": row}, ensure_ascii=False) + "\n")
        else:
            if bundle in pred_q1:
                stats["rows_duplicate_bundle_overwrite_Q1"] += 1
            pred_q1[bundle] = str(q1)

        if q2 is None:
            stats["rows_missing_Q2"] += 1
            if dumped_q2 < dump_missing_n:
                dumped_q2 += 1
                with dump_fp_q2.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"line_no": line_no, "bundle_name": bundle, "row": row}, ensure_ascii=False) + "\n")
        else:
            if bundle in pred_q2:
                stats["rows_duplicate_bundle_overwrite_Q2"] += 1
            pred_q2[bundle] = str(q2)

        stats["rows_used_any"] += 1

    if dumped_q1 == 0 and dump_fp_q1.exists():
        dump_fp_q1.unlink(missing_ok=True)
    if dumped_q2 == 0 and dump_fp_q2.exists():
        dump_fp_q2.unlink(missing_ok=True)

    return pred_q1, pred_q2, dict(stats)


# ---------------- Overall summary helpers ----------------

def extract_model_variant_from_fname(fname: str) -> Tuple[str, str]:
    """
    Parse (model, variant) from filename.
    Prefer: <model>_<task>_<variant>...
      e.g. gemini-3-pro-preview-new_state_noprompt.jsonl
           gemini-3-flash-preview_state_eot__data_xxx.jsonl
    """
    base = fname[:-5] if fname.endswith(".jsonl") else fname

    m = re.search(r"^(.*)_(state|you|consensus)_(cot|eot|noprompt)\b", base)
    if m:
        return m.group(1), m.group(3)

    mv = re.search(r"_(cot|eot|noprompt)\b", base)
    variant = mv.group(1) if mv else "NA"
    model = re.sub(r"_(state|you|consensus)\b.*$", "", base)
    model = model if model else base
    return model, variant


def ensure_master_row(master: Dict[Tuple[str, str], Dict[str, Any]], model: str, variant: str) -> Dict[str, Any]:
    key = (model, variant)
    if key not in master:
        master[key] = {"model": model, "variant": variant}
    return master[key]


def flatten_simple(prefix: str, m: Dict[str, Any]) -> Dict[str, Any]:
    return {
        f"{prefix}n": m["n"],
        f"{prefix}correct": m["correct"],
        f"{prefix}acc": f"{m['acc']:.6f}",
        f"{prefix}micro_p": f"{m['micro']['precision']:.6f}",
        f"{prefix}micro_r": f"{m['micro']['recall']:.6f}",
        f"{prefix}micro_f1": f"{m['micro']['f1']:.6f}",
        f"{prefix}macro_p": f"{m['macro']['precision']:.6f}",
        f"{prefix}macro_r": f"{m['macro']['recall']:.6f}",
        f"{prefix}macro_f1": f"{m['macro']['f1']:.6f}",
    }


# ---------------- File selection helpers ----------------

def file_matches_task(fname: str, task: str) -> bool:
    n = fname.lower()
    task = task.lower()
    if task == "state":
        return ("state" in n) and ("you" not in n) and ("consensus" not in n)
    if task == "you":
        return "you" in n
    if task == "consensus":
        return "consensus" in n
    return False


# ---------------- Main ----------------

def main():
    ap = argparse.ArgumentParser(
        description="Evaluate 3 tasks: state (merged), you (Q1/Q2 separate), consensus (two-step points + conditional Q2)."
    )
    ap.add_argument("--gt", action="append", required=True,
                    help="GT jsonl path(s). You can pass multiple --gt for mixed tasks.")
    ap.add_argument("--pred_dir", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--ext", default=".jsonl")
    ap.add_argument("--tasks", default="state,you,consensus",
                    help="Comma-separated tasks to run: state,you,consensus")
    ap.add_argument("--only_windows", default="0,1", help="For state only (default 0,1)")
    ap.add_argument("--dump_missing_n", type=int, default=3)
    ap.add_argument("--labels", default=None, help='Optional fixed label ordering: "A,B,C" (applies to all)')
    args = ap.parse_args()

    gt_paths = [Path(p) for p in args.gt]
    pred_dir = Path(args.pred_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    keep_widx = set(int(x.strip()) for x in args.only_windows.split(",") if x.strip() != "")
    fixed_labels = args.labels.split(",") if args.labels else None
    tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]

    gold = load_gold_multi(gt_paths)
    if not any(gold[t] for t in gold):
        raise RuntimeError("No gold parsed from provided --gt files.")

    all_files = sorted([p for p in pred_dir.iterdir() if p.is_file() and p.name.endswith(args.ext)])
    if not all_files:
        raise RuntimeError(f"No *{args.ext} found in {pred_dir}")

    master: Dict[Tuple[str, str], Dict[str, Any]] = {}

    # ===================== state =====================
    if "state" in tasks:
        task_out = out_dir / "state_task1_merged"
        task_out.mkdir(parents=True, exist_ok=True)
        dump_dir = task_out / "debug_dumps"
        dump_dir.mkdir(parents=True, exist_ok=True)

        gold_state: Dict[Tuple[str, int], str] = gold["state"]
        if not gold_state:
            print("[state] No gold found; skipping.")
        else:
            files = [p for p in all_files if file_matches_task(p.name, "state")]
            if not files:
                print("[state] No pred files matched; skipping.")
            else:
                summary_rows: List[Dict[str, Any]] = []
                combined_true: List[str] = []
                combined_pred: List[str] = []

                for fp in files:
                    pred, pstats = load_pred_state_windows(fp, keep_widx, args.dump_missing_n, dump_dir)

                    keys = sorted(set(gold_state) & set(pred))
                    y_true = [gold_state[k] for k in keys]
                    y_pred = [pred[k] for k in keys]

                    missing_pred_for_gold = len(set(gold_state) - set(pred))
                    missing_gold_for_pred = len(set(pred) - set(gold_state))

                    m = compute_metrics(y_true, y_pred, labels=(fixed_labels or STATE_LABELS))

                    report = {
                        "task": "state_task1_merged",
                        "file_name": fp.name,
                        "file_path": str(fp),
                        "eval_definition": (
                            "Merged Task1: window_index=0->GT.answers.Q1, window_index=1->GT.answers.Q2; "
                            "prediction label extracted from model output Q1 even for window1."
                        ),
                        "included_window_index": sorted(list(keep_widx)),
                        "parse_stats": pstats,
                        "missing_pred_for_gold": missing_pred_for_gold,
                        "missing_gold_for_pred": missing_gold_for_pred,
                        **m,
                    }

                    out_json = task_out / f"{fp.stem}.metrics.json"
                    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


                    row = {
                        "file_name": fp.name,
                        "missing_pred_for_gold": missing_pred_for_gold,
                        "missing_gold_for_pred": missing_gold_for_pred,
                        "rows_total": pstats.get("rows_total", 0),
                        "rows_used": pstats.get("rows_used", 0),
                        "rows_missing_key_or_widx": pstats.get("rows_missing_key_or_widx", 0),
                        "rows_missing_label": pstats.get("rows_missing_label", 0),
                        "rows_widx_filtered_out": pstats.get("rows_widx_filtered_out", 0),
                        "metrics_json": out_json.name,
                    }
                    row.update(flatten_simple("", m))
                    summary_rows.append(row)

                    combined_true.extend(y_true)
                    combined_pred.extend(y_pred)

                    # master
                    model, variant = extract_model_variant_from_fname(fp.name)
                    mr = ensure_master_row(master, model, variant)
                    mr["state_file"] = fp.name
                    mr["state_n"] = m["n"]
                    mr["state_acc"] = f"{m['acc']:.6f}"
                    mr["state_macro_f1"] = f"{m['macro']['f1']:.6f}"

                    print(f"[state][{fp.name}] aligned_n={m['n']} rows_total={pstats.get('rows_total',0)} "
                          f"rows_used={pstats.get('rows_used',0)} label_missing={pstats.get('rows_missing_label',0)}")

                # summary.csv
                summary_csv = task_out / "summary.csv"
                with summary_csv.open("w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(summary_rows)

                # combined
                cm = compute_metrics(combined_true, combined_pred, labels=(fixed_labels or STATE_LABELS))
                (task_out / "combined.metrics.json").write_text(
                    json.dumps({"task": "state_task1_merged_combined", **cm}, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                print(f"[state] Wrote: {task_out}")

    # ===================== you =====================
    if "you" in tasks:
        task_out = out_dir / "you_q1q2_separate"
        task_out.mkdir(parents=True, exist_ok=True)
        dump_dir = task_out / "debug_dumps"
        dump_dir.mkdir(parents=True, exist_ok=True)

        gold_you: Dict[str, Dict[str, str]] = gold["you"]
        if not gold_you:
            print("[you] No gold found; skipping.")
        else:
            files = [p for p in all_files if file_matches_task(p.name, "you")]
            if not files:
                print("[you] No pred files matched; skipping.")
            else:
                summary_rows = []
                combined_true_q1, combined_pred_q1 = [], []
                combined_true_q2, combined_pred_q2 = [], []

                for fp in files:
                    pred_q1, pred_q2, pstats = load_pred_q1q2_by_bundle(fp, args.dump_missing_n, dump_dir, task_name="you")

                    # Q1
                    keys_q1 = sorted([b for b in gold_you.keys() if "Q1" in gold_you[b] and b in pred_q1])
                    y_true_q1 = [gold_you[b]["Q1"] for b in keys_q1]
                    y_pred_q1 = [pred_q1[b] for b in keys_q1]
                    m_q1 = compute_metrics(y_true_q1, y_pred_q1, labels=fixed_labels)

                    missing_pred_for_gold_q1 = sum(1 for b in gold_you.keys() if "Q1" in gold_you[b] and b not in pred_q1)
                    missing_gold_for_pred_q1 = sum(1 for b in pred_q1.keys() if b not in gold_you or "Q1" not in gold_you[b])

                    # Q2
                    keys_q2 = sorted([b for b in gold_you.keys() if "Q2" in gold_you[b] and b in pred_q2])
                    y_true_q2 = [gold_you[b]["Q2"] for b in keys_q2]
                    y_pred_q2 = [pred_q2[b] for b in keys_q2]
                    m_q2 = compute_metrics(y_true_q2, y_pred_q2, labels=fixed_labels)

                    missing_pred_for_gold_q2 = sum(1 for b in gold_you.keys() if "Q2" in gold_you[b] and b not in pred_q2)
                    missing_gold_for_pred_q2 = sum(1 for b in pred_q2.keys() if b not in gold_you or "Q2" not in gold_you[b])

                    report = {
                        "task": "you_q1q2_separate",
                        "file_name": fp.name,
                        "file_path": str(fp),
                        "eval_definition": "YOU: Q1 and Q2 evaluated separately (no gating).",
                        "parse_stats": pstats,
                        "Q1": {
                            "missing_pred_for_gold": missing_pred_for_gold_q1,
                            "missing_gold_for_pred": missing_gold_for_pred_q1,
                            **m_q1
                        },
                        "Q2": {
                            "missing_pred_for_gold": missing_pred_for_gold_q2,
                            "missing_gold_for_pred": missing_gold_for_pred_q2,
                            **m_q2
                        }
                    }

                    out_json = task_out / f"{fp.stem}.metrics.json"
                    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

                    row = {
                        "file_name": fp.name,
                        "rows_total": pstats.get("rows_total", 0),
                        "rows_missing_bundle": pstats.get("rows_missing_bundle", 0),
                        "rows_missing_Q1": pstats.get("rows_missing_Q1", 0),
                        "rows_missing_Q2": pstats.get("rows_missing_Q2", 0),
                        "Q1_missing_pred_for_gold": missing_pred_for_gold_q1,
                        "Q1_missing_gold_for_pred": missing_gold_for_pred_q1,
                        "Q2_missing_pred_for_gold": missing_pred_for_gold_q2,
                        "Q2_missing_gold_for_pred": missing_gold_for_pred_q2,
                        "metrics_json": out_json.name,
                    }
                    row.update(flatten_simple("Q1_", m_q1))
                    row.update(flatten_simple("Q2_", m_q2))
                    summary_rows.append(row)

                    combined_true_q1.extend(y_true_q1)
                    combined_pred_q1.extend(y_pred_q1)
                    combined_true_q2.extend(y_true_q2)
                    combined_pred_q2.extend(y_pred_q2)

                    # master
                    model, variant = extract_model_variant_from_fname(fp.name)
                    mr = ensure_master_row(master, model, variant)
                    mr["you_file"] = fp.name
                    mr["you_q1_acc"] = f"{m_q1['acc']:.6f}"
                    mr["you_q2_acc"] = f"{m_q2['acc']:.6f}"
                    mr["you_q1_macro_f1"] = f"{m_q1['macro']['f1']:.6f}"
                    mr["you_q2_macro_f1"] = f"{m_q2['macro']['f1']:.6f}"

                    print(f"[you][{fp.name}] Q1_n={m_q1['n']} Q2_n={m_q2['n']} rows_total={pstats.get('rows_total',0)}")

                summary_csv = task_out / "summary.csv"
                with summary_csv.open("w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(summary_rows)

                combined_report = {
                    "task": "you_combined",
                    "Q1": compute_metrics(combined_true_q1, combined_pred_q1, labels=fixed_labels),
                    "Q2": compute_metrics(combined_true_q2, combined_pred_q2, labels=fixed_labels),
                }
                (task_out / "combined.metrics.json").write_text(
                    json.dumps(combined_report, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                print(f"[you] Wrote: {task_out}")

    # ===================== consensus =====================
    if "consensus" in tasks:
        task_out = out_dir / "consensus_q2_points"
        task_out.mkdir(parents=True, exist_ok=True)
        dump_dir = task_out / "debug_dumps"
        dump_dir.mkdir(parents=True, exist_ok=True)

        gold_cons: Dict[str, Dict[str, str]] = gold["consensus"]
        if not gold_cons:
            print("[consensus] No gold found; skipping.")
        else:
            files = [p for p in all_files if file_matches_task(p.name, "consensus")]
            if not files:
                print("[consensus] No pred files matched; skipping.")
            else:
                summary_rows = []
                combined_true_q1, combined_pred_q1 = [], []
                combined_true_q2_cond, combined_pred_q2_cond = [], []
                combined_points_score = 0
                combined_points_max = 0

                for fp in files:
                    pred_q1, pred_q2, pstats = load_pred_q1q2_by_bundle(fp, args.dump_missing_n, dump_dir, task_name="consensus")

                    # Q1 normal metrics
                    keys_q1 = sorted([b for b in gold_cons.keys() if "Q1" in gold_cons[b] and b in pred_q1])
                    y_true_q1 = [gold_cons[b]["Q1"] for b in keys_q1]
                    y_pred_q1 = [pred_q1[b] for b in keys_q1]
                    m_q1 = compute_metrics(y_true_q1, y_pred_q1, labels=(fixed_labels or CONSENSUS_Q1_LABELS))

                    missing_pred_for_gold_q1 = sum(1 for b in gold_cons.keys() if "Q1" in gold_cons[b] and b not in pred_q1)
                    missing_gold_for_pred_q1 = sum(1 for b in pred_q1.keys() if b not in gold_cons or "Q1" not in gold_cons[b])

                    # Q2 conditional (only evaluate Q2 on bundles where Q1 is correct)
                    keys_q2_all = sorted([b for b in gold_cons.keys() if "Q2" in gold_cons[b] and b in pred_q1 and b in pred_q2])
                    keys_q2_cond = []
                    y_true_q2_cond = []
                    y_pred_q2_cond = []

                    # two-step points score
                    points_score = 0
                    points_max = 0

                    for b in keys_q2_all:
                        q1_true = gold_cons[b].get("Q1")
                        q2_true = gold_cons[b].get("Q2")
                        q1_pred = pred_q1.get(b)
                        q2_pred = pred_q2.get(b)

                        if q1_true is None or q2_true is None or q1_pred is None or q2_pred is None:
                            continue

                        # 2 points per bundle when both Qs exist and are predicted
                        points_max += 2

                        q1_ok = (q1_pred == q1_true)
                        if q1_ok:
                            points_score += 1  # Q1 point
                            # conditional Q2 eval set
                            keys_q2_cond.append(b)
                            y_true_q2_cond.append(q2_true)
                            y_pred_q2_cond.append(q2_pred)

                            if q2_pred == q2_true:
                                points_score += 1  # Q2 point only if Q1 ok AND Q2 ok
                        else:
                            # Q1 wrong => no points; Q2 cannot earn points
                            pass

                    # Q2 conditional metrics
                    m_q2_cond = compute_metrics(y_true_q2_cond, y_pred_q2_cond, labels=(fixed_labels or CONSENSUS_Q2_LABELS))

                    # missing counts
                    missing_pred_for_gold_q2 = sum(1 for b in gold_cons.keys()
                                                   if "Q2" in gold_cons[b] and (b not in pred_q1 or b not in pred_q2))
                    missing_gold_for_pred_q2 = sum(1 for b in pred_q2.keys()
                                                   if b not in gold_cons or "Q2" not in gold_cons[b])

                    points_acc = safe_div(points_score, points_max) if points_max > 0 else 0.0

                    report = {
                        "task": "consensus_q2_points",
                        "file_name": fp.name,
                        "file_path": str(fp),
                        "eval_definition": (
                            "CONSENSUS: two-step points scoring. "
                            "Per bundle: +1 if Q1 correct; +1 if (Q1 correct AND Q2 correct). "
                            "Also reports Q2 conditional metrics on subset where Q1 correct."
                        ),
                        "parse_stats": pstats,
                        "Q1": {
                            "missing_pred_for_gold": missing_pred_for_gold_q1,
                            "missing_gold_for_pred": missing_gold_for_pred_q1,
                            **m_q1
                        },
                        "Q2_conditional_on_Q1_correct": {
                            "missing_pred_for_gold": missing_pred_for_gold_q2,
                            "missing_gold_for_pred": missing_gold_for_pred_q2,
                            **m_q2_cond
                        },
                        "points": {
                            "score": points_score,
                            "max": points_max,
                            "acc": points_acc
                        }
                    }

                    out_json = task_out / f"{fp.stem}.metrics.json"
                    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

                    # Task 3 confusion table refers to Q1: consensus type.

                    row = {
                        "file_name": fp.name,
                        "rows_total": pstats.get("rows_total", 0),
                        "rows_missing_bundle": pstats.get("rows_missing_bundle", 0),
                        "rows_missing_Q1": pstats.get("rows_missing_Q1", 0),
                        "rows_missing_Q2": pstats.get("rows_missing_Q2", 0),
                        "Q1_missing_pred_for_gold": missing_pred_for_gold_q1,
                        "Q1_missing_gold_for_pred": missing_gold_for_pred_q1,
                        "Q2_missing_pred_for_gold": missing_pred_for_gold_q2,
                        "Q2_missing_gold_for_pred": missing_gold_for_pred_q2,
                        "points_score": points_score,
                        "points_max": points_max,
                        "points_acc": f"{points_acc:.6f}",
                        "metrics_json": out_json.name,
                    }
                    row.update(flatten_simple("Q1_", m_q1))
                    row.update(flatten_simple("Q2c_", m_q2_cond))
                    summary_rows.append(row)

                    combined_true_q1.extend(y_true_q1)
                    combined_pred_q1.extend(y_pred_q1)
                    combined_true_q2_cond.extend(y_true_q2_cond)
                    combined_pred_q2_cond.extend(y_pred_q2_cond)
                    combined_points_score += points_score
                    combined_points_max += points_max

                    # master
                    model, variant = extract_model_variant_from_fname(fp.name)
                    mr = ensure_master_row(master, model, variant)
                    mr["consensus_file"] = fp.name
                    mr["cons_q1_acc"] = f"{m_q1['acc']:.6f}"
                    mr["cons_q2_cond_acc"] = f"{m_q2_cond['acc']:.6f}"
                    mr["cons_points_acc"] = f"{points_acc:.6f}"

                    print(f"[consensus][{fp.name}] Q1_n={m_q1['n']} Q2c_n={m_q2_cond['n']} "
                          f"points={points_score}/{points_max} rows_total={pstats.get('rows_total',0)}")

                summary_csv = task_out / "summary.csv"
                with summary_csv.open("w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(summary_rows)

                combined_report = {
                    "task": "consensus_combined",
                    "Q1": compute_metrics(combined_true_q1, combined_pred_q1, labels=(fixed_labels or CONSENSUS_Q1_LABELS)),
                    "Q2_conditional_on_Q1_correct": compute_metrics(combined_true_q2_cond, combined_pred_q2_cond, labels=(fixed_labels or CONSENSUS_Q2_LABELS)),
                    "points": {
                        "score": combined_points_score,
                        "max": combined_points_max,
                        "acc": safe_div(combined_points_score, combined_points_max) if combined_points_max > 0 else 0.0
                    }
                }
                (task_out / "combined.metrics.json").write_text(
                    json.dumps(combined_report, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                print(f"[consensus] Wrote: {task_out}")

    # ===================== overall master summary =====================
    overall_csv = out_dir / "overall_summary.csv"
    fieldnames = [
            "model",
            "variant",
            "state_acc",
            "state_macro_f1",
            "you_q1_acc",
            "you_q1_macro_f1",
            "you_q2_acc",
            "you_q2_macro_f1",
            "cons_q1_acc",
            "cons_q2_cond_acc",
            "cons_points_acc",
        ]
    rows = sorted(master.values(), key=lambda r: (r.get("model", ""), r.get("variant", "")))
    with overall_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    # Public release: keep only the final core-metrics table.
    # Scoring above is unchanged from the validated v4 evaluator.
    for auxiliary_dir in (
        "state_task1_merged",
        "you_q1q2_separate",
        "consensus_q2_points",
    ):
        shutil.rmtree(
            out_dir / auxiliary_dir,
            ignore_errors=True,
        )

    print(f"\nAll done. Output root: {out_dir}")
    print(f"Overall summary: {overall_csv}")


if __name__ == "__main__":
    main()