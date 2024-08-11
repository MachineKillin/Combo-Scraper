import requests, re, subprocess, os, urllib3, datetime, threading, cloudscraper, time
from bs4 import BeautifulSoup
from console import utils
from colorama import Fore
from pathvalidate import sanitize_filename

e = datetime.datetime.now()
current_date = e.strftime("%Y-%m-%d-%H-%M-%S")
urllib3.disable_warnings()
agent = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'}
pages = 0
scraped = 0
 
class leech():
    def save(output, thread, host, alr = False):
        global scraped
        if alr == False: filtered = [line.strip() for line in output.split('\n') if re.compile(r'([^\s|]+[@][^\s|]+[.][^\s|]+[:][^\s|]+)').match(line.strip()) and len(line.strip()) <= 64 and line.strip()]
        else: filtered = output
        filtered = [f"{line.split(':')[-2]}:{line.split(':')[-1]}" if line.startswith("http") else line for line in filtered]
        scraped += len(filtered)
        print(Fore.GREEN+f"Scraped [{len(filtered)}] from [{thread}] at [{host}]")
        open(f'combos/scapedcombos-{current_date}.txt', 'a', encoding='utf-8').write('\n'.join(map(str, filtered))+"\n")
    def gofile(link, thread, content_id = None):
        if content_id is not None:
            token = requests.post("https://api.gofile.io/accounts").json()["data"]["token"]
            wt = requests.get("https://gofile.io/dist/js/alljs.js").text.split('wt: "')[1].split('"')[0]
            data = requests.get(f"https://api.gofile.io/contents/{content_id}?wt={wt}&cache=true", headers={"Authorization": "Bearer " + token},).json()
            if data["status"] == "ok":
                if data["data"].get("passwordStatus", "passwordOk") == "passwordOk":
                    dir = os.path.join(link, sanitize_filename(data["data"]["name"]))
                    if data["data"]["type"] == "folder":
                        for children_id in data["data"]["childrenIds"]:
                            if data["data"]["children"][children_id]["type"] == "folder":
                                leech.gofile(dir, thread, content_id=children_id)
                            else:
                                link = data["data"]["children"][children_id]["link"]
                                leech.save(requests.get(link, headers={"Cookie": "accountToken=" + token}).text, thread, "gofile.io")
                    else:
                        link = data["data"]["link"]
                        leech.save(requests.get(link, headers={"Cookie": "accountToken=" + token}).text, thread, "gofile.io")
        else: leech.gofile(link, thread, link.split("/")[-1])
    def handle(link, thread):
        try:
            if link.startswith('https://www.upload.ee/files/'):
                f = BeautifulSoup(requests.get(link, headers=agent).text, 'html.parser')
                download = f.find('a', id='d_l').get('href')
                leech.save(requests.get(download, headers=agent).text, thread, "upload.ee")
            elif link.startswith('https://www.mediafire.com/file/'):
                f = BeautifulSoup(requests.get(link, headers=agent).text, 'html.parser')
                download = f.find('a', id='downloadButton').get('href')
                leech.save(requests.get(download, headers=agent).text, thread, "mediafire.com")
            elif link.startswith('https://pixeldrain.com/u/'):
                leech.save(requests.get(link.replace("/u/", "/api/file/")+"?download", headers=agent).text, thread, "pixeldrain.com")
            elif link.startswith('https://mega.nz/file/'):
                process = subprocess.Popen(f"megatools\\megatools.exe dl {link} --no-ask-password --print-names", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True,)
                output = process.stdout.readlines()
                process.wait()
                saved = output[-1].strip()
                leech.save(open(saved, 'r', encoding='utf-8').read(), thread, "mega.nz")
                os.remove(saved)
            elif link.startswith('https://www.sendspace.com/file/'):
                req = requests.get(link, headers=agent)
                soup = BeautifulSoup(req.text, 'html.parser')
                download_link = soup.find('a', {'id': 'download_button'})
                link = download_link['href']
                leech.save(requests.get(link, verify=False, headers=agent).text, thread, "sendspace.com")
            elif link.startswith('https://gofile.io/d/'):
                leech.gofile(link, thread)
            #else: print(f"Unknown paste site: {link}")
        except: pass
    def heypass():
        dupe = []
        try:
            for page in range(1, pages):
                req = requests.get(f"https://heypass.net/forums/combo-lists.69/page-{page}?order=post_date&direction=desc", headers=agent)
                soup = BeautifulSoup(req.text, 'html.parser')
                target_div = soup.find('div', class_='structItemContainer-group js-threadList')
                if target_div:
                    links = target_div.find_all('a')
                    print(Fore.MAGENTA+f"Found [{len(links)}] posts from heypass.net")
                    for link in links:
                        href = link.get('href')
                        if href and "members" not in href:
                            href = href.strip('latest')
                            if href not in dupe:
                                dupe.append(href)
                                thread = requests.get("https://heypass.net"+href, headers=agent).text
                                s = BeautifulSoup(thread, 'html.parser')
                                allhref = s.find_all('a', href=True)
                                for lin in allhref:
                                    leech.handle(lin['href'], "https://heypass.net"+href)
                else: print(Fore.RED+"Could not get posts from heypass.net")
        except: pass
    def nohide():
        dupe = []
        try:
            scraper = cloudscraper.create_scraper()
            req = scraper.get("https://nohide.space/forums/free-email-pass.3/?order=post_date&direction=desc")
            #open('nohide.txt', 'w', encoding='utf-8').write(req.text)
            soup = BeautifulSoup(req.text, 'html.parser')
            target_div = soup.find('div', class_='structItemContainer-group js-threadList')
            if target_div:
                links = target_div.find_all('a')
                print(Fore.MAGENTA+f"Found [{len(links)}] posts from nohide.space")
                for link in links:
                    href = link.get('href')
                    if href and "/threads/" in href:
                        href = href.strip('latest').rsplit('page-', 1)[0]
                        if href not in dupe:
                            dupe.append(href)
                            s = BeautifulSoup(scraper.get("https://nohide.space"+href, headers=agent).text, 'html.parser')
                            for ele in s.find_all('div', class_='bbWrapper'):
                                link_el = ele.find_all('a', href=True)
                                for url in link_el:
                                    leech.handle(url['href'], "https://nohide.space"+href)
            else: print(Fore.RED+"Could not get posts from nohide.space [Possible CloudFlare Blocking]")
        except Exception as e: print(e)
    def nulled():
        dupe = []
        try:
            for page in range(1, pages):
                req = requests.get(f"https://www.nulled.to/forum/74-combolists/page-{page}?sort_key=start_date", headers=agent)
                soup = BeautifulSoup(req.text, 'html.parser')
                links = soup.find_all('a', class_='topic_title highlight_unread', itemprop='url', id=True)
                print(Fore.MAGENTA+f"Found [{len(links)}] posts from nulled.to")
                for link in links:
                    href = link.get('href')
                    if href not in dupe:
                        dupe.append(href)
                        s = BeautifulSoup(requests.get(href, headers=agent).text, 'html.parser')
                        section_element = s.find('section', id='nulledPost')
                        link_elements = section_element.find_all('a', href=True)
                        for link_el in link_elements:
                            url = link_el['href']
                            if "/gateway.php" not in url:
                                leech.handle(url, href)
        except: pass
    def hellofhackers():
        dupe = []
        try:
            for page in range(1, pages):
                req = requests.get(f"https://hellofhackers.com/forums/combolists.18/page-{page}?order=post_date&direction=desc", headers=agent)
                soup = BeautifulSoup(req.text, 'html.parser')
                target_div = soup.find('div', class_='structItemContainer-group js-threadList')
                if target_div:
                    links = target_div.find_all('a')
                    print(Fore.MAGENTA+f"Found [{len(links)}] posts from hellofhackers.com")
                    for link in links:
                        href = link.get('href')
                        if href and "/threads/" in href:
                            href = href.strip('latest').rsplit('page-', 1)[0]
                            if href not in dupe:
                                dupe.append(href)
                                s = BeautifulSoup(requests.get("https://hellofhackers.com"+href, headers=agent).text, 'html.parser')
                                for ele in s.find_all('div', class_='bbWrapper'):
                                    link_el = ele.find_all('a', href=True)
                                    for url in link_el:
                                        sup = BeautifulSoup(requests.get(url['href'], headers=agent).text, 'html.parser')
                                        external_link_element = sup.find('div', class_='external-link')
                                        if external_link_element:
                                            lk = external_link_element.text.strip()
                                            leech.handle(lk, "https://hellofhackers.com"+href)
                else: print(Fore.RED+"Could not get posts from hellofhackers.com")
        except: pass
    def crackingx():
        dupe = []
        try:
            for page in range(1, pages):
                req = requests.get(f"https://crackingx.com/forums/5/page-{page}?order=post_date&direction=desc", headers=agent)
                soup = BeautifulSoup(req.text, 'html.parser')
                target_div = soup.find('div', class_='structItemContainer-group js-threadList')
                if target_div:
                    links = target_div.find_all('a')
                    print(Fore.MAGENTA+f"Found [{len(links)}] posts from crackingx.com")
                    for link in links:
                        href = link.get('href')
                        if href and "/threads/" in href:
                            href = href.strip('latest').rsplit('page-', 1)[0]
                            if href not in dupe:
                                dupe.append(href)
                                s = BeautifulSoup(requests.get("https://crackingx.com"+href, headers=agent).text, 'html.parser')
                                for ele in s.find_all('div', class_='bbWrapper'):
                                    link_el = ele.find_all('a', href=True)
                                    for url in link_el:
                                        leech.handle(url.get('href'), "https://crackingx.com"+href)
                else: print(Fore.RED+"Could not get posts from crackingx.com")
        except: pass
    def leaksro():
        dupe = []
        try:
            for page in range(1, pages):
                req = requests.get(f"https://www.leaks.ro/forum/308-combolists/page/{page}/?sortby=start_date&sortdirection=desc", headers=agent)
                soup = BeautifulSoup(req.text, 'html.parser')
                target_div = soup.find('ol', class_='ipsDataList')
                if target_div:
                    links = target_div.find_all('a')
                    print(Fore.MAGENTA+f"Found [{len(links)}] posts from leaks.ro")
                    for link in links:
                        href = link.get('href')
                        if href and "/topic/" in href:
                            if href not in dupe:
                                dupe.append(href)
                                s = BeautifulSoup(requests.get(href, headers=agent).text, 'html.parser')
                                links = s.find("div", class_="cPost_contentWrap").find_all("a")
                                for link in links:
                                    leech.handle(link.get("href"), href)
                else: print(Fore.RED+"Could not get posts from leaks.ro")
        except: pass
    def pastefo():
        try:
            for page in range(1, pages):
                req = requests.get(f"https://paste.fo/recent/{page}")
                soup = BeautifulSoup(req.text, 'html.parser')
                tables_without_class = soup.find_all('tr', class_=False)
                for table in tables_without_class:
                    links = table.find_all('a')
                    for link in links:
                        data = re.findall(r'([^\s|]+[@][^\s|]+[.][^\s|]+[:][^\s|]+)', requests.get(f"https://paste.fo/raw{link.get('href')}").text)
                        if len(data) > 0:
                            leech.save(data, f"https://paste.fo{link.get('href')}", "paste.fo", alr=True)
        except Exception as e: print(e)
    def crackingpro():
        try:
            for page in range(1, pages):
                req = requests.get(f"https://www.crackingpro.com/forum/23-combos/page/{page}/", headers=agent)
                soup = BeautifulSoup(req.text, 'html.parser')
                li_elements = soup.find_all('li', class_='ipsType_light')
                hrefs = [li.find('a')['href'] for li in li_elements if li.find('a')]
                print(Fore.MAGENTA+f"Found [{len(hrefs)}] posts from crackingpro.com")
                for href in hrefs:
                    if '/topic/' in href:
                        soup = BeautifulSoup(requests.get(href, headers=agent).text, 'html.parser')
                        div_element = soup.find('div', class_='ipsType_normal ipsType_richText ipsPadding_bottom ipsContained')
                        leech.handle(div_element.find('a')['href'], href)
                else: print(Fore.RED+"Could not get posts from crackingpro.com")
        except: pass
    def combolist():
        try:
            for page in range(1, pages):
                req = requests.get(f"https://www.combolist.xyz/category/combolist-5?page={page}", headers=agent)
                #open('comblist.txt', 'a', encoding='utf-8').write(req.text)
                soup = BeautifulSoup(req.text, 'html.parser')
                read_more_elements = soup.find_all('a', class_='read-more')
                hrefs = [element['href'] for element in read_more_elements]
                print(Fore.MAGENTA+f"Found [{len(hrefs)}] posts from combolist.xyz")
                for href in hrefs:
                    soup = BeautifulSoup(requests.get(href, headers=agent).text, 'html.parser')
                    div_element = soup.find('div', class_='article-content dont-break-out')
                    leech.handle(div_element.find('a')['href'], href)
        except: pass

def title():
    utils.set_title(f"Combo Scraper by KillinMachine | Combos: {scraped}  -  Pages: {pages-1}")
    time.sleep(1)
    threading.Thread(target=title).start()

def start():
    global pages
    utils.set_title(f"Combo Scraper by KillinMachine")
    pages = int(input(Fore.LIGHTGREEN_EX+"Pages to Scrape: "))+1
    if not os.path.exists("combos"): os.makedirs("combos/")
    title()
    functions = [leech.heypass, leech.nohide, leech.nulled, leech.hellofhackers, leech.crackingx, leech.leaksro, leech.pastefo, leech.crackingpro] # leech.combolist
    #functions = [leech.combolist] THIS IS KEPT OUT BECAUSE I THINK THAT SITE IS UPLOADING FAKE LISTS!
    threads = []
    for func in functions:
        thread = threading.Thread(target=func)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    print(Fore.YELLOW+f"Scraped [{scraped}] combos from [{len(functions) * pages}] pages.")
    input()
    exit()

start()