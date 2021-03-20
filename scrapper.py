import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import time
from pathlib import Path


class bcolors:
    DEFAULT = "\033[39m"
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Meme:
    def __init__(self, title, content, image, status, details, year, category):
        self.title = title
        self.content = content
        self.image = image
        self.status = status
        self.details = details
        self.year = year
        self.category = category


HEADERS = {'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.91 Safari/537.36'),
           'Accept-Language': 'en-US',
           'Accept-Encoding': 'br, gzip, deflate',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
           'Referer': 'http://www.google.com/',
           'Connection': 'keep-alive',
           'Cookie': '_y=2c150114-87C7-40B7-CBD5-92DFCB4A6117; _shopify_y=2c150114-87C7-40B7-CBD5-92DFCB4A6117; _s=4eced5ef-AC62-451A-B82E-1B6F7EC24B82; _shopify_s=4eced5ef-AC62-451A-B82E-1B6F7EC24B82'}

baseurl = "https://knowyourmeme.com"
all_url = baseurl + "/memes/all/page/"

pages_max = 1700  # pages_end shuld be less than this
pages_start = 500
pages_end = 1583 # 117 batches
timeout = 10  # in seconds
sleep_value = 1

ignored_section = "Search Interest"
memes_to_sleep = 10


def get_memes_list(response: str):
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.findAll(class_='entry_list')


def parse_list(memes_list):
    memes_path = []
    for meme in memes_list:
        meme_paths = meme.findAll('a', href=True)
        for meme_path in meme_paths:
            meme_path['href'].replace(
                '-', ' '), 'https://knowyourmeme.com%s' % meme_path
            meme_name = meme_path['href'].replace('-', ' ')
            href_path = meme_path['href']
            # memes_path.append(meme_name, meme_path)
            if href_path.startswith('/memes/'):
                memes_path.append(meme_path['href'])
    return memes_path


def get_meme_data(meme_path: str):
    r = requests.get(baseurl + meme_path, headers=HEADERS, timeout=timeout)
    soup = BeautifulSoup(r.text, 'html.parser')

    content = extract_content(soup)
    content = create_string(content)
    image = extract_image(soup)
    title = extract_title(soup)
    status, details, year, category = extract_details(soup)

    meme = Meme(trim(title),
                content,
                trim(image),
                trim(status),
                trim(details),
                trim(year),
                trim(category))
    return meme


def trim(text: str):
    return text.replace('\n', ' ').replace('\r', '').replace(' ', '')


def extract_content(soup: BeautifulSoup):
    meme_info = []
    entries = soup.findAll('div', {'class': 'entry-section'})
    for entry in entries:
        text = entry.getText()
        if text != "":
            meme_info.append(text)
    return meme_info


def extract_metadata(soup: BeautifulSoup):
    meme_metadata = []
    entries = soup.findAll('div', {'class': 'photo-wrapper'})
    for entry in entries:
        text = entry.getText()
        if text != "":
            meme_metadata.append(text)
    return meme_metadata


def extract_image(soup: BeautifulSoup):
    entry = soup.find('div', {'class': 'photo-wrapper'})
    return entry.next.next.next["data-src"]


def extract_title(soup: BeautifulSoup):
    entry = soup.find('section', class_="info wide")
    if entry is None:
        entry = soup.find('section', class_="info")
    return entry.find("h1").text


def extract_details(soup: BeautifulSoup):
    entry = soup.findAll('div', class_="detail")

    status = 'Undefined'
    details = 'Undefined'
    year = 1970
    category = 'Undefined'

    filtered = list(filter(lambda entry: entry.next.next.text == "Status:", entry))
    status = filtered[0].next.next.next.next.next.text if len(filtered) != 0 else status;

    filtered = list(filter(lambda entry: entry.next.next.text == "Origin:", entry))
    details = filtered[0].next.next.next.next.next.text if len(filtered) != 0 else details;

    filtered = list(filter(lambda entry: entry.next.next.text == "Year:", entry))
    if len(filtered) != 0:
        year_to_check = filtered[0].next.next.next.next.next.text
        year = year_to_check if year_to_check.find("unknown") == -1 else year
    
    filtered = list(filter(lambda entry: entry.next.next.text == "Type:", entry))
    category = filtered[0].next.next.next.next.next.text if len(filtered) != 0 else category;

    return status, details, year, category


def create_string(meme_info):
    result = ""
    for info in meme_info:
        if ignored_section in info:
            return result
        result = result + "\n" + info
    return result


def save_to_file(file_name: str, content: str):
    with open("memes/" + file_name, 'w') as f:
        f.write(content)


def main():
    Path("memes").mkdir(parents=True, exist_ok=True)
    # sleeper = memes_to_sleep

    # in case of scraping detection wait 2 sec after few memes
    # sleeper = sleeper - 1
    # if sleeper <= 0:
    # sleeper = memes_to_sleep

    for i in range(pages_end, pages_start, -1):

        print(
            f'\n🔽{bcolors.OKBLUE}Batch {i - pages_start + 1} out of {pages_end - pages_start}')

        request_url = all_url + str(i)
        print(f'{bcolors.OKBLUE}Url: {request_url}')

        response = requests.get(request_url, headers=HEADERS, timeout=timeout)
        memes_list = get_memes_list(response)
        memes_url_list = parse_list(memes_list)
        del memes_url_list[::2]
        print(bcolors.OKGREEN)
        for meme_url in tqdm(memes_url_list):

            try:
                meme = get_meme_data(meme_url)
                meme_json = json.dumps(meme.__dict__)

                meme_name = meme_url[7:].replace('-', ' ').replace('/', '-')
                save_to_file(meme_name + '.json', meme_json)

            except Exception as e:
                print(f'{bcolors.FAIL}❌ TimedOut : MemeUrl: {meme_url}')
                print(e)
                print(bcolors.OKGREEN)

        print(f'{bcolors.OKBLUE}💤Going for a {sleep_value}sec sleep')
        time.sleep(sleep_value)


main()
