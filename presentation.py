"""Present calibrated estimates and original classifier scores distinctly."""
def probability_result(disease, prediction):
    probability = prediction.get('calibrated_probability')
    available = disease == 'cvd' and probability is not None
    score = None if available else prediction['pu_score']
    return {
        'calibrated_probability': probability if available else None,
        'model_score': score,
        'probability_status': 'available' if available else 'score_available',
        'message': '',
        'imputed_count': prediction['imputed_count'],
        'imputed_features': prediction['imputed_features'],
    }
