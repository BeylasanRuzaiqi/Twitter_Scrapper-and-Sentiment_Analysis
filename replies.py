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
from selenium.webdriver.common.action_chains import ActionChains

def wait_for_element(driver, by, selector):
    return WebDriverWait(driver, 30).until(
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

def collect_replies(driver, tweet_id):
    collected_replies = []
    collected_tweets_ids = set()
    last_height = 0

    while True:
        try:
            wait_for_element(driver, By.CSS_SELECTOR, 'div[data-testid="tweetText"]')
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            replies = soup.select('article[class*="css-175oi2r r-18u37iz r-1udh08x r-i023vh r-1qhn6m8 r-o7ynqc r-6416eg r-1ny4l3l r-1loqt21"]')

            for reply_element in replies:
                try:
                    reply_id_element = reply_element.find('a', href=True)
                    if reply_id_element:
                        reply_id = reply_id_element['href']
                        if reply_id == tweet_id or reply_id in collected_tweets_ids:
                            continue
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

            # Click on the "Reload" button if it exists
            reload_button = driver.find_elements(By.CSS_SELECTOR, 'div[class="css-175oi2r r-sdzlij r-1phboty r-rs99b7 r-lrvibr r-2yi16 r-1qi8awa r-ymttw5 r-1loqt21 r-o7ynqc r-6416eg r-1ny4l3l"]')
            if reload_button:
                try:
                    reload_button[0].click()
                    time.sleep(2)
                except Exception as e_reload:
                    print(f"Error clicking 'Reload' button: {str(e_reload)}")

            # Click on the "Show more replies" button if it exists
            show_more_replies_buttons = driver.find_elements(By.CSS_SELECTOR, 'div[class="css-1rynq56 r-bcqeeo r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-5njf8e"]')
            if show_more_replies_buttons:
                for button in show_more_replies_buttons:
                    try:
                        if button.text == "Show more replies":
                            ActionChains(driver).move_to_element(button).click().perform()
                            time.sleep(1)
                    except Exception as e_button:
                        print(f"Error clicking 'Show more replies' button: {str(e_button)}")

            # Click on the "Show" button if it exists
            show_buttons = driver.find_elements(By.CSS_SELECTOR, 'span[class*="css-1qaijid r-dnmrzs r-1udh08x r-3s2u2q r-bcqeeo r-qvutc0 r-poiln3 r-1b43r93 r-1cwl3u0"]')
            if show_buttons:
                for button in show_buttons:
                    try:
                        if button.text == "Show":
                            ActionChains(driver).move_to_element(button).click().perform()
                            time.sleep(1)
                    except Exception as e_button:
                        print(f"Error clicking 'Show' button: {str(e_button)}")

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("No more replies. Exiting.")
                break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            last_height = new_height

        except Exception as e:
            print(f"Error in scraping: {str(e)}")
            break

    with io.open('twitter_replies.json', 'a', encoding='utf-8') as json_file:
        json.dump(collected_replies, json_file, ensure_ascii=False, indent=4)

    return collected_replies

if __name__ == '__main__':
    load_dotenv()
    driver = webdriver.Chrome()
    try:
        login(driver, os.getenv("TUSERNAME"), os.getenv("PASSWORD"))
        # change your file name here to file that contains tweets
        with io.open('twitter_results.json', 'r', encoding='utf-8') as json_file:
            tweets = json.load(json_file)
            tweet_ids = [tweet['id'] for tweet in tweets]
            for tweet in tweets:
                tweet_id = tweet['id']
                driver.get("https://twitter.com" + tweet_id)
                collect_replies(driver, tweet_id)
    finally:
        driver.quit()

# show button = 'span[class*="css-1qaijid r-dnmrzs r-1udh08x r-3s2u2q r-bcqeeo r-qvutc0 r-poiln3 r-1b43r93 r-1cwl3u0"]'
# reload button = 'div[class="css-175oi2r r-sdzlij r-1phboty r-rs99b7 r-lrvibr r-2yi16 r-1qi8awa r-ymttw5 r-1loqt21 r-o7ynqc r-6416eg r-1ny4l3l"]'
# show more replies button = 'div[class="css-1rynq56 r-bcqeeo r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-5njf8e"]'