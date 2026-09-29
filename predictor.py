"""Validated inference using supplied models, without fitting or retraining."""
from pathlib import Path
import json
import warnings
import joblib
import numpy as np
from scipy.special import expit
from sklearn.exceptions import InconsistentVersionWarning
from schema import DISEASES

MODEL_DIR = Path(__file__).resolve().parent / 'models'
MODELS, MODEL_ERRORS = {}, {}


def positive_probability(model, X):
    if list(model.classes_) != [0, 1]:
        raise ValueError('Expected binary classes [0, 1].')
    if hasattr(model, 'feature_names_in_'):
        import pandas as pd
        X = pd.DataFrame(X, columns=model.feature_names_in_)
    result = np.asarray(model.predict_proba(X), dtype=float)[:, 1]
    if not np.isfinite(result).all() or ((result < 0) | (result > 1)).any():
        raise ValueError('Model returned an invalid probability.')
    return result


def load_models():
    MODELS.clear()
    MODEL_ERRORS.clear()
    for disease in DISEASES:
        try:
            directory = MODEL_DIR / disease / 'ukbb_weights'
            features = directory.joinpath('feature_names.txt').read_text().split()
            if not features or len(features) != len(set(features)):
                raise ValueError('Feature names must be nonempty and unique.')
            import pandas as pd
            med = pd.read_csv(directory / 'feature_medians.tsv', sep='\t', index_col=0)
            if med.index.duplicated().any():
                raise ValueError('Duplicate feature medians.')
            medians = {k: float(med.loc[k, 'median']) for k in features}
            if not np.isfinite(list(medians.values())).all():
                raise ValueError('Feature medians must be finite.')
            with warnings.catch_warnings():
                warnings.simplefilter('error', InconsistentVersionWarning)
                if (directory / 'compact/manifest.json').exists():
                    from compact_forest import load_compact
                    models = load_compact(directory / 'compact')
                else:
                    models = joblib.load(directory / 'pu_models.joblib', mmap_mode='r')
                pn = joblib.load(directory / 'pn_model.joblib') if (directory / 'pn_model.joblib').exists() else None
            if not isinstance(models, (list, tuple)):
                models = [models]
            if not models:
                raise ValueError('Empty PU ensemble.')
            for model in list(models) + ([pn] if pn is not None else []):
                if model.n_features_in_ != len(features):
                    raise ValueError('Model feature count differs from the feature dictionary.')
                if hasattr(model, 'feature_names_in_') and list(model.feature_names_in_) != features:
                    raise ValueError('Model feature order differs from the feature dictionary.')
                if list(model.classes_) != [0, 1]:
                    raise ValueError('Unsupported model classes.')
                model.n_jobs = 1
            required = {f['model_feature'] for f in DISEASES[disease]['fields']}
            if not required.issubset(features):
                raise ValueError('Form fields do not match model features.')
            bundle = {'features': features, 'medians': medians, 'models': models, 'pn': pn}
            meta_file = directory / 'model_meta.json'
            bundle['meta'] = json.loads(meta_file.read_text()) if meta_file.exists() else {}
            if disease == 'cvd':
                deployment = json.loads((MODEL_DIR / 'cvd/deployment.json').read_text())
                if deployment['calibration_input'] != 'logit_of_adapter_probability':
                    raise ValueError('Unsupported calibration input.')
                if not 0 < deployment['epsilon'] < 0.5:
                    raise ValueError('Invalid calibration epsilon.')
                if set(deployment['adapter_features']) != required | {'pu_score'}:
                    raise ValueError('Unexpected adapter features.')
                bundle['deployment'] = deployment
            MODELS[disease] = bundle
            predict(disease, [medians])
        except Exception as exc:
            MODELS.pop(disease, None)
            MODEL_ERRORS[disease] = f'{type(exc).__name__}: {exc}'


def validate_row(disease, raw):
    values, errors = {}, []
    fields = DISEASES[disease]['fields']
    for field in fields:
        name, value = field['name'], raw.get(field['name'])
        if value is None or str(value).strip() == '':
            errors.append(f'{name}: required')
            continue
        try:
            if isinstance(value, bool) or str(value).startswith('='):
                raise ValueError
            value = float(value)
            if not np.isfinite(value):
                raise ValueError
        except (ValueError, TypeError, OverflowError):
            errors.append(f'{name}: enter a finite number')
            continue
        if field['type'] == 'select':
            if value not in {float(v) for v, _ in field['options']}:
                errors.append(f"{name}: expected one of {', '.join(v for v, _ in field['options'])}")
                continue
        elif not float(field['min']) <= value <= float(field['max']):
            errors.append(f"{name}: expected {field['min']}–{field['max']} {field['unit']}")
            continue
        values[name] = value
    for name in MODELS.get(disease, {}).get('features', []):
        if name in {f['name'] for f in fields}:
            continue
        value = raw.get(name)
        if value is None or str(value).strip() == '':
            continue
        try:
            if isinstance(value, bool):
                raise ValueError
            value = float(value)
            if not np.isfinite(value) or abs(value) > np.finfo(np.float32).max:
                raise ValueError
            values[name] = value
        except (ValueError, TypeError, OverflowError):
            errors.append(f'{name}: enter a finite number in training units or leave blank')
    return values, errors


def adapt_and_calibrate(deployment, X):
    X = np.asarray(X, dtype=float)
    X = np.where(np.isnan(X), deployment['imputer_statistics'], X)
    scaled = (X - deployment['scaler_mean']) / deployment['scaler_scale']
    raw = expit(scaled @ np.asarray(deployment['adapter_coef']) + deployment['adapter_intercept'])
    clipped = np.clip(raw, deployment['epsilon'], 1-deployment['epsilon'])
    logit = np.log(clipped / (1-clipped))
    calibrated = expit(logit * deployment['calibrator_coef'] + deployment['calibrator_intercept'])
    return raw, calibrated


def predict(disease, rows):
    bundle = MODELS[disease]
    X = np.asarray([[row.get(f, bundle['medians'][f]) for f in bundle['features']] for row in rows], dtype=float)
    if X.ndim != 2 or not np.isfinite(X).all():
        raise ValueError('Prediction inputs must be finite.')
    scores = np.stack([positive_probability(model, X) for model in bundle['models']])
    means, spreads = scores.mean(axis=0), scores.std(axis=0)
    pn = positive_probability(bundle['pn'], X) if bundle['pn'] is not None else None
    raw = calibrated = None
    if disease == 'cvd':
        deployment = bundle['deployment']
        adapted_scores = 1-means if deployment['flip_pu_score'] else means
        adapter_rows = [{**row, 'pu_score': score} for row, score in zip(rows, adapted_scores)]
        raw, calibrated = adapt_and_calibrate(deployment, [[r[f] for f in deployment['adapter_features']] for r in adapter_rows])
        if not np.isfinite(calibrated).all():
            raise ValueError('Invalid calibrated estimate.')
    results = []
    for i, row in enumerate(rows):
        filled = [f for f in bundle['features'] if f not in row]
        results.append({'pu_score': float(means[i]), 'pu_std': float(spreads[i]),
                        'adapter_score': float(raw[i]) if raw is not None else None,
                        'calibrated_probability': float(calibrated[i]) if calibrated is not None else None,
                        'pn_score': float(pn[i]) if pn is not None else None,
                        'imputed_features': ', '.join(filled), 'imputed_count': len(filled)})
    return results
