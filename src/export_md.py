from datetime import datetime
import os

def export_markdown(posts):

    os.makedirs("output", exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")

    with open(f"output/digest_{today}.md", "w") as f:

        f.write(f"# X Digest {today}\n\n")

        for p in posts:

            f.write(f"## {p['author']}\n")
            f.write(f"{p['summary']}\n\n")
