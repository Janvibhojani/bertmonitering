from __future__ import annotations

import argparse
import logging

from Services.nlp_service import generate_train_files
from Services.spacy_trainer import train_ner


def main():
    logging.basicConfig(level=logging.INFO)

    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True, help="Directory containing scraped .json files")
    ap.add_argument("--out-dir", default="training_data", help="Where to write train/dev jsonl")
    ap.add_argument("--model-dir", default="models/financial_ner", help="Where to save spaCy model")
    ap.add_argument("--n-iter", type=int, default=20, help="Number of training iterations")
    ap.add_argument("--dropout", type=float, default=0.3, help="Dropout rate used during training")
    args = ap.parse_args()

    info = generate_train_files(input_dir=args.input_dir, out_dir=args.out_dir)
    train_path = info["train"]

    model_path = train_ner(
        train_path=train_path,
        output_dir=args.model_dir,
        n_iter=args.n_iter,
        dropout=args.dropout,
    )
    print("Done. Model saved to:", model_path)


if __name__ == "__main__":
    main()
