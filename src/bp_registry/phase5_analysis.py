"""Read-only, source-qualified Phase 5 shot tables and Plotly presentation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from html import escape
import json
from pathlib import Path
from typing import Any, Mapping

from .canonical.budgets import WorkVector
from .ledger import read_canonical_events


ARMS = ("identity", "guided_decimation", "impulse", "freezing", "syndrome_flip", "sign_flip", "restart_belief")
OUTCOMES = ("exact", "stabilizer_equivalent", "logical_failure", "invalid_syndrome", "outcome_unavailable")
WORK_FIELDS = ("check_to_variable_updates", "variable_to_check_updates", "intervention_actions", "transformations", "original_checks")
_RESULT_ROOT = Path(__file__).resolve().parents[2] / "data/results/phase5-interventions"


@dataclass(frozen=True, slots=True)
class AttemptRow:
    shot_id: int
    arm: str
    order: int
    termination: str
    payload_json: str
    qualification: str

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self.payload_json)


@dataclass(frozen=True, slots=True)
class ShotArmRow:
    shot_id: int
    sample_identity: str
    arm: str
    manifest_sha256: str
    code_id: str
    source_revision: str
    variant: str
    qualification: str
    native_availability: str
    assessment_status: str
    outcome: str
    termination: str
    selected_candidate: tuple[int, ...] | None
    selected_origin_json: str
    original_valid: bool | None
    attempt_count: int
    work_json: str

    @property
    def work(self) -> dict[str, int]:
        return json.loads(self.work_json)

    @property
    def selected_origin(self) -> Any:
        return json.loads(self.selected_origin_json)


@dataclass(frozen=True, slots=True)
class Phase5Dataset:
    rows: tuple[ShotArmRow, ...]
    attempts: tuple[AttemptRow, ...]
    ledger_sha256: str
    design_digest: str
    source_root: str
    assessment_status: str

    def shot(self, shot_id: int) -> tuple[ShotArmRow, ...]:
        return tuple(row for row in self.rows if row.shot_id == shot_id)

    def attempts_for(self, shot_id: int, arm: str) -> tuple[AttemptRow, ...]:
        return tuple(row for row in self.attempts if row.shot_id == shot_id and row.arm == arm)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Phase 5 evidence JSON must be an object")
    return value


def load_verified_evidence(source: str | Path) -> Phase5Dataset:
    """Check confined persisted identities and build immutable, complete shot rows."""
    root = Path(source).resolve(strict=True)
    permitted = _RESULT_ROOT.resolve(strict=True)
    if root != permitted / "b1-mechanism-pilot" and root != permitted / "b1-calibration":
        raise ValueError("Phase 5 analysis only reads the two confined B1 evidence roots")
    result = _read_json(root / "result.json")
    if result.get("code_id") != "b1-ghp-882" or result.get("relation") != "pilot_adaptation" or result.get("assessment_status") != "not_assessed":
        raise ValueError("Phase 5 analysis requires qualified B1 pilot evidence")
    if tuple(result.get("arm_order", ())) != ARMS or result.get("shot_ids") != list(range(4 if result.get("stage") == "calibration" else 16)):
        raise ValueError("Phase 5 result has the wrong matched arm or shot set")
    ledger = root / "events.jsonl"
    actual_hash = sha256(ledger.read_bytes()).hexdigest()
    if actual_hash != result.get("ledger_sha256"):
        raise ValueError("Phase 5 aggregate ledger digest differs from result evidence")
    events = read_canonical_events(ledger)
    rows: list[ShotArmRow] = []
    attempts: list[AttemptRow] = []
    for arm in ARMS:
        arm_root = root / arm
        manifest = _read_json(arm_root / "manifest.json")
        arm_result = _read_json(arm_root / "result.json")
        arm_ledger = arm_root / "events.jsonl"
        if sha256(arm_ledger.read_bytes()).hexdigest() != arm_result.get("ledger_sha256"):
            raise ValueError(f"{arm} ledger digest differs from its public result")
        arm_evidence = result.get("arm_evidence", {}).get(arm, {})
        if (manifest.get("run_id") != f"phase5-b1-{result['stage']}-{arm}"
                or arm_result.get("manifest_sha256") != arm_evidence.get("manifest_sha256")
                or manifest.get("intervention", {}).get("kind") != arm
                or manifest.get("evidence", {}).get("assessment_status") != "not_assessed"):
            raise ValueError(f"{arm} public manifest and result identity differ")
        source = manifest["intervention"]
        for shot_id in result["shot_ids"]:
            stream = [event for event in events if event["run_id"] == manifest["run_id"] and event["shot_id"] == shot_id]
            if not stream or stream[0]["kind"] != "shot_begin" or stream[-1]["kind"] != "termination":
                raise ValueError(f"{arm} shot {shot_id} lacks complete structural evidence")
            if any(event["ledger_version"] != 5 for event in stream):
                raise ValueError("Phase 5 analysis requires only version-five events")
            sample_identity = stream[0]["sample_seed_identity"]
            if sample_identity != result["physical_sample_identities"][str(shot_id)]:
                raise ValueError("matched physical sample identity differs across arms")
            identity = stream[0]["data"]["identity"]
            if (identity.get("manifest_sha256") != arm_result["manifest_sha256"]
                    or identity.get("source_variant") != source["variant"]
                    or identity.get("qualification") != source["qualification"]
                    or any(event["data"]["identity"] != identity for event in stream)):
                raise ValueError("Phase 5 shot identity differs within or across evidence")
            work_events = [event for event in stream if event["kind"] == "work"]
            if len(work_events) != 1:
                raise ValueError("Phase 5 shot requires one typed work event")
            work_payload = work_events[0]["data"]["payload"]
            leaves = work_payload["leaves"]
            if len({leaf["leaf_id"] for leaf in leaves}) != len(leaves):
                raise ValueError("Phase 5 analysis found duplicate work leaves")
            total = WorkVector.from_evidence(work_payload["work_vector"], structural_event_version=4)
            if total != WorkVector.sum(WorkVector.from_evidence(leaf["work_vector"], structural_event_version=4) for leaf in leaves):
                raise ValueError("Phase 5 analysis found an incorrect work leaf reduction")
            terminal = stream[-1]["data"]["payload"]
            selected = terminal["candidate"]
            original_checks = [event["data"]["payload"] for event in stream if event["kind"] == "original_check"]
            selected_original_valid = None if selected is None else any(
                check.get("candidate") == selected and check.get("valid") is True for check in original_checks
            )
            if selected is not None and not selected_original_valid:
                raise ValueError("Phase 5 selected candidate lacks an original-validity check")
            arm_attempts = [event["data"]["payload"] for event in stream if event["kind"] == "attempt"]
            for order, payload in enumerate(arm_attempts):
                attempts.append(AttemptRow(
                    shot_id, arm, order,
                    str(payload.get("termination", payload.get("terminal_reason", "not_applicable"))),
                    json.dumps(payload, sort_keys=True, separators=(",", ":")),
                    source["qualification"],
                ))
            rows.append(ShotArmRow(
                shot_id, sample_identity, arm, arm_result["manifest_sha256"],
                manifest["artifact"]["code_id"], source["source_revision"], source["variant"],
                source["qualification"], source["native_availability"], "not_assessed",
                terminal["outcome"] or "outcome_unavailable", stream[-1]["termination"],
                None if selected is None else tuple(int(bit) for bit in selected),
                json.dumps(terminal["selected_origin"], sort_keys=True, separators=(",", ":")),
                selected_original_valid, len(arm_attempts),
                json.dumps(work_payload["work_vector"], sort_keys=True, separators=(",", ":")),
            ))
    if len(rows) != len(ARMS) * len(result["shot_ids"]):
        raise ValueError("Phase 5 analysis has incomplete matched shot rows")
    return Phase5Dataset(tuple(sorted(rows, key=lambda row: (row.shot_id, ARMS.index(row.arm)))),
                         tuple(sorted(attempts, key=lambda row: (row.shot_id, ARMS.index(row.arm), row.order))),
                         actual_hash, result["design_digest"], str(root), "not_assessed")


def synchronized_figure(dataset: Phase5Dataset, *, selected_arm: str = "guided_decimation"):
    """One legend action toggles an arm in all outcome, attempt, and work panels."""
    if selected_arm not in ARMS or selected_arm == "identity":
        raise ValueError("selected arm must be one of the six interventions")
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    figure = make_subplots(rows=1, cols=3, subplot_titles=("Outcome cells", "Attempts per matched shot", "Typed work per shot"),
                           horizontal_spacing=0.08)
    palette = ("#20324d", "#007a72", "#99613a", "#7159a6", "#b04c68", "#4d83aa", "#937500")
    for index, arm in enumerate(ARMS):
        selected = [row for row in dataset.rows if row.arm == arm]
        source = selected[0]
        visible: bool | str = True if arm in {"identity", selected_arm} else "legendonly"
        counts = Counter(row.outcome for row in selected)
        hover = f"{escape(arm)}<br>{escape(source.variant)}<br>{escape(source.qualification)}<br>{escape(source.assessment_status)}"
        figure.add_trace(go.Bar(
            x=list(OUTCOMES), y=[counts[status] for status in OUTCOMES], name=arm,
            legendgroup=arm, showlegend=True, visible=visible, marker_color=palette[index],
            hovertemplate=hover + "<br>%{x}: %{y} shots<extra></extra>",
        ), row=1, col=1)
        figure.add_trace(go.Scatter(
            x=[row.shot_id for row in selected], y=[row.attempt_count for row in selected],
            mode="lines+markers", name=arm, legendgroup=arm, showlegend=False,
            visible=visible, line_color=palette[index],
            hovertemplate=hover + "<br>shot %{x}: %{y} attempts<extra></extra>",
        ), row=1, col=2)
        figure.add_trace(go.Box(
            x=[field for field in WORK_FIELDS for _row in selected],
            y=[row.work[field] for field in WORK_FIELDS for row in selected],
            name=arm, legendgroup=arm, showlegend=False, visible=visible,
            marker_color=palette[index], boxpoints="all", jitter=0.2,
            hovertemplate=hover + "<br>%{x}: %{y} work units<extra></extra>",
        ), row=1, col=3)
    figure.update_layout(
        title="B1 matched Phase 5 mechanism evidence — pilot_adaptation, not_assessed",
        legend=dict(groupclick="togglegroup"), barmode="group", boxmode="group",
        height=620, width=1450, template="plotly_white", margin=dict(l=65, r=30, t=95, b=140),
    )
    figure.update_xaxes(title_text="Outcome cell", tickangle=-30, row=1, col=1)
    figure.update_yaxes(title_text="Shots", row=1, col=1)
    figure.update_xaxes(title_text="Matched physical shot", row=1, col=2)
    figure.update_yaxes(title_text="Attempts", row=1, col=2)
    figure.update_xaxes(title_text="Typed work category", tickangle=-35, row=1, col=3)
    figure.update_yaxes(title_text="Work units per shot", row=1, col=3)
    return figure
