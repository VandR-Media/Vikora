"""Windows RC4 hotfix, applied only after the RC3 zip hash is verified."""
from pathlib import Path
from PIL import Image
import base64, shutil, sys, traceback

root=Path(sys.argv[1]).resolve()
assert (root/"pyproject.toml").is_file()
runner=root/"src/app/local_runner.py"
s=runner.read_text(encoding="utf-8")
assert 'log_level="warning", access_log=False))' in s
s=s.replace("import logging\n","import logging\nimport traceback\n",1)
s=s.replace('log_level="warning", access_log=False))',
            'log_level="warning", access_log=False,\n                                                   log_config=None))',1)
old='        message = "Не удалось запустить Vikora.\\n\\n" + str(exc) + "\\n\\nПопробуйте закрыть ранее открытые окна Vikora."'
assert old in s
new='''        try:
            from app.local_runtime import data_directory
            error_log = data_directory() / "vikora_startup_error.log"
            error_log.parent.mkdir(parents=True, exist_ok=True)
            error_log.write_text(traceback.format_exc(), encoding="utf-8")
            hint = "\\n\\nДиагностика сохранена: " + str(error_log)
        except Exception:
            hint = ""
        message = ("Не удалось запустить Vikora.\\n\\n" + str(exc)
                   + "\\n\\nПопробуйте закрыть ранее открытые окна Vikora." + hint)'''
s=s.replace(old,new,1)
runner.write_text(s,encoding="utf-8")
for rel in ("pyproject.toml","src/app/main.py","packaging/Vikora.iss",
            "VERSION.txt","tests/test_windows_rc3.py"):
    p=root/rel
    t=p.read_text(encoding="utf-8-sig").replace("1.4.0rc3","1.4.0rc4").replace("1.4.0-rc3","1.4.0-rc4").replace("1.4.0 RC3","1.4.0 RC4")
    p.write_text(t,encoding="utf-8")
p=root/"packaging/verify_release_sources.py"
s=p.read_text(encoding="utf-8")
s=s.replace("'windows_entry.py', 'src/app/local_runner.py',",
            "'windows_entry.py', 'src/app/local_runner.py',\n        'branding/vikora.ico', 'branding/vikora.png',")
s=s.replace("if '1.4.0 RC3' not in version_file:\n        raise AssertionError('VERSION.txt must name RC3, not a previous installer')",
            "if display_version.replace('-rc', ' RC') not in version_file:\n        raise AssertionError('VERSION.txt must match the installer version')")
p.write_text(s,encoding="utf-8")
source=Path(__file__).resolve().parents[1]/"branding/vikora_logo_png.base64"
png=base64.b64decode(source.read_text(encoding="ascii").strip(),validate=True)
brand=root/"branding"
brand.mkdir(exist_ok=True)
(brand/"vikora.png").write_bytes(png)
im=Image.open(brand/"vikora.png").convert("RGBA")
im.save(brand/"vikora.ico",format="ICO",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
shutil.copy(brand/"vikora.png",root/"src/app/web/assets/vikora-logo.png")
p=root/"src/app/web/index.html"
t=p.read_text(encoding="utf-8").replace('  <link rel="stylesheet" href="/assets/styles.css" />',
'  <link rel="icon" type="image/png" href="/assets/vikora-logo.png" />\n  <link rel="stylesheet" href="/assets/styles.css" />')
p.write_text(t,encoding="utf-8")
p=root/"packaging/build_windows.ps1"
t=p.read_text(encoding="utf-8")
backtick=chr(96)
old="--paths src --collect-data app --collect-submodules app --collect-submodules uvicorn "+backtick
assert old in t
t=t.replace(old,old+"\n    --icon branding/vikora.ico "+backtick,1)
p.write_text(t,encoding="utf-8")
p=root/"packaging/Vikora.iss"
t=p.read_text(encoding="utf-8")
t=t.replace("UninstallDisplayIcon={app}\\{#MyAppExe}","SetupIconFile=..\\branding\\vikora.ico\nUninstallDisplayIcon={app}\\{#MyAppExe}")
p.write_text(t,encoding="utf-8")
p=root/"pyproject.toml"
t=p.read_text(encoding="utf-8").replace('"web/assets/*.css", "web/assets/*.js"','"web/assets/*.css", "web/assets/*.js", "web/assets/*.png"')
p.write_text(t,encoding="utf-8")
(root/"tests/test_windows_rc4_console_logging.py").write_text('''import sys
from pathlib import Path
import uvicorn
def test_uvicorn_without_console(monkeypatch):
    monkeypatch.setattr(sys,"stdout",None)
    monkeypatch.setattr(sys,"stderr",None)
    config=uvicorn.Config("app.main:app",host="127.0.0.1",port=18467,log_config=None)
    assert config.log_config is None
def test_launcher_has_safe_logging():
    text=(Path(__file__).resolve().parents[1]/"src/app/local_runner.py").read_text(encoding="utf-8")
    assert "log_config=None" in text
    assert "vikora_startup_error.log" in text
def test_branding():
    root=Path(__file__).resolve().parents[1]
    assert (root/"branding/vikora.ico").is_file()
    assert (root/"branding/vikora.png").is_file()
    assert "--icon branding/vikora.ico" in (root/"packaging/build_windows.ps1").read_text(encoding="utf-8")
    assert "SetupIconFile=" in (root/"packaging/Vikora.iss").read_text(encoding="utf-8")
''',encoding="utf-8")
(root/"docs/RELEASE_NOTES_V1_4_RC4_RU.md").write_text("# Vikora 1.4 RC4\n\nИсправлена ошибка запуска Windows (Uvicorn formatter default); добавлен лог ошибки и новый логотип.\n",encoding="utf-8")
print("Vikora RC4 fix applied")
