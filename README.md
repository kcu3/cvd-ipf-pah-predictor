# CVD / IPF / PAH predictor

This package contains the Flask application, Docker build definition, Compose deployment, HTTPS reverse proxy configuration, password setup, and model checksums. It does not contain patient records or live credentials. The model assets are attached to a private release in this repository.

## Repository and model assets

This private repository keeps the application and deployment files together. The model archive is stored in this repository's private Releases because it is too large for a regular Git file. Repository access is required to download it.

```sh
git clone https://github.com/kcu3/cvd-ipf-pah-predictor.git
cd cvd-ipf-pah-predictor
```

Download `predictor_model_assets.zip` from [the private release](https://github.com/kcu3/cvd-ipf-pah-predictor/releases/tag/v1.0.0) and extract it here, creating `models/`. Keep the archive and model files out of Git. `MODEL_SHA256.json` and `verify_models.py` verify each extracted model file.

## Requirements

A Linux server with Docker Engine and Docker Compose v2, at least 4 GB RAM (8 GB recommended), and approximately 5 GB free disk space. Use one predictor service instance initially. Point a dedicated hostname at the server. Ports 80 and 443 must be available to Caddy. This configuration serves the predictor at the hostname root; it does not replace an existing site or automatically modify DNS.

## Deployment

From the repository root, after extracting the model archive:

```sh
python3 -m venv .setup-venv
. .setup-venv/bin/activate
pip install Werkzeug==3.1.8
python configure.py
python verify_models.py
docker compose build --pull
docker compose up -d
docker compose ps
```

Use Python 3.12 for setup. `configure.py` prompts for the HTTPS origin and a NEW password twice. It generates a password hash and random session key locally. It does not reuse the existing website password. Keep `secrets/` and `.env` out of source control. The private parent directory restricts host access; the config file is readable by the unprivileged container user through its read-only secret mount.

Caddy obtains and renews a TLS certificate for the configured domain. The application port is not published to the host. Open the HTTPS domain, sign in, and test CVD, IPF and PAH using **Fill typical values**. Download each Excel template, fill its Data sheet and upload it to obtain a results workbook. Do not use actual patient records for the deployment smoke test.

The container health check verifies the login service only. Models load after authenticated access; use the authenticated `/health` endpoint to verify all three models. Loading is lazy, so the first authenticated request takes longer.

## Existing reverse proxy

If the recipient already operates an HTTPS reverse proxy, integrate the `predictor` service with that proxy instead of starting the bundled Caddy service. Preserve the secret and model mounts, forward the original HTTPS scheme, and do not expose port 8000 directly. `server.py` trusts one proxy's scheme header and assumes only the trusted proxy can reach it. Adjust the deployment network accordingly.

## Operation

```sh
docker compose logs --tail=100 predictor
docker compose restart predictor
docker compose down
```

Model files are mounted read-only; uploads are processed in memory and are not written by the application. Avoid adding request-body logging at the proxy. Session cookies are secure and expire after eight hours. Authentication is required for prediction, templates, assets, and model health. Login throttling is process-local; add proxy-level throttling if scaling to multiple replicas. Preserve the Caddy data volume for certificates.

## Model interpretation and provenance

CVD uses the supplied UKBB PU forest with the BBRU adapter/calibration. IPF and PAH display their supplied model scores as percentages; this packaging does not add clinical calibration or change endpoints. The compact CVD representation stores the original tree decisions and leaf outputs without retraining. All 50 forests were compared with the originals over 257 synthetic/decision-boundary cases; maximum absolute difference was 8.33e-16.

The weights and preprocessing summaries are UKBB/BBRU-derived artifacts, not raw records. Their inclusion is not a determination of permission to redistribute them; the project holder should confirm the recipient and permitted use under the applicable project arrangements.


