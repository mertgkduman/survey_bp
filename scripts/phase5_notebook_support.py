"""Escaped, shot-first notebook tables over immutable Phase 5 analysis rows."""

from __future__ import annotations

from html import escape
import json

from bp_registry.phase5_analysis import ARMS, Phase5Dataset


def shot_table_html(dataset: Phase5Dataset, *, shot_id: int, selected_arm: str) -> str:
    if selected_arm not in ARMS or selected_arm == "identity":
        raise ValueError("select one intervention arm")
    matched = dataset.shot(shot_id)
    if len(matched) != len(ARMS) or len({row.sample_identity for row in matched}) != 1:
        raise ValueError("shot-first view requires seven matched arm rows")
    highlighted = {"identity", selected_arm}
    headings = ("Arm", "Status", "Outcome cell", "Selected candidate", "Selected origin", "Original valid", "Attempts", "C2V work", "Qualification", "Source revision", "Variant")
    body = []
    for row in matched:
        style = ' class="selected"' if row.arm in highlighted else ""
        values = (
            row.arm, row.termination, row.outcome, json.dumps(row.selected_origin),
            "yes" if row.original_valid is True else "unavailable" if row.original_valid is None else "no",
            str(row.attempt_count), str(row.work["check_to_variable_updates"]), row.qualification,
            row.source_revision, row.variant,
        )
        candidate = row.selected_candidate
        candidate_cell = (
            "unavailable" if candidate is None else
            f"<details><summary>{sum(candidate)} ones · {len(candidate)} bits</summary><code>"
            + "".join(str(bit) for bit in candidate) + "</code></details>"
        )
        cells = [f"<td>{escape(value)}</td>" for value in values]
        cells.insert(3, f"<td>{candidate_cell}</td>")
        body.append("<tr" + style + ">" + "".join(cells) + "</tr>")
    return (
        '<div class="phase5-shot"><h3>Matched physical shot ' + str(shot_id) + "</h3>"
        + '<p>Sample identity: <code>' + escape(matched[0].sample_identity) + '</code>. '
        + 'Assessment: <strong>not_assessed</strong>; relation: <strong>pilot_adaptation</strong>.</p>'
        + '<table><thead><tr>' + "".join(f"<th>{escape(label)}</th>" for label in headings)
        + '</tr></thead><tbody>' + "".join(body) + '</tbody></table></div>'
    )


def attempt_details_html(dataset: Phase5Dataset, *, shot_id: int) -> str:
    matched = dataset.shot(shot_id)
    if len(matched) != len(ARMS):
        raise ValueError("attempt drilldown requires a complete matched shot")
    sections = ['<section class="phase5-attempts"><h3>Every recorded attempt</h3>']
    for arm in ARMS:
        row = next(item for item in matched if item.arm == arm)
        attempts = dataset.attempts_for(shot_id, arm)
        sections.append("<h4>" + escape(arm) + " — " + str(len(attempts)) + " attempts</h4>")
        if not attempts:
            sections.append('<p class="attempt-empty">No intervention attempt was proposed; terminal: '
                            + escape(row.termination) + ".</p>")
            continue
        for attempt in attempts:
            payload = attempt.payload
            target = payload.get("target_index", payload.get("selected_target", payload.get("test_vector", "unavailable")))
            summary = f"{arm} attempt {attempt.order}: {attempt.termination}; target {target}"
            sections.append(
                "<details><summary>" + escape(summary) + "</summary>"
                + "<p>Qualification: " + escape(attempt.qualification) + "</p>"
                + "<pre>" + escape(json.dumps(payload, sort_keys=True, indent=2)) + "</pre></details>"
            )
    sections.append("</section>")
    return "".join(sections)
