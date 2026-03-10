from datetime import datetime
import os

def export(posts):
    os.makedirs("output", exist_ok=True)
    path = f"output/digest_{datetime.now().date()}.md"
    with open(path, "w") as f:
        f.write("# Digest\n\n")
        for p in posts:
            f.write(f"- {p['text']}\n")
    return path
