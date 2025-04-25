from facebook_scraper import get_posts, set_cookies

set_cookies("cookies.txt")

for post in get_posts('nasa', pages=2):
    print(post['text'][:100])
    print(f"👍 {post['likes']} 💬 {post['comments']} 🔁 {post['shares']}")
    print("-" * 60)
