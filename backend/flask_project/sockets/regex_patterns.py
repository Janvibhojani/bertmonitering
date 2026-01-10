

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

# ============================================================
# Regex-based entity extraction (for TRAINING DATA)
# ============================================================

Entity = Tuple[int, int, str]

NUM = r"[\d,]+(?:\.\d+)?"

# --- Word entities ---
RE_GOLD_WORD = re.compile(r"\bGOLD\b", re.IGNORECASE)
RE_SILVER_WORD = re.compile(r"\bSILVER\b", re.IGNORECASE)

# Purity / weight markers (often appear in gold products; label as GOLD for training usefulness)
RE_PURITY = re.compile(
    r"\b(995|9999?|999\.9|100GMS?|50GM|200GM|10\s?GM|100\s?GM|1KG|500GM)\b",
    re.IGNORECASE,
)

# Combined tokens like GOLD995MUM, SILVER999AHD
RE_COMBINED_GOLD = re.compile(r"\bGOLD[0-9A-Z]+\b", re.IGNORECASE)
RE_COMBINED_SILVER = re.compile(r"\bSILVER[0-9A-Z]+\b", re.IGNORECASE)

# High / Low variations: capture label + number (we label the number span as HIGH/LOW)
RE_HIGH_FULL = re.compile(
    rf"\bH(?:IGH)?\s*[-:|]?\s*(?P<v>{NUM})", re.IGNORECASE)
RE_LOW_FULL = re.compile(rf"\bL(?:OW)?\s*[-:|]?\s*(?P<v>{NUM})", re.IGNORECASE)

# Inline ranges (pipe separated): first=LOW, second=HIGH
RE_RANGE_PIPE = re.compile(rf"(?P<low>{NUM})\s*\|\s*(?P<high>{NUM})")

# Space-separated ranges (rare): two large numbers next to each other
RE_RANGE_SPACE = re.compile(
    rf"(?<!\d)(?P<low>\d{{4,7}}(?:\.\d+)?)\s+(?P<high>\d{{4,7}}(?:\.\d+)?)(?!\d)")

# Currency markers
RE_CURRENCY = re.compile(r"\b(INR|RS)\b|[$₹]", re.IGNORECASE)

# Time stamps
RE_TIME = re.compile(r"\b\d{1,2}:\d{2}:\d{2}\b")

# City names and abbreviations (extend as needed)
RE_CITY = re.compile(
    r"\b(CHENNAI|MUMBAI|DELHI|RAIPUR|COIMBATORE|BANGALORE|HYDERABAD|VIJAYWADA|VJA|CHE|CBE|AHD)\b",
    re.IGNORECASE,
)

# BUY / SELL markers
RE_BUY = re.compile(r"\bBUY\b", re.IGNORECASE)
RE_SELL = re.compile(r"\bSELL\b", re.IGNORECASE)


def extract_entities(text: str) -> List[Entity]:
    """
    Returns: List of (start_char, end_char, label)
    Used by your training pipeline to create spaCy training examples.
    """
    if not text:
        return []

    entities: List[Entity] = []
    occupied: Set[int] = set()

    def add(start: int, end: int, label: str):
        if start >= end or start < 0 or end > len(text):
            return
        for pos in range(start, end):
            if pos in occupied:
                return
        entities.append((start, end, label))
        occupied.update(range(start, end))

    # GOLD / SILVER words
    for m in RE_GOLD_WORD.finditer(text):
        add(m.start(), m.end(), "GOLD")
    for m in RE_SILVER_WORD.finditer(text):
        add(m.start(), m.end(), "SILVER")

    # Combined tokens
    for m in RE_COMBINED_GOLD.finditer(text):
        add(m.start(), m.end(), "GOLD")
    for m in RE_COMBINED_SILVER.finditer(text):
        add(m.start(), m.end(), "SILVER")

    # Purity markers (tag as GOLD)
    for m in RE_PURITY.finditer(text):
        add(m.start(), m.end(), "GOLD")

    # HIGH / LOW numeric values (label the NUMBER span)
    for m in RE_HIGH_FULL.finditer(text):
        v = m.group("v")
        if v:
            add(m.start("v"), m.end("v"), "HIGH")

    for m in RE_LOW_FULL.finditer(text):
        v = m.group("v")
        if v:
            add(m.start("v"), m.end("v"), "LOW")

    # Ranges
    for m in RE_RANGE_PIPE.finditer(text):
        add(m.start("low"), m.end("low"), "LOW")
        add(m.start("high"), m.end("high"), "HIGH")

    for m in RE_RANGE_SPACE.finditer(text):
        add(m.start("low"), m.end("low"), "LOW")
        add(m.start("high"), m.end("high"), "HIGH")

    # Currency / Time / City
    for m in RE_CURRENCY.finditer(text):
        add(m.start(), m.end(), "CURRENCY")

    for m in RE_TIME.finditer(text):
        add(m.start(), m.end(), "TIME")

    for m in RE_CITY.finditer(text):
        add(m.start(), m.end(), "CITY")

    # BUY / SELL
    for m in RE_BUY.finditer(text):
        add(m.start(), m.end(), "BUY")
    for m in RE_SELL.finditer(text):
        add(m.start(), m.end(), "SELL")

    return sorted(entities, key=lambda x: (x[0], x[1]))


# ============================================================
# Decoder for Playwright inner_text -> normalized records
# ============================================================

_HEADER_NOISE = re.compile(
    r"^(product|commodity|buy|sell|bid|ask|delivery|dt|time)\b", re.I)

# "GOLD ($)" etc.
_RE_USD_ASSET = re.compile(r"^(gold|silver|inr)\s*\(\s*[$₹]?\s*\)\s*$", re.I)
# "GOLD SPOT"
_RE_SPOT_ASSET = re.compile(r"^(gold|silver|inr)\s*spot\s*$", re.I)

# "Gold Current" / "Silver Current" / "Gold Costing"
_RE_CURRENT_LABEL = re.compile(r"^(gold|silver)\s+(current|costing)\s*$", re.I)

# "GOLD" / "SILVER" / "INR" as a plain line (could be a section header OR a vertical block label)
_RE_PLAIN_ASSET = re.compile(r"^(gold|silver|inr)\s*\.?\s*$", re.I)

_RE_LOW = re.compile(rf"(?i)\bL(?:OW)?\s*[:\-]?\s*(?P<v>{NUM})")
_RE_HIGH = re.compile(rf"(?i)\bH(?:IGH)?\s*[:\-]?\s*(?P<v>{NUM})")

# A line that's ONLY a number
_RE_ONLY_NUM = re.compile(rf"^{NUM}$")

# A product-ish line: name \t value [\t value]
_RE_PRODUCT_LINE = re.compile(
    rf"^(?P<name>.+?)(?:\t+|\s{{2,}})(?P<v1>{NUM}|--|-)(?:(?:\t+|\s{{2,}})(?P<v2>{NUM}|--|-))?\s*$",
    re.I,
)


def _to_float(x: Optional[str]) -> Optional[float]:
    if not x:
        return None
    x = x.strip()
    if x in {"-", "--"}:
        return None
    try:
        return float(x.replace(",", ""))
    except Exception:
        return None


def _section_from_name(name: str) -> str:
    n = name.lower()
    if "gold" in n:
        return "GOLD"
    if "silver" in n:
        return "SILVER"
    if "inr" in n or "₹" in n or re.search(r"\brs\b", n):
        return "INR"
    return "OTHER"


def _keys_from_text(name: str) -> List[str]:
    up = name.upper()
    return [k for k in ("GOLD", "SILVER", "INR") if k in up]


def _safe_strip(line: str) -> str:
    # keep tabs for parsing; strip only outer whitespace
    return line.strip(" \r")


def decode_inner_text(inner_text: str, time_str: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Decode raw inner_text into records:
      {Section, Name, Buy, Sell, Low, High, Time, keys?}

    Goal: work across many bullion sites with mixed formats.
    """
    if not inner_text or not inner_text.strip():
        return []

    t = time_str or datetime.now().strftime("%H:%M:%S")

    # Keep tabs; remove empty lines
    raw_lines = [_safe_strip(ln) for ln in inner_text.splitlines()]
    lines = [ln for ln in raw_lines if ln and not ln.isspace()]

    records: List[Dict[str, Any]] = []

    # Helper to add summary
    def add_summary(name: str, buy: Optional[float], low: Optional[float], high: Optional[float],
                    sell: Optional[float] = None, keys: Optional[List[str]] = None):
        if buy is None and sell is None and low is None and high is None:
            return
        rec = {
            "Section": "SUMMARY",
            "Name": name,
            "Buy": buy,
            "Sell": sell if sell is not None else buy,
            "Low": low,
            "High": high,
            "Time": t,
            "is_summary": True,
        }
        if keys:
            rec["keys"] = keys
        records.append(rec)

    # ============================================================
    # PASS 1: USD summary blocks like:
    #   GOLD ($)
    #   4451.35
    #   4428.85 | 4476.20
    # ============================================================
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = _RE_USD_ASSET.match(line)
        if m:
            asset = m.group(1).upper()
            price = _to_float(lines[i + 1]) if i + 1 < len(lines) else None
            low = high = None
            if i + 2 < len(lines):
                rng = RE_RANGE_PIPE.search(lines[i + 2])
                if rng:
                    low = _to_float(rng.group("low"))
                    high = _to_float(rng.group("high"))
            # Only treat as this summary style if a range/L/H is present.
            if low is not None or high is not None:
                add_summary(asset, price, low, high, keys=[asset])
            i += 3
            continue
        i += 1

    # ============================================================

    # ============================================================
    # PASS 1b: Plain asset blocks (no ($)) like:
    #   GOLD
    #   4453.05
    #   L: 4428.02 | H: 4475.79
    # ============================================================
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = _RE_PLAIN_ASSET.match(line)
        if m and i + 1 < len(lines) and _RE_ONLY_NUM.match(lines[i + 1].strip()):
            asset = m.group(1).upper().rstrip(".")
            price = _to_float(lines[i + 1].strip())
            low = high = None
            if i + 2 < len(lines):
                # supports "L: low | H: high" or "L: low" and "H: high"
                rng = RE_RANGE_PIPE.search(lines[i + 2])
                if rng:
                    low = _to_float(rng.group("low"))
                    high = _to_float(rng.group("high"))
                ml = _RE_LOW.search(lines[i + 2])
                mh = _RE_HIGH.search(lines[i + 2])
                if ml and low is None:
                    low = _to_float(ml.group("v"))
                if mh and high is None:
                    high = _to_float(mh.group("v"))
                # sometimes low/high are on subsequent lines
                if (low is None or high is None):
                    for j in range(i + 2, min(i + 6, len(lines))):
                        if low is None:
                            ml2 = _RE_LOW.search(lines[j])
                            if ml2:
                                low = _to_float(ml2.group("v"))
                        if high is None:
                            mh2 = _RE_HIGH.search(lines[j])
                            if mh2:
                                high = _to_float(mh2.group("v"))
            # Only treat as this summary style if a range/L/H is present.
            if low is not None or high is not None:
                add_summary(asset, price, low, high, keys=[asset])
        i += 1

# PASS 2: SPOT blocks like:
    #   GOLD SPOT
    #
    #   4452.28
    #
    #   H : 4475.81
    #   L : 4428.14
    # ============================================================
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = _RE_SPOT_ASSET.match(line)
        if m:
            asset = m.group(1).upper()
            # scan next ~8 lines for price + H + L
            price = low = high = None
            for j in range(i + 1, min(i + 15, len(lines))):
                lj = lines[j].strip()
                if _RE_SPOT_ASSET.match(lj):
                    break
                if price is None and _RE_ONLY_NUM.match(lj):
                    price = _to_float(lj)
                mh = _RE_HIGH.search(lj)
                if mh:
                    high = _to_float(mh.group("v"))
                ml = _RE_LOW.search(lj)
                if ml:
                    low = _to_float(ml.group("v"))
            add_summary(f"{asset}_SPOT", price, low, high, keys=[asset])
            i += 1
            continue
        i += 1

    # ============================================================
    # PASS 3: "Gold Current"/"Silver Current"/"Gold Costing" blocks:
    #   Gold Current
    #   136590 | 136610
    #   HIGH | 136999   LOW | 136523
    # ============================================================
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = _RE_CURRENT_LABEL.match(line)
        if m and i + 1 < len(lines):
            asset = m.group(1).upper()
            kind = m.group(2).upper()  # CURRENT / COSTING
            # buy|sell line
            buy = sell = low = high = None
            rng = RE_RANGE_PIPE.search(lines[i + 1])
            if rng:
                buy = _to_float(rng.group("low"))
                sell = _to_float(rng.group("high"))
            elif _RE_ONLY_NUM.match(lines[i + 1].strip()):
                buy = _to_float(lines[i + 1].strip())
                sell = buy
            # high/low line
            if i + 2 < len(lines):
                mh = _RE_HIGH.search(lines[i + 2])
                ml = _RE_LOW.search(lines[i + 2])
                if mh:
                    high = _to_float(mh.group("v"))
                if ml:
                    low = _to_float(ml.group("v"))
            add_summary(f"{asset}_{kind}", buy, low,
                        high, sell=sell, keys=[asset])
            i += 3
            continue
        i += 1

    # ============================================================
    # PASS 4: Vertical 4-number blocks:
    #   GOLD
    #   138276
    #   138776
    #   138298
    #   138001
    # interpreted as: Buy, High, Sell, Low  (common in your feeds)
    # ============================================================
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = _RE_PLAIN_ASSET.match(line)
        if m:
            asset = m.group(1).upper().rstrip(".")
            nums: List[float] = []
            j = i + 1
            while j < len(lines) and len(nums) < 4:
                if _RE_ONLY_NUM.match(lines[j].strip()):
                    v = _to_float(lines[j].strip())
                    if v is not None:
                        nums.append(v)
                    j += 1
                    continue
                # allow empty-ish spacer lines that sometimes appear as "\t"
                if lines[j].strip() in {"", "\t"}:
                    j += 1
                    continue
                break

            if len(nums) >= 4:
                buy, high, sell, low = nums[0], nums[1], nums[2], nums[3]
                add_summary(f"{asset}_VERT", buy, low,
                            high, sell=sell, keys=[asset])
                i = j
                continue
        i += 1

    # ============================================================
    # PASS 5: Tables and product lists (stateful)
    # - "PRODUCT\tBUY\tSELL" tables with interleaved L/H lines
    # - Simple section lists under "GOLD" / "SILVER" headings
    # ============================================================
    current_section: Optional[str] = None
    last_product: Optional[Dict[str, Any]] = None

    def finalize_product(rec: Dict[str, Any]):
        # If buy missing but sell present, copy sell to buy
        if rec.get("Buy") is None and rec.get("Sell") is not None:
            rec["Buy"] = rec["Sell"]
        if rec.get("Sell") is None and rec.get("Buy") is not None:
            rec["Sell"] = rec["Buy"]

    for line in lines:
        s = line.strip()

        # Skip obvious headers
        if _HEADER_NOISE.match(s):
            last_product = None
            continue

        # Update current section when we see a plain section header
        msec = _RE_PLAIN_ASSET.match(s)
        if msec:
            # Treat as section header ONLY if next to it doesn't look like a vertical block (we already handled vertical pass)
            current_section = msec.group(1).upper().rstrip(".")
            last_product = None
            continue

        # L/H attachment lines
        if last_product is not None:
            ml = _RE_LOW.search(s)
            if ml:
                last_product["Low"] = _to_float(ml.group("v"))
                # some sites put SELL as 2nd column on the same low line: "L : 135891\t136149"
                parts = s.split("\t")
                if len(parts) >= 2:
                    cand = _to_float(parts[-1])
                    if cand is not None:
                        last_product["Sell"] = cand
                continue

            mh = _RE_HIGH.search(s)
            if mh:
                last_product["High"] = _to_float(mh.group("v"))
                continue

            # Sometimes SELL appears as a standalone numeric line with leading tab
            if _RE_ONLY_NUM.match(s) and (last_product.get("Sell") is None or last_product.get("Buy") is None):
                v = _to_float(s)
                if v is not None:
                    # Prefer filling Sell first if Buy already exists
                    if last_product.get("Buy") is not None and last_product.get("Sell") is None:
                        last_product["Sell"] = v
                    elif last_product.get("Buy") is None:
                        last_product["Buy"] = v
                continue

        # Product line
        mp = _RE_PRODUCT_LINE.match(s)
        if mp:
            name = (mp.group("name") or "").strip()
            # hard-skip fake rows like "L : 12345"
            if re.fullmatch(rf"(?i)[lh](?:ow|igh)?\s*[:\-]?\s*{NUM}", name.strip()):
                continue

            v1 = _to_float(mp.group("v1"))
            v2 = _to_float(mp.group("v2"))

            # Decide section
            section = _section_from_name(name) if _section_from_name(
                name) != "OTHER" else (current_section or "OTHER")

            # Treat COSTING rows as SUMMARY (common across sites)
            if "COSTING" in name.upper() and section in {"GOLD", "SILVER"}:
                rec = {
                    "Section": "SUMMARY",
                    "Name": f"{section}_COSTING",
                    "Buy": v1,
                    "Sell": v2 if v2 is not None else v1,
                    "Low": None,
                    "High": None,
                    "Time": t,
                    "is_summary": True,
                    "keys": [section],
                }
            else:
                rec = {
                    "Section": section,
                    "Name": name,
                    "Buy": v1,
                    "Sell": v2 if v2 is not None else v1,
                    "Low": None,
                    "High": None,
                    "Time": t,
                }
            k = _keys_from_text(name)
            if k:
                rec["keys"] = k

            records.append(rec)
            last_product = rec
            continue

        # If line didn't match anything, reset product attachment when we hit another header-ish block
        if s.upper().startswith(("BUY", "SELL", "BID", "ASK", "PRODUCT")):
            last_product = None

    # Finalize + cleanup duplicates
    for r in records:
        if r.get("Section") != "SUMMARY":
            finalize_product(r)

    # Filter out product rows with no prices at all
    filtered: List[Dict[str, Any]] = []
    for r in records:
        if r.get("Section") == "SUMMARY":
            # allow summaries even if only low/high
            if r.get("Buy") is None and r.get("Sell") is None and r.get("Low") is None and r.get("High") is None:
                continue
            filtered.append(r)
        else:
            if r.get("Buy") is None and r.get("Sell") is None:
                continue
            filtered.append(r)

    # Deduplicate exact duplicates
    seen = set()
    uniq: List[Dict[str, Any]] = []
    for r in filtered:
        key = (r.get("Section"), r.get("Name"), r.get("Buy"), r.get(
            "Sell"), r.get("Low"), r.get("High"), r.get("is_summary", False))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)

    return uniq


__all__ = ["decode_inner_text", "extract_entities"]
