import os
from pathlib import Path
from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix
from hosted_auth import create_application

application = ProxyFix(create_application(Path(os.environ.get('PREDICTOR_CONFIG', '/run/secrets/predictor_config'))), x_proto=1)
if __name__ == '__main__':
    serve(application, host='0.0.0.0', port=8000, threads=2,
          clear_untrusted_proxy_headers=False, max_request_body_size=16*1024*1024)
