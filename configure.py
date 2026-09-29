import getpass,json,secrets,os
from pathlib import Path
from urllib.parse import urlsplit
from werkzeug.security import generate_password_hash
origin=input('Public HTTPS origin (for example https://predictor.example.org): ').strip().rstrip('/')
u=urlsplit(origin)
if u.scheme!='https' or not u.hostname or u.path or u.query or u.fragment or u.username or u.port:
    raise SystemExit('Enter an HTTPS domain without path, credentials, or port.')
a=getpass.getpass('Choose a NEW predictor password (at least 12 characters): ')
b=getpass.getpass('Repeat password: ')
if a!=b or len(a)<12:raise SystemExit('Passwords must match and contain at least 12 characters.')
p=Path('secrets');p.mkdir(mode=0o700,exist_ok=True)
config=p/'config.json'
if config.exists():raise SystemExit('Existing config preserved. Move it explicitly before reconfiguring.')
fd=os.open(config,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:json.dump({'password_hash':generate_password_hash(a),'secret_key':secrets.token_hex(32),'mount_path':'','public_origin':origin},f)
# Container uid must be able to read the mounted secret; keep its parent directory private.
config.chmod(0o644)
Path('.env').write_text('PREDICTOR_DOMAIN='+u.hostname+'\n')
print('Configuration saved. Keep secrets/ and .env private.')
