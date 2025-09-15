import time, random, re

def new_id(prefix: str) -> str:
    return f"{prefix}_{int(time.time()*1000)}_{random.randint(100,999)}"

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "x"
