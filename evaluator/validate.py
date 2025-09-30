# evaluator/validate.py
def validate_evaluation_result(obj):
    # minimal checks; raise ValueError if invalid
    if not isinstance(obj, dict):
        raise ValueError("result not a dict")

    # required top-level keys
    keys = ["cv_match_rate", "cv_feedback", "project_scores", "project_score", "project_feedback", "overall_summary"]
    for k in keys:
        if k not in obj:
            raise ValueError(f"missing key: {k}")

    # cv_match_rate 0-1
    cm = obj["cv_match_rate"]
    if not (isinstance(cm, (int, float)) and 0.0 <= float(cm) <= 1.0):
        raise ValueError("cv_match_rate invalid")

    ps = obj["project_scores"]
    if not isinstance(ps, dict):
        raise ValueError("project_scores must be dict")
    for p in ["correctness","code_quality","resilience","documentation","creativity"]:
        if p not in ps or not (isinstance(ps[p], int) and 1 <= ps[p] <= 5):
            raise ValueError(f"project_scores.{p} invalid")

    # project_score 0-10
    if not (isinstance(obj["project_score"], (int, float)) and 0.0 <= float(obj["project_score"]) <= 10.0):
        raise ValueError("project_score invalid")

    return True
