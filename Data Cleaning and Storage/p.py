import asyncio
import json
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from twikit import Client

# Set style for visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

async def scrape_and_visualize_data(usernames):
    client = Client()

    await client.login(
        auth_info_1="meowdev88",
        auth_info_2="gauradashari@gmail.com",
        password="meowdev03"
    )

    all_users_data = {}
    all_tweets_df = pd.DataFrame()

    # Scrape data for each username
    for username in usernames:
        try:
            print(f"Fetching data for user: {username}")
            user = await client.get_user_by_screen_name(username)
            tweets = await user.get_tweets("Tweets", count=20)
            
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
                }
                data.append(tweet_data)
            
            all_users_data[username] = data
            
            # Save individual user data
            with open(f"{username}_tweets.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Saved {len(data)} tweets to {username}_tweets.json")
            
            # Convert to DataFrame and append
            user_df = pd.DataFrame(data)
            all_tweets_df = pd.concat([all_tweets_df, user_df])
        
        except Exception as e:
            print(f"Error fetching data for {username}: {e}")
    
    # Save combined data
    with open("all_twitter_data.json", "w", encoding="utf-8") as f:
        json.dump(all_users_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved combined data for {len(all_users_data)} users to all_twitter_data.json")
    
    # Create visualizations
    create_visualizations(all_tweets_df, all_users_data)
    
    return all_users_data

def create_visualizations(df, all_users_data):
    if df.empty:
        print("No data available for visualization.")
        return
    
    # Try to convert created_at to datetime with error handling
    try:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    except Exception as e:
        print(f"Warning: Could not convert created_at to datetime: {e}")
        # Create a dummy date column if conversion fails
        df['created_at'] = pd.to_datetime('today')
    
    # Ensure numeric types for metrics columns
    metrics = ['likes', 'retweets', 'replies', 'quotes', 'bookmarks', 'views']
    
    for metric in metrics:
        try:
            df[metric] = pd.to_numeric(df[metric], errors='coerce')
        except Exception as e:
            print(f"Warning: Could not convert {metric} to numeric: {e}")
            df[metric] = 0
    
    # Now create visualizations with the cleaned data
    
    # 1. Engagement metrics comparison across users
    plt.figure(figsize=(14, 10))
    
    # Calculate average metrics per user with error handling
    avg_metrics_list = []
    
    for username in df['username'].unique():
        user_metrics = {'username': username}
        user_df = df[df['username'] == username]
        
        for metric in metrics:
            try:
                user_metrics[metric] = user_df[metric].mean()
            except Exception:
                user_metrics[metric] = 0
        
        avg_metrics_list.append(user_metrics)
    
    avg_metrics = pd.DataFrame(avg_metrics_list)
    
    # Create subplots for each metric
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    for i, metric in enumerate(metrics):
        try:
            sns.barplot(x='username', y=metric, data=avg_metrics, ax=axes[i], palette='viridis')
            axes[i].set_title(f'Average {metric.capitalize()} per Tweet')
            axes[i].set_xlabel('Username')
            axes[i].set_ylabel(metric.capitalize())
            axes[i].tick_params(axis='x', rotation=45)
        except Exception as e:
            print(f"Warning: Could not create barplot for {metric}: {e}")
            axes[i].text(0.5, 0.5, f"Could not visualize {metric}", 
                      horizontalalignment='center', verticalalignment='center')
    
    plt.tight_layout()
    plt.savefig('user_engagement_comparison.png')
    print("✅ Saved user engagement comparison chart to user_engagement_comparison.png")

    # 2. Total engagement metrics per user (pie chart)
    try:
        plt.figure(figsize=(12, 12))
        total_engagement = df.groupby('username')['likes', 'retweets', 'replies'].sum()
        total_engagement_per_user = total_engagement.sum(axis=1)
        
        if total_engagement_per_user.sum() > 0:
            plt.pie(total_engagement_per_user, labels=total_engagement_per_user.index, autopct='%1.1f%%', 
                    shadow=True, startangle=90, colors=sns.color_palette('viridis', len(total_engagement_per_user)))
            plt.axis('equal')
            plt.title('Total Engagement Share by User (Likes + Retweets + Replies)')
            plt.savefig('total_engagement_share.png')
            print("✅ Saved total engagement share chart to total_engagement_share.png")
        else:
            print("Warning: No valid engagement data for pie chart")
    except Exception as e:
        print(f"Warning: Could not create pie chart: {e}")

    # 3. Timeline of likes for each user
    try:
        plt.figure(figsize=(14, 8))
        for username in df['username'].unique():
            user_df = df[df['username'] == username].sort_values('created_at')
            if not user_df.empty and not user_df['created_at'].isna().all():
                plt.plot(user_df['created_at'], user_df['likes'], 'o-', label=username)
        
        plt.title('Likes Timeline by User')
        plt.xlabel('Tweet Date')
        plt.ylabel('Number of Likes')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('likes_timeline.png')
        print("✅ Saved likes timeline chart to likes_timeline.png")
    except Exception as e:
        print(f"Warning: Could not create likes timeline: {e}")

    # 4. Views vs Engagement scatter plot
    try:
        plt.figure(figsize=(14, 8))
        
        # Ensure views are not zero to avoid division by zero
        df['views_safe'] = df['views'].replace(0, np.nan)
        df['engagement_ratio'] = (df['likes'] + df['retweets'] + df['replies']) / df['views_safe']
        
        scatter = sns.scatterplot(x='views', y='likes', 
                                hue='username', size='retweets',
                                sizes=(50, 400), data=df, alpha=0.7)
        
        plt.title('Views vs Likes Relationship (Size = Retweets)')
        plt.xlabel('Views')
        plt.ylabel('Likes')
        plt.grid(True)
        plt.savefig('views_vs_likes.png')
        print("✅ Saved views vs likes scatter plot to views_vs_likes.png")
    except Exception as e:
        print(f"Warning: Could not create scatter plot: {e}")
    
    # 5. Correlation heatmap of metrics
    try:
        plt.figure(figsize=(10, 8))
        correlation = df[metrics].corr()
        sns.heatmap(correlation, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
        plt.title('Correlation Between Engagement Metrics')
        plt.tight_layout()
        plt.savefig('metrics_correlation.png')
        print("✅ Saved metrics correlation heatmap to metrics_correlation.png")
    except Exception as e:
        print(f"Warning: Could not create correlation heatmap: {e}")
        
    # 6. Engagement distribution by user (boxplot)
    try:
        plt.figure(figsize=(16, 10))
        metrics_to_plot = ['likes', 'retweets', 'replies']
        
        for i, metric in enumerate(metrics_to_plot):
            plt.subplot(1, 3, i+1)
            sns.boxplot(x='username', y=metric, data=df, palette='viridis')
            plt.title(f'{metric.capitalize()} Distribution')
            plt.xticks(rotation=45)
            
        plt.tight_layout()
        plt.savefig('engagement_distribution.png')
        print("✅ Saved engagement distribution boxplot to engagement_distribution.png")
    except Exception as e:
        print(f"Warning: Could not create boxplot: {e}")

def load_and_visualize_from_json(json_file="all_twitter_data.json"):
    """Load data from existing JSON file and create visualizations"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            all_users_data = json.load(f)
        
        # Convert to DataFrame
        all_tweets = []
        for username, tweets in all_users_data.items():
            for tweet in tweets:
                tweet['username'] = username
                all_tweets.append(tweet)
        
        df = pd.DataFrame(all_tweets)
        
        # Create visualizations
        create_visualizations(df, all_users_data)
        
        return True
    except Exception as e:
        print(f"Error loading and visualizing from JSON: {e}")
        return False

async def main():
    # List of users to scrape
    usernames = ["vwakesahu", "elonmusk", "BillGates", "sundarpichai"]
    
    # Option 1: Scrape new data and visualize
    print("Option 1: Scraping new data and creating visualizations...")
    all_user_data = await scrape_and_visualize_data(usernames)
    
    # Option 2: If you already have the JSON files and just want to visualize
    # Uncomment the following lines to use this option
    # print("Option 2: Loading existing data and creating visualizations...")
    # load_and_visualize_from_json("all_twitter_data.json")
    
    print("Data collection and visualization complete!")

if __name__ == "__main__":
    asyncio.run(main())