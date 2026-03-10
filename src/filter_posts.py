def filter_posts(posts):

    filtered = []

    for p in posts:
        if len(p["text"]) > 10:
            filtered.append(p)

    return filtered
