from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
import re

def scrape_youtube_channel(channel_url, max_videos=5):
    # Setup browser with improved options
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    # Initialize webdriver
    driver = webdriver.Chrome(options=options)
    
    try:
        print(f"Opening {channel_url}")
        driver.get(channel_url)
        
        # Accept cookies if prompt appears (common on YouTube)
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Accept all' or contains(text(), 'Accept all')]"))
            ).click()
            print("Accepted cookies")
        except TimeoutException:
            print("No cookie prompt found or already accepted")
        
        # Scroll to load videos
        print("Scrolling to load videos...")
        scroll_pause_time = 2
        for i in range(3):  # Increased scrolls for more content
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            print(f"Scroll {i+1} completed")
            time.sleep(scroll_pause_time)
        
        # Wait for video content to load
        print("Waiting for video elements to load...")
        
        # Try several selectors for YouTube's layout (it changes frequently)
        selectors_to_try = [
            "ytd-rich-grid-media", 
            "ytd-rich-item-renderer",
            "ytd-grid-video-renderer",
            "ytd-video-renderer"
        ]
        
        found_elements = False
        for video_selector in selectors_to_try:
            try:
                print(f"Trying selector: {video_selector}")
                WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, video_selector))
                )
                found_elements = True
                print(f"Success with selector: {video_selector}")
                break
            except TimeoutException:
                print(f"Couldn't find elements with selector: {video_selector}")
        
        if not found_elements:
            print("Failed to find video elements. YouTube may have updated their layout.")
            
            # Last resort - try a very generic selector
            try:
                print("Trying generic approach...")
                # Take screenshot for debugging
                driver.save_screenshot("youtube_debug.png")
                print("Screenshot saved as youtube_debug.png")
                
                # Try to find any elements that might contain video info
                video_selector = "div"
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/watch?v=']"))
                )
                found_elements = True
            except TimeoutException:
                print("All attempts failed. YouTube has likely changed their layout significantly.")
                return pd.DataFrame()
        
        # Find all video elements - use a more comprehensive approach
        if found_elements:
            if video_selector == "div":
                # If we're using the generic approach
                video_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/watch?v=']")
                print(f"Found {len(video_elements)} video links with generic selector")
            else:
                video_elements = driver.find_elements(By.TAG_NAME, video_selector)
                print(f"Found {len(video_elements)} video elements with {video_selector}")
        
        # Extract data
        data = []
        for i, video_container in enumerate(video_elements[:max_videos]):
            try:
                # Find title and link within the container - using CSS selector to be more specific
                title_element = video_container.find_element(By.CSS_SELECTOR, "a#video-title-link, a#video-title")
                title = title_element.get_attribute("title") or title_element.text
                url = title_element.get_attribute("href")
                
                # Debug info
                print(f"Title element found: {title_element.tag_name}, Text: {title_element.text}")
                
                # Find metadata - specifically look for views
                try:
                    # Get all metadata spans and check their contents
                    metadata_spans = video_container.find_elements(By.CSS_SELECTOR, "#metadata-line span, yt-formatted-string.style-scope.ytd-video-meta-block")
                    views_text = ""
                    
                    # Look for text that contains "views"
                    for span in metadata_spans:
                        span_text = span.text
                        if "view" in span_text.lower():
                            views_text = span_text
                            break
                    
                    # If we couldn't find a span with "views", take the first one as fallback
                    if not views_text and metadata_spans:
                        views_text = metadata_spans[0].text
                    
                    views = views_text if views_text else "N/A"
                except Exception as e:
                    print(f"Error extracting views: {e}")
                    views = "N/A"
                
                data.append({
                    "title": title,
                    "url": url,
                    "views": views
                })
                print(f"Scraped video {i+1}: {title}, Views: {views}")
            except Exception as e:
                print(f"Error scraping video {i+1}: {e}")
                continue
        
        # Create DataFrame with explicit column order
        df = pd.DataFrame(data)
        # Make sure we have the correct columns in the right order
        if not df.empty:
            df = df[["title", "url", "views"]]
        
        return df
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()
        
    finally:
        driver.quit()
        print("Browser closed")

if __name__ == "__main__":
    # Use the modern YouTube channel URL format (the /c/ format is deprecated)
    channel_url = "https://www.youtube.com/@Google/videos"
    
    # Uncomment this if you want to try the older URL format
    # channel_url = "https://www.youtube.com/c/Google/videos"
    
    df = scrape_youtube_channel(channel_url, max_videos=5)
    
    if not df.empty:
        print("\nScraped Videos:")
        print(df)
        
        # Save to CSV (optional)
        df.to_csv("youtube_videos.csv", index=False)
        print("Data saved to youtube_videos.csv")
    else:
        print("No data was scraped")