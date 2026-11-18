import math
from numbers import Real


def validate_features(payload, feature_names):
    if not isinstance(payload, dict):
        raise ValueError("The request body must be a JSON object.")
    if "features" not in payload:
        raise ValueError("Missing required field: features.")

    features = payload["features"]
    if isinstance(features, dict):
        expected = set(feature_names)
        provided = set(features)
        missing = sorted(expected - provided)
        extra = sorted(provided - expected)
        if missing or extra:
            details = []
            if missing:
                details.append("missing feature names: " + ", ".join(missing))
            if extra:
                details.append("unexpected feature names: " + ", ".join(extra))
            raise ValueError("; ".join(details) + ".")
        values = [features[name] for name in feature_names]
    elif isinstance(features, list):
        if len(features) != len(feature_names):
            raise ValueError(
                "Expected {} features in this order: {}.".format(
                    len(feature_names), ", ".join(feature_names)
                )
            )
        values = features
    else:
        raise ValueError("features must be an array or an object keyed by feature name.")

    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(
                "Feature {!r} must be a JSON number.".format(feature_names[index])
            )
        if not math.isfinite(value):
            raise ValueError(
                "Feature {!r} must be finite.".format(feature_names[index])
            )

    return [float(value) for value in values]
