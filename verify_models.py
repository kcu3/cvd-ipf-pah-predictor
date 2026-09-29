import hashlib,json
from pathlib import Path
for name,expected in json.loads(Path('MODEL_SHA256.json').read_text()).items():
    p=Path(name)
    if not p.is_file() or hashlib.file_digest(p.open('rb'),'sha256').hexdigest()!=expected:
        raise SystemExit('Missing or changed model file: '+name)
print('All model checksums verified.')
