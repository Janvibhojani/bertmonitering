from flask import Blueprint, request, jsonify
from Services.spacy_trainer import predict

spacy_bp = Blueprint("spacy", __name__)


@spacy_bp.route("/predict", methods=["POST"])
def predict_entities():
    data = request.json or {}

    model_dir = data.get("model_dir", "models/financial_ner")
    text = data.get("text")

    if not text:
        return jsonify({"error": "text is required"}), 400

    ents = predict(model_dir, text)
    return jsonify({"entities": ents})
