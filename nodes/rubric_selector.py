from __future__ import annotations

from core.rubrics import infer_candidate_track, select_scoring_rubric
from core.schemas import CandidateProfile, JobProfile
from core.state import WorkflowState
from harness.trace import add_trace


def rubric_selector_node(state: WorkflowState) -> WorkflowState:
    candidate = CandidateProfile.model_validate(state.get("candidate_profile"))
    job = JobProfile.model_validate(state.get("job_profile"))

    track, confidence, reason = infer_candidate_track(candidate, job)
    scoring_rubric = select_scoring_rubric(track)

    updated_candidate = candidate.model_copy(
        update={
            "candidate_track": track,
            "track_confidence": confidence,
            "track_reason": reason,
        }
    )

    return {
        "candidate_profile": updated_candidate.model_dump(),
        "scoring_rubric": scoring_rubric.model_dump(),
        "current_step": "rubric_selector",
        "trace": add_trace(
            state,
            "rubric_selector",
            f"Selected {track} scoring rubric.",
            {"track": track, "confidence": confidence, "reason": reason},
        ),
    }
