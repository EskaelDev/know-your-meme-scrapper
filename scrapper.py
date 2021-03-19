import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time


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


HEADERS = {'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36')}

baseurl = "https://knowyourmeme.com"
all_url = baseurl + "/memes/all/page/"

pages_max = 1700  # pages_end shuld be less than this
pages_start = 0
pages_end = 50

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


def get_meme_info(meme_path: str):
    meme_info = []
    r = requests.get(baseurl + meme_path, headers=HEADERS)
    soup = BeautifulSoup(r.text, 'html.parser')
    entries = soup.findAll('div', {'class': 'entry-section'})
    for entry in entries:
        text = entry.getText()
        if text != "":
            meme_info.append(text)
    return meme_info


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
    sleeper = memes_to_sleep

    for i in range(pages_start, pages_end):

        print("\n%sBatch %s out of %s" %
              (bcolors.OKBLUE, i - pages_start + 1, pages_end - pages_start))

        request_url = all_url + str(i)
        print("%sUrl: %s" % (bcolors.OKBLUE, request_url))

        response = requests.get(request_url, headers=HEADERS)
        memes_list = get_memes_list(response)
        memes_url_list = parse_list(memes_list)

        print(bcolors.OKGREEN)
        for meme_url in tqdm(memes_url_list):

            # in case of scraping detection wait 2 sec after few memes
            # sleeper = sleeper - 1
            # if sleeper <= 0:
            #     time.sleep(2)
            #     sleeper = memes_to_sleep

            meme_info = get_meme_info(meme_url)
            info = create_string(meme_info)
            meme_name = meme_url[7:].replace('-', ' ').replace('/', '-')
            save_to_file(meme_name + '.txt', meme_name + info)


main()
