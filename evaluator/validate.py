# evaluator/validate.py
def _validate_float(value, min_val, max_val, field_name):
    if not isinstance(value, (int, float)):
        raise ValueError(f'{field_name} must be a number')
    if not (min_val <= float(value) <= max_val):
        raise ValueError(f'{field_name} must be between {min_val} and {max_val}')


def _validate_int(value, min_val, max_val, field_name):
    if not isinstance(value, int):
        raise ValueError(f'{field_name} must be an integer')
    if not (min_val <= value <= max_val):
        raise ValueError(f'{field_name} must be between {min_val} and {max_val}')


def validate_evaluation_result(obj: dict) -> bool:
    """
    Validate the evaluation result JSON structure from the LLM.
    Raises ValueError if validation fails, returns True otherwise.
    """

    if not isinstance(obj, dict):
        raise ValueError('Result must be a dict')

    # Required top-level keys
    required_keys = [
        'cv_match_rate',
        'cv_feedback',
        'project_scores',
        'project_score',
        'project_feedback',
        'overall_summary',
    ]
    for k in required_keys:
        if k not in obj:
            raise ValueError(f'Missing key: {k}')

    # Validate cv_match_rate (0–1 float)
    _validate_float(obj['cv_match_rate'], 0.0, 1.0, 'cv_match_rate')

    # Validate project_scores
    ps = obj['project_scores']
    if not isinstance(ps, dict):
        raise ValueError('project_scores must be a dict')

    score_fields = ['correctness', 'code_quality', 'resilience', 'documentation', 'creativity']
    for field in score_fields:
        if field not in ps:
            raise ValueError(f'Missing project_scores.{field}')
        _validate_int(ps[field], 1, 5, f'project_scores.{field}')

    # Validate project_score (0–10 float)
    _validate_float(obj['project_score'], 0.0, 10.0, 'project_score')

    return True
