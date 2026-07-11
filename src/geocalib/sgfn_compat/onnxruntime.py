"""Import-only ONNX Runtime stub; SGFN confirmatory inference never exports ONNX."""


class InferenceSession:  # pragma: no cover - ONNX export is outside this experiment.
    def __init__(self, *args, **kwargs):
        raise RuntimeError("onnxruntime_disabled_for_sgfn_confirmatory_inference")

