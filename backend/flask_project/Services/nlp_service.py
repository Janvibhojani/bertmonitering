from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

# Prefer project-local regex patterns (training_data/regex_patterns.py)
try:
    from sockets.regex_patterns import extract_entities  # type: ignore
except Exception:  # pragma: no cover
    from regex_patterns import extract_entities  # type: ignore


TEXT_KEYS = ("inner_text", "text", "content", "message")


def _iter_text_fields(
    obj: Any,
    *,
    max_depth: int = 12,
    _depth: int = 0,
    _seen: Optional[Set[int]] = None,
) -> Iterable[str]:
    """Yield text only from known keys in nested dict/list structures.

    Safety features:
    - max_depth to avoid runaway recursion
    - _seen set to avoid revisiting the same object
    """
    if obj is None:
        return

    if _seen is None:
        _seen = set()

    if _depth > max_depth:
        return

    oid = id(obj)
    if oid in _seen:
        return
    _seen.add(oid)

    if isinstance(obj, dict):
        for k in TEXT_KEYS:
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                yield v.strip()

        for v in obj.values():
            yield from _iter_text_fields(v, max_depth=max_depth, _depth=_depth + 1, _seen=_seen)

    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_text_fields(item, max_depth=max_depth, _depth=_depth + 1, _seen=_seen)


def generate_train_files(
    input_dir: str,
    out_dir: str = "training_data",
    min_chars: int = 30,
    dev_ratio: float = 0.15,
    seed: int = 13,
    max_file_mb: int = 25,
    max_texts_per_file: int = 2000,
) -> Dict[str, Any]:
    """Create spaCy NER JSONL training files from scraped JSONs in `input_dir`.

    Writes:
      - {out_dir}/train.jsonl
      - {out_dir}/dev.jsonl (optional)

    Raises ValueError if no examples with entities are produced.
    """
    in_path = Path(input_dir)
    if not in_path.exists() or not in_path.is_dir():
        raise FileNotFoundError(f"input_dir does not exist or is not a directory: {input_dir}")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    train_path = out_path / "train.jsonl"
    dev_path = out_path / "dev.jsonl"

    json_files = sorted(in_path.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No .json files found in: {input_dir}")

    texts_scanned = 0
    examples: List[Dict[str, Any]] = []

    for fp in json_files:
        # Skip very large files to avoid long reads / recursion blowups
        try:
            size_mb = fp.stat().st_size / (1024 * 1024)
            if size_mb > max_file_mb:
                logging.warning("Skipping large file (%.1f MB): %s", size_mb, fp)
                continue
        except Exception:
            pass

        logging.info("Processing JSON: %s", fp)

        try:
            raw = fp.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(raw)
        except Exception as e:
            logging.warning("Skipping invalid JSON file %s: %s", fp, e)
            continue

        count = 0
        for text in _iter_text_fields(data, max_depth=12):
            count += 1
            if count > max_texts_per_file:
                logging.warning("Stopping early in %s after %d text fields", fp, max_texts_per_file)
                break

            text = text.strip()
            if len(text) < min_chars:
                continue

            texts_scanned += 1

            try:
                ents = extract_entities(text)  # List[(start, end, label)]
            except Exception as e:
                logging.warning("Error extracting entities from text in %s: %s", fp, e)
                continue

            if not ents:
                continue

            norm_ents: List[List[Any]] = []
            for start, end, label in ents:
                norm_ents.append([int(start), int(end), str(label)])

            examples.append({"text": text, "entities": norm_ents})

    rng = random.Random(seed)
    rng.shuffle(examples)

    if not examples:
        train_path.write_text("", encoding="utf-8")
        if dev_path.exists():
            dev_path.unlink()
        raise ValueError(
            f"No training examples with entities were produced. "
            f"Scanned {texts_scanned} texts from {len(json_files)} json files. "
            f"Check your regex_patterns.extract_entities() rules or your scraped JSON format."
        )

    dev_examples: List[Dict[str, Any]] = []
    train_examples: List[Dict[str, Any]] = examples

    if dev_ratio and 0 < dev_ratio < 1 and len(examples) >= 5:
        cut = max(1, int(len(examples) * dev_ratio))
        dev_examples = examples[:cut]
        train_examples = examples[cut:]

    with train_path.open("w", encoding="utf-8") as f:
        for ex in train_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    dev_out: Optional[str] = None
    if dev_examples:
        with dev_path.open("w", encoding="utf-8") as f:
            for ex in dev_examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        dev_out = str(dev_path)
    else:
        if dev_path.exists():
            dev_path.unlink()

    return {
        "train": str(train_path),
        "dev": dev_out,
        "texts_scanned": texts_scanned,
        "examples_with_entities": len(examples),
        "out_dir": str(out_path),
    }


class FinancialNERService:
    def __init__(self, model_dir: str = "models/financial_ner"):
        self.model_dir = model_dir

    def generate(
        self,
        input_dir: str,
        out_dir: str = "training_data",
        min_chars: int = 30,
        dev_ratio: float = 0.15,
    ):
        return generate_train_files(
            input_dir=input_dir,
            out_dir=out_dir,
            min_chars=min_chars,
            dev_ratio=dev_ratio,
        )
