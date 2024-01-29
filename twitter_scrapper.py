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
from dotenv import load_dotenv

def wait_for_element(driver, by, selector):
    return WebDriverWait(driver, 40).until(
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

def scrape_tweets(driver):
    tweets_collected = 0
    collected_tweets = []

    while True:
        driver.execute_script("window.scrollBy(0, 500);")  # Scroll by 500 pixels
        # reload_button_css_selector = "div.css-175oi2r.r-sdzlij.r-1phboty.r-rs99b7.r-lrvibr.r-2yi16.r-1qi8awa.r-ymttw5.r-1loqt21.r-o7ynqc.r-6416eg.r-1ny4l3l"
        # reload_button = WebDriverWait(driver, 40).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, reload_button_css_selector))
        # )

        # # Click the "reload" button
        # reload_button.click()
        WebDriverWait(driver, 40).until(
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
            if tweets_collected >= 6000:
                print("Tweet limit reached. Exiting.")
                break
        # Save tweets to a JSON file after each scroll
        with io.open('twitter_results.json', 'w', encoding='utf-8') as json_file:
            json.dump(collected_tweets, json_file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    # Get Twitter credentials from environment variables
    twitter_username=os.getenv("TUSERNAME")
    twitter_password=os.getenv("PASSWORD")
    driver = webdriver.Chrome()
    try:
        login(driver, twitter_username, twitter_password)
        driver.get("https://twitter.com/pdo_om")
        scrape_tweets(driver)
    finally:
        driver.quit()
