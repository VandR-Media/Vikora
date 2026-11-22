# RC9 benchmark scope: 24 additional scenarios, 30 synthetic cases total.
"""RC9: add 24 harder synthetic HR-evidence scenarios (30 total)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
assert (root / "pyproject.toml").is_file(), "Vikora sources missing"


def replace_once(path: str, before: str, after: str) -> None:
    file = root / path
    source = file.read_text(encoding="utf-8-sig")
    assert source.count(before) == 1, (
        f"RC9: expected source anchor not found exactly once: {path}: {before[:80]!r}"
    )
    file.write_text(source.replace(before, after, 1), encoding="utf-8")


NEW_CASES = [
    {
        "id": "rc9-sql-three-years",
        "label": "SQL: практический опыт более трёх лет",
        "criteria": [{"key": "sql", "description": "Подтверждённый практический опыт написания SQL-запросов не менее 3 лет"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. С 2021 по 2025 год работала аналитиком данных: ежедневно писала SQL-запросы для выгрузки, объединения и проверки данных, готовила отчёты для руководителя."}],
        "expected": {"sql": "met"},
    },
    {
        "id": "rc9-sql-one-year-shortfall",
        "label": "SQL: опыт есть, но меньше требуемого срока",
        "criteria": [{"key": "sql", "description": "Коммерческий опыт написания SQL-запросов не менее 3 лет"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. В течение одного года работала с SQL: составляла простые запросы для еженедельных отчётов. Общий коммерческий опыт работы с SQL — 1 год."}],
        "expected": {"sql": "partial"},
    },
    {
        "id": "rc9-sql-team-only",
        "label": "SQL использовала команда, личный опыт не описан",
        "criteria": [{"key": "sql", "description": "Личный практический опыт самостоятельного написания SQL-запросов"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. В отделе коллеги использовали SQL для выгрузок. Кандидат готовила презентации по готовым CSV-файлам. В резюме не описано, чтобы кандидат самостоятельно писала SQL-запросы или работала с SQL напрямую."}],
        "expected": {"sql": "unknown"},
    },
    {
        "id": "rc9-excel-list-only",
        "label": "Excel указан только в списке навыков",
        "criteria": [{"key": "excel", "description": "Практическое знакомство с Microsoft Excel"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Навыки: Microsoft Excel, деловая переписка, работа в команде."}],
        "expected": {"excel": "partial"},
    },
    {
        "id": "rc9-excel-personal-practice",
        "label": "Excel: самостоятельная практика без коммерческих задач",
        "criteria": [{"key": "excel", "description": "Базовое практическое владение Excel, включая формулы и сводные таблицы"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Для личного бюджета самостоятельно создала в Excel таблицу расходов, использовала формулы и сводные таблицы. В рабочих задачах Excel пока не применяла."}],
        "expected": {"excel": "partial"},
    },
    {
        "id": "rc9-excel-work-reports",
        "label": "Excel: подтверждённые рабочие задачи",
        "criteria": [{"key": "excel", "description": "Практический опыт использования Excel для рабочих отчётов, формул и сводных таблиц"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. В течение двух лет ежемесячно готовила в Excel отчёты по продажам, применяла формулы, ВПР и сводные таблицы, проверяла расхождения в данных."}],
        "expected": {"excel": "met"},
    },
    {
        "id": "rc9-google-sheets-not-excel",
        "label": "Google Sheets не подтверждает опыт Excel",
        "criteria": [{"key": "excel", "description": "Подтверждённый практический опыт работы именно в Microsoft Excel"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Для совместных таблиц команды использовала Google Sheets. В резюме нет сведений о работе в Microsoft Excel."}],
        "expected": {"excel": "unknown"},
    },
    {
        "id": "rc9-salesforce-crm-user",
        "label": "Salesforce: ведение клиентской базы",
        "criteria": [{"key": "crm", "description": "Практический опыт работы с CRM-системой для ведения клиентов и сделок"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Ежедневно работала в Salesforce: создавала карточки клиентов, обновляла контакты, фиксировала звонки и отслеживала этапы сделок."}],
        "expected": {"crm": "met"},
    },
    {
        "id": "rc9-salesforce-admin-not-required",
        "label": "CRM: пользовательский опыт без администрирования",
        "criteria": [{"key": "crm", "description": "Практический опыт работы с CRM как пользователь: поиск клиентов, обновление карточек и ведение сделок; администрирование системы не требуется"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Использовала Salesforce для поиска клиентов, обновления карточек и фиксации контактов с заказчиками. Права администратора и настройку CRM не выполняла."}],
        "expected": {"crm": "met"},
    },
    {
        "id": "rc9-crm-list-only",
        "label": "CRM указана в списке навыков без примеров",
        "criteria": [{"key": "crm", "description": "Практическое знакомство с CRM-системами"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Ключевые навыки: CRM, коммуникация с клиентами, деловая переписка."}],
        "expected": {"crm": "partial"},
    },
    {
        "id": "rc9-crm-company-only",
        "label": "CRM использовала компания, личные задачи не описаны",
        "criteria": [{"key": "crm", "description": "Личный практический опыт работы кандидата в CRM-системе"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Компания внедрила CRM для отдела продаж. Кандидат готовила презентации о продуктах и участвовала в общих встречах. В резюме не указано, имела ли кандидат доступ к CRM или выполняла в ней задачи."}],
        "expected": {"crm": "unknown"},
    },
    {
        "id": "rc9-python-course-exercises",
        "label": "Python: учебный курс и упражнения",
        "criteria": [{"key": "python", "description": "Базовое практическое знакомство с Python, включая учебные упражнения"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Завершила онлайн-курс Python, выполнила учебные упражнения по переменным, циклам и обработке списков. Коммерческих задач с Python не выполняла."}],
        "expected": {"python": "partial"},
    },
    {
        "id": "rc9-python-work-automation",
        "label": "Python: автоматизация рабочих отчётов",
        "criteria": [{"key": "python", "description": "Подтверждённый опыт использования Python для автоматизации рабочих задач"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. В рабочей роли написала на Python скрипты для автоматической обработки еженедельных отчётов, очистки CSV-файлов и сверки данных."}],
        "expected": {"python": "met"},
    },
    {
        "id": "rc9-python-personal-portfolio",
        "label": "Python: личный проект и портфолио",
        "criteria": [{"key": "python", "description": "Общее практическое знакомство с Python, включая личные проекты; коммерческий опыт не обязателен"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Самостоятельно изучала Python и создала личный проект для сортировки файлов, разместила учебный код в портфолио. В оплачиваемых рабочих проектах Python не использовала."}],
        "expected": {"python": "partial"},
    },
    {
        "id": "rc9-python-commercial-required",
        "label": "Python: личная практика не заменяет требуемый коммерческий опыт",
        "criteria": [{"key": "python", "description": "Именно коммерческий опыт использования Python в оплачиваемых рабочих проектах"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Самостоятельно изучала Python и создала личный проект для сортировки файлов, разместила учебный код в портфолио. В оплачиваемых рабочих проектах Python не использовала."}],
        "expected": {"python": "not_met"},
    },
    {
        "id": "rc9-sql-contradiction",
        "label": "Противоречивые сведения о SQL",
        "criteria": [{"key": "sql", "description": "Подтверждённый практический опыт использования SQL; при прямом противоречии в резюме не делай уверенный вывод"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Раздел «Навыки»: SQL — продвинутый уровень. Раздел «О себе»: «Я никогда не использовала SQL ни в работе, ни во время обучения». Эти два утверждения противоречат друг другу."}],
        "expected": {"sql": "unknown"},
    },
    {
        "id": "rc9-english-b1-vs-b2",
        "label": "Английский B1 при требовании B2",
        "criteria": [{"key": "english", "description": "Уровень английского языка не ниже B2 по CEFR"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Английский язык — B1 (Intermediate), подтверждённый внутренним тестированием в 2025 году."}],
        "expected": {"english": "partial"},
    },
    {
        "id": "rc9-project-coordination",
        "label": "Координация задач без полного управления проектом",
        "criteria": [{"key": "project_management", "description": "Опыт самостоятельного управления проектом от планирования до завершения, включая ответственность за сроки, объём и бюджет"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Координировала еженедельные статусы команды и напоминала о сроках. План проекта, бюджет и решения об объёме работ оставались ответственностью руководителя проекта."}],
        "expected": {"project_management": "partial"},
    },
    {
        "id": "rc9-people-management",
        "label": "Подтверждённое управление командой",
        "criteria": [{"key": "people_management", "description": "Опыт прямого управления командой сотрудников, распределения задач и контроля результатов"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. С 2022 по 2024 год была непосредственным руководителем команды из шести сотрудников: распределяла задачи, проводила встречи один на один и оценивала результаты работы."}],
        "expected": {"people_management": "met"},
    },
    {
        "id": "rc9-no-direct-reports",
        "label": "Командная работа без прямых подчинённых",
        "criteria": [{"key": "people_management", "description": "Опыт формального линейного управления сотрудниками с прямыми подчинёнными"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Работала в команде из восьми человек, помогала коллегам согласовывать задачи. Прямых подчинённых и формальной ответственности за управление сотрудниками не было."}],
        "expected": {"people_management": "not_met"},
    },
    {
        "id": "rc9-expired-first-aid",
        "label": "Срок действия сертификата истёк",
        "criteria": [{"key": "first_aid", "description": "Наличие действующего на текущую дату сертификата по оказанию первой помощи"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Сертификат по оказанию первой помощи получен в 2021 году. Срок действия сертификата истёк в 2023 году, обновление не проходила."}],
        "expected": {"first_aid": "not_met"},
    },
    {
        "id": "rc9-no-driving-license",
        "label": "Отсутствие водительского удостоверения",
        "criteria": [{"key": "driving_license", "description": "Наличие действующего водительского удостоверения категории B"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Водительского удостоверения нет, автомобиль не водит."}],
        "expected": {"driving_license": "not_met"},
    },
    {
        "id": "rc9-access-not-sql",
        "label": "Microsoft Access не подтверждает опыт SQL",
        "criteria": [{"key": "sql", "description": "Подтверждённый опыт самостоятельного написания SQL-запросов"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Создавала формы и отчёты в Microsoft Access, работала с таблицами базы данных. В резюме нет сведений о самостоятельном написании SQL-запросов."}],
        "expected": {"sql": "unknown"},
    },
    {
        "id": "rc9-java-not-recent",
        "label": "Java использовалась давно, но не в требуемый период",
        "criteria": [{"key": "java", "description": "Практический опыт использования Java в течение последних двух лет"}],
        "pages": [{"page": 1, "text": "Вымышленное резюме. Вымышленный кандидат. Использовала Java в учебных проектах с 2017 по 2019 год. С 2019 года Java не использовала."}],
        "expected": {"java": "not_met"},
    },
]

assert len(NEW_CASES) == 24
assert len({case["id"] for case in NEW_CASES}) == 24

# Append 24 scenarios to the full 22-case RC8 suite; do not alter RC8 behaviour or prompts.
dataset_path = root / "src/app/quality_cases_v14.json"
data = json.loads(dataset_path.read_text(encoding="utf-8"))
assert data.get("version") == "vikora-synthetic-v2"
assert len(data.get("cases", [])) == 22, "RC9 expected the complete 22-case RC8 baseline"
existing_ids = {case.get("id") for case in data["cases"]}
assert not existing_ids.intersection(case["id"] for case in NEW_CASES)
data["cases"].extend(NEW_CASES)
data["version"] = "vikora-synthetic-v3"
assert len(data["cases"]) == 46
dataset_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

qa = "src/app/services/quality_audit.py"
replace_once(qa, 'DATASET_VERSION = "vikora-synthetic-v2"',
                'DATASET_VERSION = "vikora-synthetic-v3"')

# RC9 is a separate experimental installer identity; RC8 remains reproducible.
for rel in ("pyproject.toml", "src/app/main.py", "packaging/Vikora.iss",
            "VERSION.txt", "packaging/verify_release_sources.py",
            "tests/test_windows_rc3.py"):
    file = root / rel
    text = file.read_text(encoding="utf-8-sig")
    updated = (text.replace("1.4.0rc8", "1.4.0rc9")
                   .replace("1.4.0-rc8", "1.4.0-rc9")
                   .replace("1.4.0 RC8", "1.4.0 RC9"))
    file.write_text(updated, encoding="utf-8")

js_file = root / "src/app/web/assets/app.js"
js = js_file.read_text(encoding="utf-8")
js_file.write_text(js.replace("Vikora v1.4 RC8", "Vikora v1.4 RC9"), encoding="utf-8")

(root / "tests/test_ollama_rc9_benchmark.py").write_text('''"""RC9 expanded synthetic benchmark contract; no real CVs or candidate data."""
from collections import Counter

from app.services import quality_audit

EXPECTED_NEW_IDS = {
    "rc9-sql-three-years", "rc9-sql-one-year-shortfall", "rc9-sql-team-only",
    "rc9-excel-list-only", "rc9-excel-personal-practice", "rc9-excel-work-reports",
    "rc9-google-sheets-not-excel", "rc9-salesforce-crm-user",
    "rc9-salesforce-admin-not-required", "rc9-crm-list-only", "rc9-crm-company-only",
    "rc9-python-course-exercises", "rc9-python-work-automation",
    "rc9-python-personal-portfolio", "rc9-python-commercial-required",
    "rc9-sql-contradiction", "rc9-english-b1-vs-b2", "rc9-project-coordination",
    "rc9-people-management", "rc9-no-direct-reports", "rc9-expired-first-aid",
    "rc9-no-driving-license", "rc9-access-not-sql", "rc9-java-not-recent",
}


def test_rc9_benchmark_has_46_cases_and_24_new_scenarios():
    cases = quality_audit.read_synthetic_cases()
    assert quality_audit.DATASET_VERSION == "vikora-synthetic-v3"
    assert len(cases) == 46
    ids = [case["id"] for case in cases]
    assert len(set(ids)) == 46
    assert EXPECTED_NEW_IDS.issubset(set(ids))


def test_rc9_cases_have_one_unambiguous_expected_criterion():
    cases = quality_audit.read_synthetic_cases()
    new_cases = [case for case in cases if case["id"] in EXPECTED_NEW_IDS]
    assert len(new_cases) == 24
    for case in new_cases:
        assert len(case["criteria"]) == 1
        key = case["criteria"][0]["key"]
        assert set(case["expected"]) == {key}
        assert case["expected"][key] in {"met", "partial", "not_met", "unknown"}
        assert case["pages"]
        assert all("Вымышленное резюме" in page["text"] for page in case["pages"])


def test_rc9_expected_labels_cover_all_four_assessment_outcomes():
    cases = quality_audit.read_synthetic_cases()
    labels = {
        level
        for case in cases
        for level in case["expected"].values()
    }
    assert labels == {"met", "partial", "not_met", "unknown"}


def test_rc9_benchmark_contains_distinct_context_and_evidence_traps():
    ids = {case["id"] for case in quality_audit.read_synthetic_cases()}
    assert {
        "rc9-sql-team-only",
        "rc9-google-sheets-not-excel",
        "rc9-crm-company-only",
        "rc9-python-commercial-required",
        "rc9-sql-contradiction",
        "rc9-no-direct-reports",
        "rc9-expired-first-aid",
        "rc9-access-not-sql",
        "rc9-java-not-recent",
    }.issubset(ids)
''', encoding="utf-8")

(root / "docs/RC9_BENCHMARK_DESIGN.md").write_text(
    "# Vikora 1.4 RC9 — расширенный синтетический HR-бенчмарк\n\n"
    "RC9 не меняет правила анализа Qwen3 из RC8. Изменяется только набор контрольных примеров: "
    "22 исходных сценария RC8 плюс 24 новых, всего 46. Все резюме полностью вымышленные.\n\n"
    "Новые группы проверок:\n"
    "- Срок и глубина опыта: SQL 4 года против требования 3 лет; SQL 1 год против требования 3 лет.\n"
    "- Контекст использования: навык команды против личного опыта; инструмент работодателя против личных задач.\n"
    "- Уровень доказательств: навык в списке; учебный курс; личный проект; рабочие задачи.\n"
    "- Переносимость навыков: Google Sheets не считается автоматическим доказательством Microsoft Excel; "
    "Microsoft Access не считается автоматическим доказательством SQL.\n"
    "- Границы требования: пользователь CRM против администратора; личный Python-проект против коммерческого опыта.\n"
    "- Противоречия и пороговые условия: противоречивые сведения о SQL; английский B1 при требовании B2; "
    "управление проектом против координации; управление людьми против командного взаимодействия.\n"
    "- Срок действия и актуальность: истёкший сертификат; отсутствие водительского удостоверения; "
    "Java, не использовавшаяся после 2019 года.\n\n"
    "Ожидаемые метки заданы до запуска модели. Они являются гипотезами тестового набора, а не доказанными "
    "оценками реальных кандидатов. Результаты RC9 следует анализировать по каждому сценарию и по типу ошибки, "
    "а не только по общему проценту совпадений.\n",
    encoding="utf-8",
)

(root / "docs/RELEASE_NOTES_RC9.md").write_text(
    "# Vikora 1.4 RC9 — расширенная проверка локального ИИ\n\n"
    "Добавлены 24 сложных синтетических сценария к полному исходному набору из 22 сценариев RC8: всего 46. "
    "Проверяются длительность опыта, личное и командное использование инструментов, учебные и личные проекты, "
    "различие похожих программ, пользовательский опыт CRM, пороговые требования, противоречия, "
    "управление проектами и людьми, срок действия сертификатов и актуальность навыков. "
    "Промпт и алгоритм строгой проверки цитат RC8 не меняются. Реальные резюме не используются.\n",
    encoding="utf-8",
)

print("Vikora RC9 expanded synthetic benchmark applied: 46 cases total")
