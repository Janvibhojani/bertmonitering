# helpers.py
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime

def parse_gold_table(text: str) -> pd.DataFrame:
    """
    Universal parser for bullion site inner_text.
    Handles multiple formats (tabs, pipes, newlines).
    """
    # Split by newline & tab, clean
    lines = [line.strip() for line in re.split(r"[\n\r]+", text) if line.strip()]
    rows = []
    now = datetime.now().strftime("%H:%M:%S")

    for line in lines:
        # Split by tab or pipe
        parts = [p.strip() for p in re.split(r"[\t|]", line) if p.strip()]
        if not parts:
            continue

        # Extract all numbers (ints & floats)
        nums = re.findall(r"\d+(?:\.\d+)?", line)

        # Case 1: Direct Gold/Silver/INR line
        if any(word in parts[0].upper() for word in ["GOLD", "SILVER", "INR"]):
            name = parts[0]
            buy = sell = high = low = ""

            if len(nums) == 1:
                buy = sell = nums[0]
            elif len(nums) == 2:
                buy, sell = nums[0], nums[1]
            elif len(nums) == 3:  # Some sites give Buy | Low | High
                buy, low, high = nums[0], nums[1], nums[2]
            elif len(nums) >= 4:
                buy, sell, high, low = nums[0], nums[1], nums[2], nums[3]

            rows.append([name, buy, sell, low, high, now])

        # Case 2: Product-based rows (India Gold, Gold 995, etc.)
        else:
            if nums:
                first_num_index = line.find(nums[0])
                name = line[:first_num_index].strip() if first_num_index > 0 else parts[0]

                buy = sell = high = low = ""
                if len(nums) == 1:
                    buy = sell = nums[0]
                elif len(nums) == 2:
                    buy, sell = nums[0], nums[1]
                elif len(nums) == 3:
                    buy, low, high = nums[0], nums[1], nums[2]
                elif len(nums) >= 4:
                    buy, sell, high, low = nums[0], nums[1], nums[2], nums[3]

                if name:
                    rows.append([name, buy, sell, low, high, now])

    # Final DataFrame
    return pd.DataFrame(rows, columns=["Name", "Buy", "Sell", "Low", "High", "Time"])


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df.replace({"-": None, "": None}, inplace=True)
    for col in ["Buy", "Sell", "Low", "High"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def parse_table(raw_text):
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    table = []
    for line in lines:
        cols = [col.strip() for col in line.split("\t") if col.strip() != ""]
        table.append(cols)
    return table  

def clean_html(html: str, remove_attrs=("class", "className", "id", "style")):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(True):
        for attr in remove_attrs:
            if attr in tag.attrs:
                del tag.attrs[attr]
    return str(soup)  

