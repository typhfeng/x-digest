def summarize_posts(posts):

    summaries = []

    for p in posts:
        summaries.append({
            "author": p["author"],
            "summary": p["text"]
        })

    return summaries
