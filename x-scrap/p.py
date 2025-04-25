import asyncio
import json
from twikit import Client

async def main():
    client = Client()

    await client.login(
        auth_info_1="meowdev88",
        auth_info_2="gauradashari@gmail.com",
        password="meowdev03"
    )

    # Target user
    username = "vwakesahu"
    user = await client.get_user_by_screen_name(username)

    # Get latest 5 tweets
    tweets = await user.get_tweets("Tweets", count=5)

    # Store tweet data
    data = []

    for tweet in tweets:
        data.append({
            "text": tweet.text,
            "created_at": tweet.created_at,
            "likes": tweet.favorite_count,
            "retweets": tweet.retweet_count,
            "replies": tweet.reply_count,
            "quotes": tweet.quote_count,
            "bookmarks": tweet.bookmark_count,
            "views": tweet.view_count,
        })

    # Save to JSON file
    with open(f"{username}_tweets.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(data)} tweets to {username}_tweets.json")

asyncio.run(main())
