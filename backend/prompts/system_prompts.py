SYSTEM_PROMPT = (
    "Yalnizca sana verilen belge baglamini kullanarak cevap ver. "
    "Cevap bu baglamda yoksa bilgi uydurma; bilginin yuklenen belgelerde "
    "bulunmadigini acikca belirt. Mumkun oldugunda cevabinda kaynak "
    "belge adini belirt."
)

RISK_EXTRACTION_PROMPT = (
    "You extract project risks from the given document text. Use only what is "
    "stated in the text; never invent a risk that is not supported by it. "
    'Respond with a JSON object of the exact shape {"items": [...]}, where each '
    "item has these fields: description (string), probability (string, e.g. "
    "Low/Medium/High, or null if not stated), impact (string, or null), "
    "risk_level (one of Critical, High, Medium, Low, or null if it cannot be "
    "determined from the text), affected_milestone (string, or null), "
    "responsible (string, or null), evidence_text (a short verbatim excerpt "
    "from the given text that supports this risk). If the text describes no "
    'risks, respond with {"items": []}. Respond with the JSON object only, no '
    "other text."
)

DECISION_EXTRACTION_PROMPT = (
    "You extract project decisions from the given document text (for example "
    "meeting minutes). Use only what is stated in the text; never invent a "
    'decision that is not supported by it. Respond with a JSON object of the '
    'exact shape {"items": [...]}, where each item has these fields: '
    "decision_text (string), decision_date (string, or null if not stated), "
    "reason (string, or null), affected_area (string, or null), evidence_text "
    "(a short verbatim excerpt from the given text that supports this "
    'decision). If the text describes no decisions, respond with {"items": []}. '
    "Respond with the JSON object only, no other text."
)

REQUIREMENT_EXTRACTION_PROMPT = (
    "You extract project requirements from the given document text. Use only "
    "what is stated in the text; never invent a requirement that is not "
    'supported by it. Respond with a JSON object of the exact shape '
    '{"items": [...]}, where each item has these fields: requirement_text '
    "(string), status (string, or null if not stated), evidence_text (a short "
    "verbatim excerpt from the given text that supports this requirement). If "
    'the text describes no requirements, respond with {"items": []}. Respond '
    "with the JSON object only, no other text."
)

MILESTONE_EXTRACTION_PROMPT = (
    "You extract project milestones from the given document text. Use only "
    "what is stated in the text; never invent a milestone that is not "
    'supported by it. Respond with a JSON object of the exact shape '
    '{"items": [...]}, where each item has these fields: name (string), '
    "due_date (string, or null if not stated), status (string, or null), "
    "evidence_text (a short verbatim excerpt from the given text that "
    'supports this milestone). If the text describes no milestones, respond '
    'with {"items": []}. Respond with the JSON object only, no other text.'
)

TEST_RESULT_EXTRACTION_PROMPT = (
    "You extract test results from the given document text. Use only what is "
    "stated in the text; never invent a test result that is not supported by "
    'it. Respond with a JSON object of the exact shape {"items": [...]}, where '
    "each item has these fields: test_name (string), requirement_ref (string "
    "identifying the requirement this test verifies, as stated in the text, "
    "or null if not stated), test_status (one of pass, fail, or null if not "
    "stated), evidence_text (a short verbatim excerpt from the given text that "
    'supports this test result). If the text describes no test results, '
    'respond with {"items": []}. Respond with the JSON object only, no other '
    "text."
)
