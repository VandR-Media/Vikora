"""RC7: focused Ollama diagnostics + JSON-schema constrained replies.
Applied to the already-tested RC6 release tree, without touching user data.
"""
from __future__ import annotations
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
assert (root / "pyproject.toml").is_file(), "Vikora sources missing"

def replace_once(path: str, before: str, after: str) -> None:
    f = root / path
    source = f.read_text(encoding="utf-8-sig")
    assert source.count(before) == 1, f"RC7: expected source anchor not found exactly once: {path}: {before[:65]!r}"
    f.write_text(source.replace(before, after, 1), encoding="utf-8")

local = "src/app/services/local_ai.py"
replace_once(local, "from app.services.evaluate import (EvaluationFailure, SYSTEM_PROMPT,",
                   "from app.services.evaluate import (EvaluationFailure, ModelAssessment, SYSTEM_PROMPT,")
replace_once(local, "MAX_CHUNKS = 5\n", """MAX_CHUNKS = 5


class LocalAIError(EvaluationFailure):
    # A fixed, non-sensitive category: never save model output, CV excerpts or HTTP bodies.
    def __init__(self, code: str):
        super().__init__("Локальная оценка не завершена")
        self.diagnostic_code = code


""")
replace_once(local, '"model": MODEL_TAG, "stream": False, "format": "json", "think": False,',
                   '"model": MODEL_TAG, "stream": False, "format": ModelAssessment.model_json_schema(), "think": False,')
old = """        try:
            with httpx.Client(timeout=300.0, trust_env=False) as client:
                response = client.post(f"{OLLAMA_ORIGIN}/api/chat", json=payload)
                response.raise_for_status()
                content = response.json()["message"]["content"]
            if not isinstance(content, str) or len(content) > 100000:
                raise ValueError("Invalid Ollama content")
            result = json.loads(content)
            results.append(validate_grounding(result, criteria, pages))
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise EvaluationFailure("Локальная модель недоступна или вернула некорректный результат. Проверьте Ollama и попробуйте снова.") from exc"""
new = """        try:
            with httpx.Client(timeout=300.0, trust_env=False) as client:
                response = client.post(f"{OLLAMA_ORIGIN}/api/chat", json=payload)
                response.raise_for_status()
                envelope = response.json()
        except httpx.TimeoutException as exc:
            raise LocalAIError("timeout") from exc
        except httpx.HTTPStatusError as exc:
            raise LocalAIError("http_error") from exc
        except httpx.HTTPError as exc:
            raise LocalAIError("connection_error") from exc
        except (ValueError, TypeError) as exc:
            raise LocalAIError("invalid_envelope") from exc
        try:
            content = envelope["message"]["content"]
        except (KeyError, TypeError, IndexError) as exc:
            raise LocalAIError("invalid_envelope") from exc
        if not isinstance(content, str) or not content.strip() or len(content) > 100000:
            raise LocalAIError("empty_or_oversized_answer")
        try:
            result = json.loads(content)
        except ValueError as exc:
            raise LocalAIError("invalid_json") from exc
        if not isinstance(result, dict):
            raise LocalAIError("invalid_structure")
        try:
            normalized = validate_grounding(result, criteria, pages)
        except EvaluationFailure as exc:
            failure_codes = {
                "Model returned invalid assessment structure": "invalid_structure",
                "Model returned missing, duplicate or unknown criterion keys": "criterion_keys",
                "Unknown result must not contain evidence": "unknown_with_quote",
                "Known result must cite evidence": "missing_quote",
                "Model cited an excerpt not found on the stated page": "quote_not_found",
            }
            raise LocalAIError(failure_codes.get(str(exc), "validation_error")) from exc
        results.append(normalized)"""
replace_once(local, old, new)

quality = "src/app/services/quality_audit.py"
replace_once(quality, """        except EvaluationFailure:
            row.update(status='failed', predicted={}, correctly_matched=False,
                       error="ИИ не дал проверяемую оценку или точную цитату")""",
"""        except EvaluationFailure as exc:
            # Diagnostic labels are fixed strings, never HTTP bodies or model-generated prose.
            labels = {
                "timeout": "Превышено время ожидания ответа Ollama",
                "http_error": "Ollama отклонила запрос",
                "connection_error": "Нет подключения к Ollama во время оценки",
                "invalid_envelope": "Некорректный служебный ответ Ollama",
                "empty_or_oversized_answer": "Ollama вернула пустой или слишком большой ответ",
                "invalid_json": "Модель вернула ответ не в формате JSON",
                "invalid_structure": "Структура ответа модели не соответствует требованиям",
                "criterion_keys": "Модель перепутала или пропустила критерии",
                "unknown_with_quote": "Для неопределённого навыка модель добавила цитату",
                "missing_quote": "Модель не предоставила обязательную цитату",
                "quote_not_found": "Цитата модели не найдена в тестовом резюме",
                "validation_error": "Ответ модели не прошёл проверку",
            }
            code = getattr(exc, "diagnostic_code", None)
            row.update(status='failed', predicted={}, correctly_matched=False,
                       error=labels.get(code, "ИИ не дал проверяемую оценку или точную цитату"))
            if code in labels:
                row["error_code"] = code""")

# RC7 is a new installer so the installed RC6 remains recoverable.
for rel in ("pyproject.toml", "src/app/main.py", "packaging/Vikora.iss",
            "VERSION.txt", "packaging/verify_release_sources.py",
            "tests/test_windows_rc3.py"):
    file = root / rel
    text = file.read_text(encoding="utf-8-sig")
    text = (text.replace("1.4.0rc6", "1.4.0rc7")
                .replace("1.4.0-rc6", "1.4.0-rc7")
                .replace("1.4.0 RC6", "1.4.0 RC7"))
    file.write_text(text, encoding="utf-8")

js_file = root / "src/app/web/assets/app.js"
js = js_file.read_text(encoding="utf-8")
js_file.write_text(js.replace("Vikora v1.4 RC6", "Vikora v1.4 RC7"), encoding="utf-8")

(root / "tests/test_ollama_rc7.py").write_text('''"""RC7: verify typed safe Ollama errors and continued strict citation checks."""
import json
import httpx
import pytest

from app.services import local_ai, quality_audit

CRITERIA = [{"key": "python", "label": "Python"}]
PAGES = [{"page": 1, "text": "Вымышленное резюме. Выполнял рабочие задачи на Python в течение 3 лет."}]


def response(level="met", excerpt="Выполнял рабочие задачи на Python"):
    return {"message": {"content": json.dumps({"results": [{
        "criterion_key": "python",
        "match_level": level,
        "evidence": [] if level == "unknown" else [{"page": 1, "excerpt": excerpt}],
        "rationale": "Подтверждается указанным опытом работы",
    }]}, ensure_ascii=False)}}


def fake_client(monkeypatch, answer=None, error=None):
    captured = {}
    class FakeResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return answer
    class FakeClient:
        def __init__(self, **kwargs):
            captured["client_options"] = kwargs
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, url, json):
            captured["url"] = url
            captured["payload"] = json
            if error is not None:
                raise error
            return FakeResponse()
    monkeypatch.setattr(local_ai.httpx, "Client", FakeClient)
    return captured


def test_valid_evidence_and_json_schema(monkeypatch):
    call = fake_client(monkeypatch, response())
    raw = local_ai.ollama_assess(CRITERIA, PAGES)
    assert raw["results"][0]["match_level"] == "met"
    assert call["payload"]["format"]["type"] == "object"
    assert call["payload"]["think"] is False
    assert call["client_options"]["trust_env"] is False
    assert call["url"] == "http://127.0.0.1:11434/api/chat"


@pytest.mark.parametrize("answer,code", [
    ({"message": {"content": "not-json"}}, "invalid_json"),
    ({"message": {"content": ""}}, "empty_or_oversized_answer"),
    ({"message": {"content": "{}"}}, "invalid_structure"),
    (response(excerpt="Фраза которой нет в документе"), "quote_not_found"),
    (response(level="met", excerpt=""), "invalid_structure"),
])
def test_errors_have_safe_categories(monkeypatch, answer, code):
    fake_client(monkeypatch, answer)
    with pytest.raises(local_ai.LocalAIError) as found:
        local_ai.ollama_assess(CRITERIA, PAGES)
    assert found.value.diagnostic_code == code


def test_timeout_is_identified_without_leaking_response(monkeypatch):
    fake_client(monkeypatch, error=httpx.ConnectTimeout("do not disclose sensitive network context"))
    with pytest.raises(local_ai.LocalAIError) as found:
        local_ai.ollama_assess(CRITERIA, PAGES)
    assert found.value.diagnostic_code == "timeout"


def test_quality_report_only_contains_safe_error_code():
    def fake_error(*args):
        raise local_ai.LocalAIError("quote_not_found")
    case = quality_audit.read_synthetic_cases()[0]
    report = quality_audit.evaluate_cases("ollama_local", [case], assess=fake_error)
    row = report["results"][0]
    assert row["error_code"] == "quote_not_found"
    assert row["status"] == "failed"
    assert "Вымышленное резюме" not in json.dumps(report, ensure_ascii=False)
    assert "quote_not_found" in json.dumps(report)
''', encoding="utf-8")

(root / "docs/RELEASE_NOTES_RC7.md").write_text(
    "# Vikora 1.4 RC7 — диагностика локальной Qwen3\\n\\n"
    "Добавлен JSON Schema для ответов Ollama и безопасные коды ошибок локального анализа. "
    "Исходные ответы модели, резюме и ключи в отчёты не включаются. "
    "Проверка точности цитат и запрет автоматических HR-решений сохранены. "
    "RC7 требует испытания на ноутбуке перед использованием реальных данных.\\n",
    encoding="utf-8",
)
print("Vikora RC7 local AI diagnostics applied")
