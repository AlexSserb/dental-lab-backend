"""Step 1 of the triage workflow: turn the doctor's report into a structured classification."""
from llm.service import call_structured

from defects.triage.prompt_provider import CLASSIFY, get_prompt
from defects.triage.prompts import build_classify_message
from defects.triage.schemas import DefectClassification

FEATURE = "defect_classify"


def classify_defect(work_names: list[str], comment: str, user=None) -> DefectClassification:
    """
    Classify a reported defect. The comment is untrusted user text: build_classify_message strips the angle
    brackets and bounds its length, and the <report> tag in the prompt tells the model never to follow
    instructions found inside it. The output is limited by the schema's enums, so nothing outside
    DefectType/DefectSeverity/confidence levels can come back. `user` goes into the LLM call log.
    """
    return call_structured(
        feature=FEATURE,
        system=get_prompt(CLASSIFY).text,
        user_text=build_classify_message(work_names, comment),
        schema=DefectClassification,
        user=user,
    )
