from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import spacy
from spacy.training import Example
from spacy.util import minibatch


def _trim_entity_span(doc, start: int, end: int, label: str):
    """Trim common punctuation/currency around an entity span."""
    span = doc.char_span(start, end, label=label, alignment_mode="contract")
    if span is None:
        return None

    text = span.text
    clean_text = text.strip(".,()$₹ ")
    if not clean_text:
        return None

    start_offset = text.find(clean_text)
    new_start = span.start_char + start_offset
    new_end = new_start + len(clean_text)
    return doc.char_span(new_start, new_end, label=label, alignment_mode="contract")


def _remove_overlapping_entities(entities: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
    # Sort by start asc, then longer first (to keep bigger spans)
    entities = sorted(entities, key=lambda x: (x[0], -(x[1] - x[0])))
    cleaned: List[Tuple[int, int, str]] = []
    for start, end, label in entities:
        overlap = False
        for cs, ce, _ in cleaned:
            if start < ce and end > cs:
                overlap = True
                break
        if not overlap:
            cleaned.append((start, end, label))
    return cleaned


def _load_jsonl(path: Path) -> List[Tuple[str, Dict[str, Any]]]:
    data: List[Tuple[str, Dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            text = item.get("text", "")
            ents = item.get("entities", [])
            data.append((text, {"entities": ents}))
    return data


def train_ner(
    train_path: str,
    output_dir: str = "models/financial_ner",
    n_iter: int = 20,
    dropout: float = 0.3,
    batch_size: int = 8,
) -> str:
    """Train a simple spaCy NER model from a jsonl file created by nlp_service."""
    train_file = Path(train_path)
    if not train_file.exists():
        raise FileNotFoundError(f"train.jsonl not found: {train_path}")

    train_data = _load_jsonl(train_file)

    nlp = spacy.blank("en")
    ner = nlp.add_pipe("ner")

    # Add labels
    for _, ann in train_data:
        for start, end, label in ann.get("entities", []):
            ner.add_label(label)

    optimizer = nlp.begin_training()

    for i in range(n_iter):
        losses: Dict[str, float] = {}
        random.shuffle(train_data)

        for batch in minibatch(train_data, size=batch_size):
            examples: List[Example] = []

            for text, ann in batch:
                if not text:
                    continue

                doc = nlp.make_doc(text)
                entities = ann.get("entities", [])
                valid: List[Tuple[int, int, str]] = []

                for start, end, label in entities:
                    span = _trim_entity_span(doc, int(start), int(end), str(label))
                    if span is not None:
                        valid.append((span.start_char, span.end_char, str(label)))

                final_ents = _remove_overlapping_entities(valid)
                if not final_ents:
                    continue

                examples.append(Example.from_dict(doc, {"entities": final_ents}))

            if examples:
                # Some examples can still cause alignment issues; skip those batches safely.
                try:
                    nlp.update(examples, drop=dropout, losses=losses, sgd=optimizer)
                except ValueError:
                    continue

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(out)
    return str(out)


def predict(model_dir: str, text: str) -> List[Dict[str, Any]]:
    """Run NER prediction and return entities as JSON-serializable dicts."""
    nlp = spacy.load(model_dir)
    doc = nlp(text)
    ents: List[Dict[str, Any]] = []
    for ent in doc.ents:
        ents.append({
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char,
        })
    return ents
