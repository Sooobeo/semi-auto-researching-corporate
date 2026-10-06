"""Retain the frozen 1.0 validator and add the practice-discovered response constraint."""
from p04_annotation_validation import validate_annotation
from p04_annotation_validation import validate_assessment as original_validate_assessment

def validate_assessment(row, annotations, contract):
    errors=original_validate_assessment(row,annotations,contract)
    if row.get('guide_version') != contract['guide_version']:
        errors.append('wrong_assessment_guide_version')
    for q in row.get('questions',[]):
        if q.get('response') not in contract['assessment_response_enums'].get(q.get('question_id'),[]):
            errors.append('invalid_assessment_response:'+str(q.get('question_id')))
    return errors
