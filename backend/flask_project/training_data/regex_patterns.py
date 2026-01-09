
# # import re
# # from typing import List, Tuple, Set, Dict, Any, Optional
# # from datetime import datetime

# # # ============================================================
# # # ENTITY EXTRACTION (FOR TRAINING DATA / NER TRAINING FILES)
# # # ============================================================

# # Entity = Tuple[int, int, str]

# # # --- Word entities ---
# # RE_GOLD_WORD = re.compile(r"\bGOLD\b", re.IGNORECASE)
# # RE_SILVER_WORD = re.compile(r"\bSILVER\b", re.IGNORECASE)

# # # Purity / weight markers (often appear in gold products; label as GOLD for training usefulness)
# # RE_PURITY = re.compile(
# #     r"\b(995|9999?|999\.9|100GMS?|50GM|200GM|10\s?GM|100\s?GM|1KG|500GM)\b",
# #     re.IGNORECASE,
# # )

# # # Combined tokens like GOLD995MUM, SILVER999AHD
# # RE_COMBINED_GOLD = re.compile(r"\bGOLD[0-9A-Z]+\b", re.IGNORECASE)
# # RE_COMBINED_SILVER = re.compile(r"\bSILVER[0-9A-Z]+\b", re.IGNORECASE)

# # # High / Low variations: capture label + number (we label the number span as HIGH/LOW)
# # RE_HIGH_FULL = re.compile(
# #     r"\bH(?:IGH)?\s*[-:|]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
# # RE_LOW_FULL = re.compile(
# #     r"\bL(?:OW)?\s*[-:|]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)

# # # Inline ranges (pipe separated): first=LOW, second=HIGH (as per your previous datasets)
# # RE_RANGE_PIPE = re.compile(r"(\d+(?:\.\d+)?)\s*\|\s*(\d+(?:\.\d+)?)")

# # # Space separated ranges (rare): two large numbers next to each other
# # RE_RANGE_SPACE = re.compile(
# #     r"(?<!\d)(\d{4,7}(?:\.\d+)?)\s+(\d{4,7}(?:\.\d+)?)(?!\d)")

# # # Currency markers
# # RE_CURRENCY = re.compile(r"\b(INR|RS)\b|[$₹]", re.IGNORECASE)

# # # Time stamps
# # RE_TIME = re.compile(r"\b\d{1,2}:\d{2}:\d{2}\b")

# # # City names and abbreviations (extend as needed)
# # RE_CITY = re.compile(
# #     r"\b(CHENNAI|MUMBAI|DELHI|RAIPUR|COIMBATORE|BANGALORE|HYDERABAD|VIJAYWADA|VJA|CHE|CBE|AHD)\b",
# #     re.IGNORECASE,
# # )

# # # BUY / SELL markers
# # RE_BUY = re.compile(r"\bBUY\b", re.IGNORECASE)
# # RE_SELL = re.compile(r"\bSELL\b", re.IGNORECASE)


# # def extract_entities(text: str) -> List[Entity]:
# #     """
# #     Returns: List of (start_char, end_char, label)
# #     This is used by your training pipeline to create NER training examples.
# #     """
# #     entities: List[Entity] = []
# #     occupied: Set[int] = set()

# #     def add(start: int, end: int, label: str):
# #         # validate span
# #         if start >= end or start < 0 or end > len(text):
# #             return
# #         # avoid overlap
# #         for pos in range(start, end):
# #             if pos in occupied:
# #                 return
# #         entities.append((start, end, label))
# #         occupied.update(range(start, end))

# #     # GOLD / SILVER
# #     for m in RE_GOLD_WORD.finditer(text):
# #         add(m.start(), m.end(), "GOLD")
# #     for m in RE_SILVER_WORD.finditer(text):
# #         add(m.start(), m.end(), "SILVER")

# #     # Combined tokens
# #     for m in RE_COMBINED_GOLD.finditer(text):
# #         add(m.start(), m.end(), "GOLD")
# #     for m in RE_COMBINED_SILVER.finditer(text):
# #         add(m.start(), m.end(), "SILVER")

# #     # Purity markers (tag as GOLD — matches your earlier pattern)
# #     for m in RE_PURITY.finditer(text):
# #         add(m.start(), m.end(), "GOLD")

# #     # HIGH / LOW numeric values
# #     for m in RE_HIGH_FULL.finditer(text):
# #         # group(1) is the number
# #         val = m.group(1)
# #         if val:
# #             val_start = text.find(val, m.start())
# #             if val_start != -1:
# #                 add(val_start, val_start + len(val), "HIGH")

# #     for m in RE_LOW_FULL.finditer(text):
# #         val = m.group(1)
# #         if val:
# #             val_start = text.find(val, m.start())
# #             if val_start != -1:
# #                 add(val_start, val_start + len(val), "LOW")

# #     # Ranges
# #     for m in RE_RANGE_PIPE.finditer(text):
# #         add(m.start(1), m.end(1), "LOW")
# #         add(m.start(2), m.end(2), "HIGH")

# #     for m in RE_RANGE_SPACE.finditer(text):
# #         add(m.start(1), m.end(1), "LOW")
# #         add(m.start(2), m.end(2), "HIGH")

# #     # Currency / Time / City
# #     for m in RE_CURRENCY.finditer(text):
# #         add(m.start(), m.end(), "CURRENCY")

# #     for m in RE_TIME.finditer(text):
# #         add(m.start(), m.end(), "TIME")

# #     for m in RE_CITY.finditer(text):
# #         add(m.start(), m.end(), "CITY")

# #     # BUY / SELL
# #     for m in RE_BUY.finditer(text):
# #         add(m.start(), m.end(), "BUY")
# #     for m in RE_SELL.finditer(text):
# #         add(m.start(), m.end(), "SELL")

# #     return sorted(entities, key=lambda x: (x[0], x[1]))


# # # ============================================================
# # # TABLE DECODER (FOR SCRAPING / NORMALIZATION)
# # # ============================================================

# # NUM = r"[\d,]+(?:\.\d+)?"


# # def _num(x: Optional[str]) -> Optional[float]:
# #     if not x or x in {"-", "--"}:
# #         return None
# #     try:
# #         return float(x.replace(",", ""))
# #     except ValueError:
# #         return None


# # RE_SUMMARY = re.compile(
# #     rf"""
# #     ^\s*(gold|silver|inr)\b.*?$          # Asset
# #     \s*(?P<price>{NUM})\s*$              # Main price
# #     (?:
# #         \s*L\s*[:\-]?\s*(?P<low1>{NUM})
# #         |
# #         \s*(?P<low2>{NUM})\s*\|\s*(?P<high2>{NUM})
# #     )
# #     .*?
# #     (?:
# #         H\s*[:\-]?\s*(?P<high1>{NUM})
# #         |
# #         (?P<high3>{NUM})
# #     )?
# #     """,
# #     re.IGNORECASE | re.MULTILINE | re.VERBOSE,
# # )

# # RE_ROW_HEADER = re.compile(
# #     r"^(product|commodity|buy|sell|bid|ask|delivery|time)\b",
# #     re.IGNORECASE,
# # )

# # RE_PRODUCT_ROW = re.compile(
# #     rf"""
# #     ^\s*
# #     (?P<name>[A-Za-z0-9().\-+/%\s₹]+?)   # product name
# #     \s*(?:\t+|\s{{2,}})
# #     (?P<price>{NUM}|--|-)
# #     """,
# #     re.IGNORECASE | re.MULTILINE | re.VERBOSE,
# # )

# # RE_LOW = re.compile(rf"L\s*[:\-]?\s*(?P<low>{NUM})", re.IGNORECASE)
# # RE_HIGH = re.compile(rf"H\s*[:\-]?\s*(?P<high>{NUM})", re.IGNORECASE)


# # _NUM = r"[\d,]+(?:\.\d+)?"
# # _RE_HEADER_NOISE = re.compile(
# #     r"^(product|commodity|buy|sell|bid|ask|delivery|dt|time)\b", re.I)


# # def decode_inner_text(inner_text: str, time_str: Optional[str] = None) -> List[Dict[str, Any]]:
# #     """Decode raw inner_text into a uniform records list.

# #     Handles ALL formats from the training data:
# #     1. Simple summary blocks (GOLD, SILVER, INR, GOLD COSTING)
# #     2. Tabular formats with BUY/SELL columns
# #     3. Product lists with prices
# #     4. Mixed formats
# #     """
# #     if not inner_text or not inner_text.strip():
# #         return []

# #     t = time_str or datetime.now().strftime("%H:%M:%S")
# #     records: List[Dict[str, Any]] = []
# #     lines = [ln.rstrip() for ln in inner_text.splitlines() if ln.strip()]

# #     # ============================================================
# #     # 1. FIRST PASS: Extract SUMMARY sections (GOLD, SILVER, INR, GOLD COSTING)
# #     # ============================================================

# #     i = 0
# #     while i < len(lines):
# #         line = lines[i].strip()
# #         line_upper = line.upper()

# #         # Handle GOLD, SILVER, INR, GOLD COSTING summary blocks
# #         if line_upper in ["GOLD", "SILVER", "INR", "GOLD COSTING", "GOLD.", "SILVER.", "INR."]:
# #             asset = line_upper.rstrip('.')

# #             # Check next line for price
# #             if i + 1 < len(lines):
# #                 price_line = lines[i + 1].strip()

# #                 # Extract the first number from the price line
# #                 price_match = re.search(r'(' + NUM + r')', price_line)
# #                 price = _num(price_match.group(1)) if price_match else None

# #                 low = None
# #                 high = None

# #                 # Check current line + next line for L:/H: patterns
# #                 combined_lines = f"{line} {price_line}"

# #                 # Also check line i+2 for range patterns
# #                 if i + 2 < len(lines):
# #                     next_next_line = lines[i + 2].strip()
# #                     combined_lines += f" {next_next_line}"

# #                     # Check for pipe separated range (e.g., "4428.02 | 4475.79")
# #                     if "|" in next_next_line:
# #                         range_parts = next_next_line.split("|")
# #                         if len(range_parts) >= 2:
# #                             low_part = range_parts[0].strip()
# #                             high_part = range_parts[1].strip()

# #                             # Check for L: or H: prefixes
# #                             if "L:" in low_part or "L :" in low_part:
# #                                 low_match = RE_LOW.search(low_part)
# #                                 if low_match:
# #                                     low = _num(low_match.group("low"))
# #                             else:
# #                                 low = _num(low_part)

# #                             if "H:" in high_part or "H :" in high_part:
# #                                 high_match = RE_HIGH.search(high_part)
# #                                 if high_match:
# #                                     high = _num(high_match.group("high"))
# #                             else:
# #                                 high = _num(high_part)

# #                 # If still no low/high, search in combined lines
# #                 if low is None:
# #                     low_match = RE_LOW.search(combined_lines)
# #                     if low_match:
# #                         low = _num(low_match.group("low"))

# #                 if high is None:
# #                     high_match = RE_HIGH.search(combined_lines)
# #                     if high_match:
# #                         high = _num(high_match.group("high"))

# #                 if price is not None:
# #                     records.append({
# #                         "Section": "SUMMARY",
# #                         "Name": asset,
# #                         "Buy": price,
# #                         "Sell": price,
# #                         "Low": low,
# #                         "High": high,
# #                         "Time": t,
# #                     })

# #                 # Skip the lines we processed
# #                 if i + 2 < len(lines) and "|" in lines[i + 2]:
# #                     i += 3  # Skip asset, price, and range line
# #                 else:
# #                     i += 2  # Skip asset and price line
# #                 continue

# #         # Handle GOLD ($), SILVER ($), INR($) format
# #         elif any(x in line_upper for x in ["GOLD ($", "SILVER ($", "INR($", "GOLD($"]):
# #             # Extract asset name
# #             if "GOLD" in line_upper:
# #                 asset = "GOLD"
# #             elif "SILVER" in line_upper:
# #                 asset = "SILVER"
# #             elif "INR" in line_upper:
# #                 asset = "INR"
# #             else:
# #                 asset = line.split()[0].upper()

# #             # Look for price in next line
# #             if i + 1 < len(lines):
# #                 price_line = lines[i + 1].strip()
# #                 price = _num(price_line)

# #                 low = None
# #                 high = None

# #                 # Check line i+2 for range
# #                 if i + 2 < len(lines):
# #                     range_line = lines[i + 2].strip()

# #                     # Check for pipe separated range
# #                     if "|" in range_line:
# #                         range_parts = range_line.split("|")
# #                         if len(range_parts) >= 2:
# #                             low = _num(range_parts[0].strip())
# #                             high = _num(range_parts[1].strip())
# #                     else:
# #                         # Check for separate L: and H: in following lines
# #                         for j in range(i + 2, min(i + 5, len(lines))):
# #                             if low is None:
# #                                 low_match = RE_LOW.search(lines[j])
# #                                 if low_match:
# #                                     low = _num(low_match.group("low"))
# #                             if high is None:
# #                                 high_match = RE_HIGH.search(lines[j])
# #                                 if high_match:
# #                                     high = _num(high_match.group("high"))

# #                 if price is not None:
# #                     records.append({
# #                         "Section": "SUMMARY",
# #                         "Name": asset,
# #                         "Buy": price,
# #                         "Sell": price,
# #                         "Low": low,
# #                         "High": high,
# #                         "Time": t,
# #                     })

# #                 i += 1  # Just increment by 1, let loop handle rest
# #                 continue

# #         # Handle GOLD SPOT, SILVER SPOT, INR SPOT format
# #         elif "SPOT" in line_upper:
# #             asset = line_upper.replace("SPOT", "").strip()
# #             if not asset:
# #                 asset = line.split()[0].upper(
# #                 ) if line.split() else line.upper()

# #             # Look for price in next lines
# #             price = None
# #             low = None
# #             high = None

# #             # Price is usually on line i+2 (skip empty line)
# #             if i + 2 < len(lines):
# #                 price_line = lines[i + 2].strip()
# #                 if re.match(r'^' + NUM + r'$', price_line):
# #                     price = _num(price_line)

# #             # Look for H: and L: in following lines
# #             for j in range(i, min(i + 6, len(lines))):
# #                 line_j = lines[j].strip()

# #                 if "H :" in line_j or "H:" in line_j:
# #                     high_match = RE_HIGH.search(line_j)
# #                     if high_match:
# #                         high = _num(high_match.group("high"))

# #                 if "L :" in line_j or "L:" in line_j:
# #                     low_match = RE_LOW.search(line_j)
# #                     if low_match:
# #                         low = _num(low_match.group("low"))

# #             if price is not None:
# #                 records.append({
# #                     "Section": "SUMMARY",
# #                     "Name": asset,
# #                     "Buy": price,
# #                     "Sell": price,
# #                     "Low": low,
# #                     "High": high,
# #                     "Time": t,
# #                 })

# #             i += 1
# #             continue

# #         i += 1

# #     # ============================================================
# #     # 2. SECOND PASS: Extract other summary formats
# #     # ============================================================

# #     # Look for India Gold, India Silver, Gold Current, Silver Current, etc.
# #     for i, line in enumerate(lines):
# #         line_upper = line.upper()

# #         # India Gold / Gold Current pattern
# #         if any(x in line_upper for x in ["INDIA GOLD", "GOLD CURRENT", "GOLD COSTING"]):
# #             parts = line.split('\t')
# #             if len(parts) >= 2:
# #                 name = parts[0].strip()
# #                 buy_price = _num(parts[1].strip()) if len(parts) > 1 else None
# #                 sell_price = _num(parts[2].strip()) if len(parts) > 2 else None
# #                 high_low = parts[3].strip() if len(parts) > 3 else ""

# #                 # Extract high/low from the last part
# #                 low = high = None
# #                 if "/" in high_low:
# #                     hl_parts = high_low.split("/")
# #                     if len(hl_parts) >= 2:
# #                         high = _num(hl_parts[0].strip())
# #                         low = _num(hl_parts[1].strip())

# #                 records.append({
# #                     "Section": "SUMMARY",
# #                     "Name": name.upper(),
# #                     "Buy": buy_price if buy_price is not None else sell_price,
# #                     "Sell": sell_price,
# #                     "Low": low,
# #                     "High": high,
# #                     "Time": t,
# #                 })

# #         # India Silver / Silver Current pattern
# #         elif any(x in line_upper for x in ["INDIA SILVER", "SILVER CURRENT", "SILVER COSTING"]):
# #             parts = line.split('\t')
# #             if len(parts) >= 2:
# #                 name = parts[0].strip()
# #                 buy_price = _num(parts[1].strip()) if len(parts) > 1 else None
# #                 sell_price = _num(parts[2].strip()) if len(parts) > 2 else None
# #                 high_low = parts[3].strip() if len(parts) > 3 else ""

# #                 # Extract high/low from the last part
# #                 low = high = None
# #                 if "/" in high_low:
# #                     hl_parts = high_low.split("/")
# #                     if len(hl_parts) >= 2:
# #                         high = _num(hl_parts[0].strip())
# #                         low = _num(hl_parts[1].strip())

# #                 records.append({
# #                     "Section": "SUMMARY",
# #                     "Name": name.upper(),
# #                     "Buy": buy_price if buy_price is not None else sell_price,
# #                     "Sell": sell_price,
# #                     "Low": low,
# #                     "High": high,
# #                     "Time": t,
# #                 })

# #     # ============================================================
# #     # 3. THIRD PASS: Look for table structures with BUY/SELL
# #     # ============================================================

# #     # Find the start of a table (look for PRODUCT header or BUY/SELL header)
# #     table_start = -1
# #     for idx, line in enumerate(lines):
# #         if ("PRODUCT" in line.upper() and ("BUY" in line.upper() or "SELL" in line.upper())) or \
# #            ("BUY" in line.upper() and "SELL" in line.upper() and "PRODUCT" not in line.upper()):
# #             table_start = idx
# #             break

# #     if table_start >= 0:
# #         i = table_start + 1  # Skip header

# #         while i < len(lines):
# #             line = lines[i].strip()

# #             # Skip empty lines or header-like lines
# #             if not line or _RE_HEADER_NOISE.match(line):
# #                 i += 1
# #                 continue

# #             # Check if this is a product line (contains GOLD/SILVER and doesn't start with L:/H:)
# #             if ("GOLD" in line.upper() or "SILVER" in line.upper()) and \
# #                not line.startswith(("L :", "H :", "L:", "H:")):

# #                 product_name = line.split('\t')[0].strip(
# #                 ) if '\t' in line else line.strip()

# #                 # Initialize values
# #                 buy_price = None
# #                 sell_price = None
# #                 low_price = None
# #                 high_price = None

# #                 # Parse the current line for BUY price
# #                 parts = line.split('\t')
# #                 if len(parts) >= 2:
# #                     # The second part might be BUY price
# #                     potential_buy = parts[1].strip()
# #                     if potential_buy and potential_buy not in ["-", "--"]:
# #                         buy_price = _num(potential_buy)

# #                 # Look ahead for L:/H: lines and SELL price
# #                 for offset in range(1, min(5, len(lines) - i)):
# #                     next_line = lines[i + offset].strip()

# #                     # Look for L: line
# #                     if next_line.startswith("L :") or next_line.startswith("L:"):
# #                         # Extract LOW price
# #                         low_match = RE_LOW.search(next_line)
# #                         if low_match:
# #                             low_price = _num(low_match.group("low"))

# #                         # Check if SELL price is on the same line (after tab)
# #                         l_parts = next_line.split('\t')
# #                         if len(l_parts) >= 2:
# #                             sell_candidate = l_parts[-1].strip()
# #                             if sell_candidate and sell_candidate not in ["-", "--"]:
# #                                 sell_price = _num(sell_candidate)

# #                     # Look for H: line
# #                     elif next_line.startswith("H :") or next_line.startswith("H:"):
# #                         # Extract HIGH price
# #                         high_match = RE_HIGH.search(next_line)
# #                         if high_match:
# #                             high_price = _num(high_match.group("high"))

# #                         # Check if SELL price is on H: line if not found yet
# #                         if sell_price is None:
# #                             h_parts = next_line.split('\t')
# #                             if len(h_parts) >= 2:
# #                                 sell_candidate = h_parts[-1].strip()
# #                                 if sell_candidate and sell_candidate not in ["-", "--"]:
# #                                     sell_price = _num(sell_candidate)

# #                     # If no L:/H: markers, check if it's a standalone SELL price
# #                     elif sell_price is None and not any(x in next_line.upper() for x in ["PRODUCT", "BUY", "SELL", "BID", "ASK"]):
# #                         # Might be a standalone SELL price line
# #                         if re.search(NUM, next_line):
# #                             sell_price = _num(next_line.split(
# #                                 '\t')[0] if '\t' in next_line else next_line)

# #                 # For products with "-" or "--" in BUY, use SELL price for both
# #                 if buy_price is None and sell_price is not None:
# #                     buy_price = sell_price

# #                 # Determine section
# #                 lname = product_name.lower()
# #                 if "gold" in lname:
# #                     section = "GOLD"
# #                 elif "silver" in lname:
# #                     section = "SILVER"
# #                 elif "inr" in lname:
# #                     section = "INR"
# #                 else:
# #                     section = "OTHER"

# #                 # Add record if we have any price
# #                 if buy_price is not None or sell_price is not None:
# #                     records.append({
# #                         "Section": section,
# #                         "Name": product_name,
# #                         "Buy": buy_price,
# #                         "Sell": sell_price if sell_price is not None else buy_price,
# #                         "Low": low_price,
# #                         "High": high_price,
# #                         "Time": t,
# #                     })

# #                 # Skip the L: and H: lines we processed
# #                 if low_price is not None or high_price is not None:
# #                     i += 3  # Skip product line, L: line, and H: line
# #                 else:
# #                     i += 1
# #             else:
# #                 i += 1

# #     # ============================================================
# #     # 4. FOURTH PASS: Look for simple product lists (no table headers)
# #     # ============================================================

# #     # If we didn't find a table structure, look for simple product lists
# #     if not any("PRODUCT" in line.upper() or ("BUY" in line.upper() and "SELL" in line.upper()) for line in lines):
# #         i = 0
# #         while i < len(lines):
# #             line = lines[i].strip()

# #             # Skip headers and summary sections we already processed
# #             if _RE_HEADER_NOISE.match(line) or \
# #                line.upper() in ["GOLD", "SILVER", "INR", "GOLD COSTING", "GOLD.", "SILVER.", "INR."] or \
# #                any(x in line.upper() for x in ["GOLD ($", "SILVER ($", "INR($", "GOLD($", "SPOT"]):
# #                 i += 1
# #                 continue

# #             # Try to match product row pattern (name followed by price)
# #             if ("GOLD" in line.upper() or "SILVER" in line.upper()) and '\t' in line:
# #                 parts = line.split('\t')
# #                 if len(parts) >= 2:
# #                     name = parts[0].strip()
# #                     price = _num(parts[1].strip())

# #                     if price is not None:
# #                         # Determine section
# #                         lname = name.lower()
# #                         if "gold" in lname:
# #                             section = "GOLD"
# #                         elif "silver" in lname:
# #                             section = "SILVER"
# #                         elif "inr" in lname:
# #                             section = "INR"
# #                         else:
# #                             section = "OTHER"

# #                         records.append({
# #                             "Section": section,
# #                             "Name": name,
# #                             "Buy": price,
# #                             "Sell": price,
# #                             "Low": None,
# #                             "High": None,
# #                             "Time": t,
# #                         })

# #             i += 1

# #     # ============================================================
# #     # 5. CLEAN UP: Remove duplicates and empty records
# #     # ============================================================

# #     # Remove records with no prices at all
# #     filtered_records = []
# #     for record in records:
# #         if record["Buy"] is not None or record["Sell"] is not None:
# #             filtered_records.append(record)

# #     # Remove exact duplicates (same name and all values)
# #     unique_records = []
# #     seen = set()
# #     for record in filtered_records:
# #         key = (record["Name"], record["Buy"],
# #                record["Sell"], record["Low"], record["High"])
# #         if key not in seen:
# #             seen.add(key)
# #             unique_records.append(record)

# #     return unique_records


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
