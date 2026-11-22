"""RC8: tune Qwen evidence extraction and synthetic evaluation semantics."""
from __future__ import annotations
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
assert (root / "pyproject.toml").is_file(), "Vikora sources missing"

def replace_once(path: str, before: str, after: str) -> None:
    f = root / path
    source = f.read_text(encoding="utf-8-sig")
    assert source.count(before) == 1, f"RC8: expected source anchor not found exactly once: {path}: {before[:75]!r}"
    f.write_text(source.replace(before, after, 1), encoding="utf-8")

local = "src/app/services/local_ai.py"
replace_once(local, """MAX_CHUNKS = 5


class LocalAIError""", """MAX_CHUNKS = 5

LOCAL_SYSTEM_PROMPT = SYSTEM_PROMPT + r''' 
ADDITIONAL LOCAL QWEN RULES — FOLLOW THESE EXACTLY:
1. EVIDENCE MUST BE A VERBATIM, CONTIGUOUS SUBSTRING copied from the supplied resume_pages[].text.
   Preserve the original spelling, punctuation, capitalization and wording. Do not paraphrase,
   translate, summarize, correct, add ellipses, or combine separated fragments. Prefer the shortest
   exact phrase that supports the assessment. If you cannot copy an exact substring, use
   match_level="unknown" and evidence=[].
2. For match_level="unknown", evidence MUST be [] (an empty array).
3. A skill explicitly named only in a skills list, with no tasks or proficiency details, is
   "partial", not "met" and not "unknown": the skill is mentioned but competence is unproven.
   Cite the exact skill name from the list.
4. Explicit self-study plus described learning exercises or personal practice, but no commercial
   projects, is "partial" when the criterion asks for general familiarity/experience. Lack of
   commercial employment alone does not erase demonstrated personal practice.
5. Use "not_met" only for an explicit negative statement about the skill/experience required.
   If the criterion specifically requires commercial/professional experience and the resume says
   that experience is absent, "not_met" may be appropriate. Do not confuse "no commercial projects"
   with "never used the skill".
6. Use "unknown" when the resume contains no relevant mention or the evidence is genuinely
   ambiguous. Never invent a quote to justify an unknown result.
'''


def _discard_unknown_evidence(raw: dict) -> dict:
    """Drop irrelevant model quotes on UNKNOWN; this can never create a positive claim."""
    items = raw.get("results")
    if isinstance(items, list):
        for item in items:
            if (isinstance(item, dict) and item.get("match_level") == "unknown"
                    and isinstance(item.get("evidence"), list)):
                item["evidence"] = []
    return raw


class LocalAIError""")
replace_once(local, '{"role": "system", "content": SYSTEM_PROMPT},',
                   '{"role": "system", "content": LOCAL_SYSTEM_PROMPT},')
replace_once(local, "normalized = validate_grounding(result, criteria, pages)",
                   "result = _discard_unknown_evidence(result)\n            normalized = validate_grounding(result, criteria, pages)")

# The old v1 case contradicted its own label: it said there was no practical experience,
# while expecting partial for a criterion explicitly asking for programming experience.
# v2 makes the intended partial case unambiguous: self-study plus personal scripts, no commercial work.
qa = "src/app/services/quality_audit.py"
replace_once(qa, 'DATASET_VERSION = "vikora-synthetic-v1"',
                'DATASET_VERSION = "vikora-synthetic-v2"')
dataset_path = root / "src/app/quality_cases_v14.json"
data = json.loads(dataset_path.read_text(encoding="utf-8"))
assert data.get("version") == "vikora-synthetic-v1"
data["version"] = "vikora-synthetic-v2"
case = next((x for x in data["cases"] if x.get("id") == "negation-trap"), None)
assert case is not None
case["label"] = "Самостоятельное обучение Python с учебными скриптами"
case["criteria"][0]["description"] = "Базовое знакомство с Python, включая самостоятельное обучение"
case["pages"][0]["text"] = (
    "Вымышленное резюме. Вымышленный кандидат. Python изучала самостоятельно по видео, "
    "написала несколько учебных скриптов, коммерческих проектов пока нет."
)
assert case["expected"]["python"] == "partial"
dataset_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# RC8 has its own install identity; do not overwrite the already installed RC7 build.
for rel in ("pyproject.toml", "src/app/main.py", "packaging/Vikora.iss",
            "VERSION.txt", "packaging/verify_release_sources.py",
            "tests/test_windows_rc3.py"):
    file = root / rel
    text = file.read_text(encoding="utf-8-sig")
    updated = (text.replace("1.4.0rc7", "1.4.0rc8")
                   .replace("1.4.0-rc7", "1.4.0-rc8")
                   .replace("1.4.0 RC7", "1.4.0 RC8"))
    file.write_text(updated, encoding="utf-8")

js_file = root / "src/app/web/assets/app.js"
js = js_file.read_text(encoding="utf-8")
assert "Vikora v1.4 RC7" in js
js_file.write_text(js.replace("Vikora v1.4 RC7", "Vikora v1.4 RC8"), encoding="utf-8")

(root / "tests/test_ollama_rc8.py").write_text(r'''"""RC8: Qwen quote precision and safe UNKNOWN normalization."""
import json
import httpx
import pytest

from app.services import local_ai, quality_audit

CRITERIA = [{"key": "python", "label": "Python"}]
PAGES = [{"page": 1, "text": "Вымышленное резюме. Выполнял рабочие задачи на Python в течение 3 лет."}]


def make_answer(level="unknown", evidence=None):
    if evidence is None:
        evidence = [{"page": 1, "excerpt": "Python"}] if level != "unknown" else []
    return {"message": {"content": json.dumps({"results": [{
        "criterion_key": "python", "match_level": level, "evidence": evidence,
        "rationale": "Проверка синтетического примера",
    }]}, ensure_ascii=False)}}


def fake_client(monkeypatch, answer):
    captured = {}
    class FakeResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return answer
    class FakeClient:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, url, json):
            captured["payload"] = json
            assert url == "http://127.0.0.1:11434/api/chat"
            return FakeResponse()
    monkeypatch.setattr(local_ai.httpx, "Client", FakeClient)
    return captured


def test_unknown_with_irrelevant_quote_is_safely_dropped(monkeypatch):
    fake_client(monkeypatch, make_answer("unknown", [{"page": 1, "excerpt": "Python"}]))
    result = local_ai.ollama_assess(CRITERIA, PAGES)
    assert result["results"][0]["match_level"] == "unknown"
    assert result["results"][0]["evidence"] == []


def test_unknown_with_malformed_evidence_is_not_silently_repaired(monkeypatch):
    fake_client(monkeypatch, make_answer("unknown", "Python"))
    with pytest.raises(local_ai.LocalAIError) as found:
        local_ai.ollama_assess(CRITERIA, PAGES)
    assert found.value.diagnostic_code == "invalid_structure"


def test_local_prompt_demands_exact_quotes_and_conservative_partial_labels(monkeypatch):
    call = fake_client(monkeypatch, make_answer("partial", [{"page": 1, "excerpt": "Python"}]))
    local_ai.ollama_assess(CRITERIA, PAGES)
    prompt = call["payload"]["messages"][0]["content"].lower()
    assert "verbatim, contiguous substring" in prompt
    assert "skills list" in prompt
    assert "self-study" in prompt
    assert "never used the skill" in prompt


def test_invented_quote_for_positive_claim_still_fails_closed(monkeypatch):
    fake_client(monkeypatch, make_answer("met", [{"page": 1, "excerpt": "Я эксперт Python"}]))
    with pytest.raises(local_ai.LocalAIError) as found:
        local_ai.ollama_assess(CRITERIA, PAGES)
    assert found.value.diagnostic_code == "quote_not_found"


def test_synthetic_dataset_v2_has_unambiguous_self_study_case():
    assert quality_audit.DATASET_VERSION == "vikora-synthetic-v2"
    case = next(x for x in quality_audit.read_synthetic_cases() if x["id"] == "negation-trap")
    assert "учебных скриптов" in case["pages"][0]["text"]
    assert "Базовое знакомство" in case["criteria"][0]["description"]
    assert case["expected"]["python"] == "partial"
''', encoding="utf-8")

(root / "docs/RELEASE_NOTES_RC8.md").write_text(
    "# Vikora 1.4 RC8 — точные цитаты и контекст Qwen3\n\n"
    "Усилены инструкции локальной Qwen3: цитаты должны быть точными непрерывными фрагментами исходного текста. "
    "Для результата unknown безопасно отбрасываются необязательные цитаты; положительные и частичные оценки "
    "по-прежнему требуют строгой проверки цитат. Уточнено различие между упоминанием навыка, личной практикой "
    "и коммерческим опытом. Набор синтетических тестов обновлён до v2; реальные резюме не используются. "
    "Автоматические решения о найме не принимаются.\n",
    encoding="utf-8",
)
print("Vikora RC8 Qwen evidence tuning applied")
