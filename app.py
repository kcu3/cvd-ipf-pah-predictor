"""Local research prediction website. Run in PyCharm with Python 3.12."""
import os
from threading import Lock
from flask import Flask, abort, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge
from schema import DISEASES
from predictor import MODELS, MODEL_ERRORS, load_models, predict, validate_row
from spreadsheets import read_upload, template_workbook, result_workbook, MAX_ROWS
from presentation import probability_result

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
prediction_lock = Lock()
load_models()


def disease_from_request():
    disease = request.values.get('disease', 'cvd').lower()
    if disease not in DISEASES:
        abort(400, description='Choose cvd, ipf or pah.')
    return disease


@app.after_request
def headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    disease = disease_from_request()
    errors, result, values, status = [], None, {}, 200
    if request.method == 'POST':
        values = request.form.to_dict()
        if disease not in MODELS:
            errors, status = ['This model is unavailable. Run check_setup.py for details.'], 503
        else:
            parsed, errors = validate_row(disease, values)
            status = 400 if errors else 200
            if not errors:
                try:
                    with prediction_lock:
                        result = probability_result(disease, predict(disease, [parsed])[0])
                except Exception:
                    app.logger.exception('Single prediction failed for %s', disease)
                    errors = ['Prediction failed. No result was produced. See the local server console.']
                    status = 503
    return render_template('index.html', disease=disease, diseases=DISEASES,
                           cfg=DISEASES[disease], fields=DISEASES[disease]['fields'],
                           result=result, errors=errors, values=values,
                           model_error=MODEL_ERRORS.get(disease), max_rows=MAX_ROWS,
                           defaults={f['name']: format(MODELS[disease]['medians'][f['model_feature']], '.12g')
                                     for f in DISEASES[disease]['fields']} if disease in MODELS else {}), status


def xlsx_response(stream, name):
    return send_file(stream, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=name)


@app.get('/template')
def template():
    disease = disease_from_request()
    if disease not in MODELS:
        abort(503, description='Model unavailable. Run check_setup.py.')
    return xlsx_response(template_workbook(disease), f'{disease}_input_template.xlsx')


@app.post('/batch')
def batch():
    disease = disease_from_request()
    if disease not in MODELS:
        abort(503, description='Model unavailable. Run check_setup.py.')
    upload = request.files.get('file')
    if upload is None or not upload.filename:
        abort(400, description='Choose an .xlsx or UTF-8 .csv file.')
    try:
        headers_, records = read_upload(upload, disease)
    except ValueError as exc:
        abort(400, description=str(exc))
    results, valid_rows, positions = [], [], []
    for source_row, record in records:
        parsed, errors = validate_row(disease, record)
        formula_fields = [name for name, val in record.items() if isinstance(val, str) and val.startswith('=')]
        if formula_fields:
            errors.append('Formulas are not accepted: ' + ', '.join(formula_fields))
        results.append({'source_row': source_row, 'status': 'invalid' if errors else 'ok',
                        'error': '; '.join(errors), 'input': record})
        if not errors:
            positions.append(len(results)-1)
            valid_rows.append(parsed)
    if valid_rows:
        try:
            with prediction_lock:
                for start in range(0, len(valid_rows), 256):
                    predictions = predict(disease, valid_rows[start:start+256])
                    for position, prediction in zip(positions[start:start+256], predictions):
                        public = probability_result(disease, prediction)
                        results[position].update(public)
        except Exception:
            app.logger.exception('Batch prediction failed for %s', disease)
            abort(503, description='Prediction failed. No results file was produced. See the local console.')
    return xlsx_response(result_workbook(disease, headers_, results), f'{disease}_predictions.xlsx')


@app.get('/health')
def health():
    models = {d: {'status': 'ok', 'features': len(b['features']), 'pu_models': len(b['models']), 'ten_year_probability_available': d == 'cvd'}
              for d, b in MODELS.items()}
    models.update({d: {'status': 'error', 'detail': e} for d, e in MODEL_ERRORS.items()})
    return {'status': 'ok' if not MODEL_ERRORS else 'error', 'models': models}, (200 if not MODEL_ERRORS else 503)


@app.errorhandler(400)
@app.errorhandler(413)
@app.errorhandler(503)
def error_page(error):
    message = 'File too large. Maximum upload size is 16 MB.' if isinstance(error, RequestEntityTooLarge) else error.description
    return render_template('error.html', message=message), error.code


if __name__ == '__main__':
    import errno
    from waitress import create_server
    port = int(os.environ.get('PORT', '5001'))
    if MODEL_ERRORS:
        print('Model errors: run check_setup.py for diagnosis.', flush=True)
    try:
        server = create_server(app, host='127.0.0.1', port=port, threads=2,
                               max_request_body_size=16*1024*1024)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            raise SystemExit(f'Port {port} is already in use. Stop the earlier website process, '
                             'or set PORT=5002 in the PyCharm run configuration. '
                             'This run did not start a server.') from None
        raise
    print(f'Open http://127.0.0.1:{port} (Ctrl+C or PyCharm Stop to stop)', flush=True)
    server.run()
