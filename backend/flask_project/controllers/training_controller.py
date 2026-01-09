import os
from flask import Blueprint, request, jsonify

from Services.nlp_service import generate_train_files
from Services.spacy_trainer import train_ner

training_bp = Blueprint("training", __name__)


@training_bp.route("/generate", methods=["POST"])
def generate():
    data = request.json or {}

    input_dir = data.get("input_dir")
    out_dir = data.get("out_dir", "training_data")
    min_chars = data.get("min_chars", 30)
    dev_ratio = data.get("dev_ratio", 0.15)

    if not input_dir or not os.path.exists(input_dir):
        return jsonify({"error": "input_dir does not exist"}), 400

    info = generate_train_files(
        input_dir=input_dir,
        out_dir=out_dir,
        min_chars=min_chars,
        dev_ratio=dev_ratio
    )

    return jsonify(info)


@training_bp.route("/train", methods=["POST"])
def train():
    data = request.json or {}

    train_path = data.get("train_path")
    output_dir = data.get("output_dir", "models/financial_ner")
    n_iter = data.get("n_iter", 20)

    if not train_path or not os.path.exists(train_path):
        return jsonify({"error": "train_path does not exist"}), 400

    model_path = train_ner(
        train_path=train_path,
        output_dir=output_dir,
        n_iter=n_iter
    )

    return jsonify({
        "status": "trained",
        "model_path": model_path
    })
