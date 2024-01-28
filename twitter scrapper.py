from selenium import webdriver
import json
import os
import io
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv

def wait_for_element(driver, by, selector):
    return WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((by, selector))
    )

def login(driver, username, password):
    driver.get("https://twitter.com/i/flow/login")
    
    username_input = wait_for_element(driver, By.CSS_SELECTOR, 'input[autocomplete*="user"]')
    username_input.clear()
    username_input.send_keys(username)
    username_input.send_keys(Keys.RETURN)

    password_input = wait_for_element(driver, By.CSS_SELECTOR, 'input[autocomplete*="password"]')
    password_input.clear()
    password_input.send_keys(password)
    password_input.send_keys(Keys.RETURN)

    time.sleep(5) 

def scrape_tweets(driver, limit=2):
    tweets_collected = 0
    collected_tweets = []

    while tweets_collected < limit:
        driver.execute_script("window.scrollBy(0, 500);")  # Scroll by 500 pixels
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='tweetText']"))
        )
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        tweet_elements = soup.select('article[class*="css-175oi2r r-18u37iz r-1udh08x r-i023vh r-1qhn6m8 r-o7ynqc r-6416eg r-1ny4l3l r-1loqt21"]')

        for tweet_element in tweet_elements:
            try:
                tweet_id = tweet_element.select('a[href*="/status/"]')[0]["href"]
                if tweet_id not in (tweet['id'] for tweet in collected_tweets):
                    tweets_collected += 1
                    tweet_text = tweet_element.text
                    tweet_date = tweet_element.select('time')[0]["datetime"]
                    tweet_likes = int(re.search('[0-9]+',(tweet_element.select('div[data-testid*="like"]')[0]["aria-label"])).group())
                    tweet_retweets = int(re.search('[0-9]+',(tweet_element.select('div[data-testid*="retweet"]')[0]["aria-label"])).group())
                    tweet_replies = int(re.search('[0-9]+',(tweet_element.select('div[data-testid*="reply"]')[0]["aria-label"])).group())
                    tweet_data = {
                        'id': tweet_id,
                        'text': tweet_text,
                        'date': tweet_date,
                        'likes': tweet_likes,
                        'retweets': tweet_retweets,
                        'replies': tweet_replies
                    }
                    collected_tweets.append(tweet_data)

                    print(f"ID: {tweet_id}")
                    print(f"Text: {tweet_text}")
                    print(f"Date: {tweet_date}")
                    print(f"Likes: {tweet_likes}")
                    print(f"Retweets: {tweet_retweets}")
                    print(f"Replies: {tweet_replies}\n")
            except Exception as e:
                print(f"Error extracting tweet information: {str(e)}")
        # Save tweets to a JSON file after each scroll
        with io.open('twitter_results.json', 'w', encoding='utf-8') as json_file:
            json.dump(collected_tweets, json_file, ensure_ascii=False, indent=4)
        if tweets_collected == limit:
            break

def collect_replies(driver, tweet_id):
    collected_replies = []
    collected_tweets_ids=set()
    last_height = 0

    while True:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="tweetText"]'))
            )
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            replies = soup.select('article[class*="css-175oi2r r-18u37iz r-1udh08x r-i023vh r-1qhn6m8 r-o7ynqc r-6416eg r-1ny4l3l r-1loqt21"]')

            for reply_element in replies:
                try:
                    reply_id = reply_element.select('a[href*="/status/"]')[0]["href"]
                    reply_id_element = reply_element.find('a', href=True)
                    if reply_id_element:
                        reply_id = reply_id_element['href']
                        if reply_id == tweet_id or reply_id in collected_tweets_ids:
                            continue  # Skip duplicates
                        collected_tweets_ids.add(reply_id)
                        try:
                            reply_text_element = reply_element.select_one('div[class*="css-1rynq56 r-8akbws r-krxsd3 r-dnmrzs r-1udh08x r-bcqeeo r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-bnwqim"]')
                            reply_text = reply_text_element.get_text(separator=' ', strip=True) if reply_text_element else "Reply text not available"
                        except AttributeError as e:
                            reply_text = "Error extracting reply text: " + str(e)
                        reply_date = reply_element.select('time')[0]["datetime"]
                        reply_likes = int(re.search('[0-9]+',(reply_element.select('div[data-testid*="like"]')[0]["aria-label"])).group())
                        reply_retweets = int(re.search('[0-9]+',(reply_element.select('div[data-testid*="retweet"]')[0]["aria-label"])).group())
                        reply_replies = int(re.search('[0-9]+',(reply_element.select('div[data-testid*="reply"]')[0]["aria-label"])).group())
                        reply_data = {
                            'reply id': reply_id,
                            'tweet id': tweet_id,
                            'reply text': reply_text,
                            'reply date': reply_date,
                            'reply_likes': reply_likes,
                            'reply_retweets': reply_retweets,
                            'reply_replies': reply_replies
                        }
                        collected_replies.append(reply_data)
                        print(f"Reply ID: {reply_id}")
                        print(f"Tweet ID: {tweet_id}")
                        print(f"Reply Text: {reply_text}")
                        print(f"Reply Date: {reply_date}")
                        print(f"Reply Likes: {reply_likes}")
                        print(f"Reply Retweets: {reply_retweets}")
                        print(f"Reply Replies: {reply_replies}\n")
                except Exception as e_reply:
                    print(f"Error extracting reply information: {str(e_reply)}")
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("No more replies. Exiting.")
                break

            driver.execute_script("window.scrollBy(0, 500);")  # Scroll by 500 pixels
            time.sleep(2)  # Add a delay to ensure the new replies are loaded
            last_height = new_height
        except Exception as e:
            print(f"Error scrolling or waiting: {str(e)}")
            break
    with io.open('twitter_replies.json', 'a', encoding='utf-8') as json_file:
        json.dump(collected_replies, json_file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    # Get Twitter credentials from environment variables
    twitter_username=os.getenv("TUSERNAME")
    twitter_password=os.getenv("PASSWORD")
    driver=webdriver.Chrome()
    try:
        login(driver, twitter_username, twitter_password)
        driver.get("https://twitter.com/pdo_om")
        scrape_tweets(driver, limit=2)
        with open('twitter_results.json', 'r', encoding='utf-8') as json_file:
            tweets = json.load(json_file)
            for tweet in tweets:
                tweet_id = tweet['id']
                driver.get("https://twitter.com" + tweet_id)
                collect_replies(driver, tweet_id)
    finally:
        driver.quit()
