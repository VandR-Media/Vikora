"""Repair test expectations inherited from RC5 after applying RC6."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/'tests/test_rc6_frontend.py'
s=p.read_text(encoding='utf-8')
old='dashboard=s.split("async function openDashboard(){",1)[1].split("async function loadAllPages",1)[0]'
new='dashboard=s.split("async function openDashboard",1)[1].split("async function loadAllPages",1)[0]'
assert old in s
p.write_text(s.replace(old,new),encoding='utf-8')
p=root/'tests/test_windows_rc3.py'
s=p.read_text(encoding='utf-8')
assert "assert '1.4.0-rc5' in proc.stdout" in s
p.write_text(s.replace("assert '1.4.0-rc5' in proc.stdout", "assert '1.4.0-rc6' in proc.stdout"),encoding='utf-8')
print('Updated RC6 test expectations')
