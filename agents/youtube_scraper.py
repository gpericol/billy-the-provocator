from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def setup_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-notifications")
    options.add_argument("--mute-audio")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)

def scroll_to_load_comments(driver, pause=1.5, max_scrolls=15):
    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(2)
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    for _ in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(pause)
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def extract_comments(driver):
    time.sleep(2)
    comment_elements = driver.find_elements(By.ID, 'content-text')
    author_elements = driver.find_elements(By.ID, 'author-text')
    like_elements = driver.find_elements(By.ID, 'vote-count-middle')

    comments = []
    for i in range(min(len(comment_elements), len(author_elements))):
        try:
            comments.append({
                "author": author_elements[i].text.strip(),
                "comment": comment_elements[i].text.strip(),
                "likes": like_elements[i].text.strip() if i < len(like_elements) else "0"
            })
        except Exception:
            continue
    return comments

def get_video_data_from_url(video_url: str, headless=True) -> dict:
    driver = setup_driver(headless)
    driver.get(video_url)
    time.sleep(3)

    # 📌 Titolo
    try:
        title_element = driver.find_element(By.XPATH, '//h1[@class="title style-scope ytd-video-primary-info-renderer"]')
        title = title_element.text.strip()
    except Exception:
        title = driver.title.replace(" - YouTube", "").strip()

    # 💬 Commenti
    scroll_to_load_comments(driver)
    comments = extract_comments(driver)

    driver.quit()

    return {
        "titolo": title,
        "commenti": comments
    }

# Opzionale funzione se vuoi solo i commenti (retrocompatibilità)
def get_comments_from_video(video_url: str, headless=True):
    return get_video_data_from_url(video_url, headless)["commenti"]
