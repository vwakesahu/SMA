import asyncio
import json
import os
from datetime import datetime
from pymongo import MongoClient
import matplotlib.pyplot as plt
import seaborn as sns
from twikit import Client

# MongoDB connection
MONGO_URI = "mongodb+srv://userone:userone@cluster0.dni41vz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "twitter_data"
COLLECTION_NAME = "tweets"

async def scrape_tweets(username, count=5):
    """Scrape tweets from a specific user"""
    client = Client()
    
    await client.login(
        auth_info_1="meowdev88",
        auth_info_2="gauradashari@gmail.com",
        password="meowdev03"
    )
    
    # Get user
    user = await client.get_user_by_screen_name(username)
    
    # Get tweets
    tweets = await user.get_tweets("Tweets", count=count)
    
    # Store tweet data
    data = []
    
    for tweet in tweets:
        tweet_data = {
            "username": username,
            "text": tweet.text,
            "created_at": tweet.created_at,
            "likes": tweet.favorite_count,
            "retweets": tweet.retweet_count,
            "replies": tweet.reply_count,
            "quotes": tweet.quote_count,
            "bookmarks": tweet.bookmark_count,
            "views": tweet.view_count,
            "scraped_at": datetime.now().isoformat()
        }
        data.append(tweet_data)
    
    return data

def store_in_mongodb(data):
    """Store tweet data in MongoDB"""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # Insert data
    result = collection.insert_many(data)
    
    print(f"✅ Stored {len(result.inserted_ids)} tweets in MongoDB")
    return len(result.inserted_ids)

def retrieve_from_mongodb(username):
    """Retrieve tweets for a specific user from MongoDB"""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # Query data
    cursor = collection.find({"username": username}, {"_id": 0})
    
    # Process and validate data before returning
    tweets = []
    for doc in cursor:
        # Ensure all required fields exist and have valid values
        processed_doc = {
            "username": doc.get("username", username),
            "text": doc.get("text", ""),
            "created_at": doc.get("created_at", ""),
            "likes": int(doc.get("likes", 0) or 0),  # Convert to int, default to 0 if None or falsy
            "retweets": int(doc.get("retweets", 0) or 0),
            "replies": int(doc.get("replies", 0) or 0),
            "quotes": int(doc.get("quotes", 0) or 0),
            "bookmarks": int(doc.get("bookmarks", 0) or 0),
            "views": int(doc.get("views", 0) or 0),
            "scraped_at": doc.get("scraped_at", "")
        }
        tweets.append(processed_doc)
    
    print(f"📊 Retrieved {len(tweets)} tweets from MongoDB for user {username}")
    return tweets

def create_visualizations(tweets, username):
    """Create visualizations from tweet data"""
    if not tweets:
        print("No tweets to visualize")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs("visualizations", exist_ok=True)
    
    # Filter out tweets with missing data and convert types
    valid_tweets = []
    for tweet in tweets:
        if (tweet.get("created_at") and 
            tweet.get("likes") is not None and 
            tweet.get("retweets") is not None and 
            tweet.get("views") is not None):
            valid_tweets.append(tweet)
    
    if not valid_tweets:
        print("No valid tweet data available for visualization")
        return
        
    # Sort tweets by date
    valid_tweets = sorted(valid_tweets, key=lambda x: x["created_at"])
    
    # Prepare data for plotting
    dates = [str(i+1) for i in range(len(valid_tweets))]  # Use sequential numbers instead of dates
    tweet_dates = [tweet["created_at"].split("T")[0] if isinstance(tweet["created_at"], str) else str(tweet["created_at"]) for tweet in valid_tweets]
    likes = [int(tweet["likes"]) if not isinstance(tweet["likes"], int) else tweet["likes"] for tweet in valid_tweets]
    retweets = [int(tweet["retweets"]) if not isinstance(tweet["retweets"], int) else tweet["retweets"] for tweet in valid_tweets]
    views = [int(tweet["views"]) if not isinstance(tweet["views"], int) else tweet["views"] for tweet in valid_tweets]
    
    # Set style
    sns.set(style="whitegrid")
    
    # Plot 1: Engagement metrics comparison
    plt.figure(figsize=(12, 6))
    plt.plot(dates, likes, marker='o', linewidth=2, label='Likes')
    plt.plot(dates, retweets, marker='s', linewidth=2, label='Retweets')
    plt.title(f'Engagement Metrics for @{username}')
    plt.xlabel('Tweet Number')
    plt.ylabel('Count')
    
    # Add a second x-axis with actual dates
    ax2 = plt.twiny()
    ax2.set_xlim(plt.gca().get_xlim())
    ax2.set_xticks(range(len(tweet_dates)))
    ax2.set_xticklabels(tweet_dates, rotation=45, ha='left')
    
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"visualizations/{username}_engagement.png")
    plt.close()
    
    # Plot 2: Views
    plt.figure(figsize=(12, 6))
    plt.bar(dates, views, color='skyblue')
    plt.title(f'Tweet Views for @{username}')
    plt.xlabel('Tweet Number')
    plt.ylabel('Views')
    
    # Add a second x-axis with actual dates
    ax2 = plt.twiny()
    ax2.set_xlim(plt.gca().get_xlim())
    ax2.set_xticks(range(len(tweet_dates)))
    ax2.set_xticklabels(tweet_dates, rotation=45, ha='left')
    
    plt.tight_layout()
    plt.savefig(f"visualizations/{username}_views.png")
    plt.close()
    
    # Plot 3: Engagement rate (likes + retweets / views)
    engagement_rates = [(like + rt) / view if view > 0 else 0 for like, rt, view in zip(likes, retweets, views)]
    plt.figure(figsize=(12, 6))
    plt.bar(dates, engagement_rates, color='lightgreen')
    plt.title(f'Engagement Rate for @{username}')
    plt.xlabel('Tweet Number')
    plt.ylabel('Engagement Rate')
    
    # Add a second x-axis with actual dates
    ax2 = plt.twiny()
    ax2.set_xlim(plt.gca().get_xlim())
    ax2.set_xticks(range(len(tweet_dates)))
    ax2.set_xticklabels(tweet_dates, rotation=45, ha='left')
    
    plt.tight_layout()
    plt.savefig(f"visualizations/{username}_engagement_rate.png")
    plt.close()
    
    print(f"✅ Created visualizations in 'visualizations/{username}_*.png'")

async def main():
    username = "vwakesahu"  # Target user
    count = 10  # Number of tweets to scrape
    
    try:
        # Step 1: Scrape tweets
        print(f"🔍 Scraping {count} tweets from @{username}...")
        tweets = await scrape_tweets(username, count)
        
        # Step 2: Store in MongoDB
        store_in_mongodb(tweets)
        
        # Step 3: Retrieve from MongoDB
        retrieved_tweets = retrieve_from_mongodb(username)
        
        # Step 4: Create visualizations
        create_visualizations(retrieved_tweets, username)
        
        print("✅ Process completed successfully!")
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())