from fetch_x_posts import fetch_posts
from filter_posts import filter_posts
from summarize import summarize_posts
from export_md import export_markdown

def main():
    posts = fetch_posts()
    filtered = filter_posts(posts)
    summary = summarize_posts(filtered)
    export_markdown(summary)

if __name__ == "__main__":
    main()
