import sys, os, requests, re, json, urllib.request, urllib.error, hashlib, hmac, traceback, logging, shutil
from pytablewriter import MarkdownTableWriter

# key for tdmb link generation (from ps3, ps4)
tmdb_key = bytearray.fromhex('F5DE66D2680E255B2DF79E74F890EBF349262F618BCAE2A9ACCDEE5156CE8DF2CDF2D48C71173CDC2594465B87405D197CF1AED3B7E9671EEB56CA6753C2E6B0')

title_ids = []
ps5_game_names = []
ps5_title_ids = []

print('checking games.txt for custom titles...')
with open('games.txt', 'r') as game_reader:
    for line in game_reader.readlines():
        line = line.strip()

        if line.startswith('#'):
            continue
        
        line = line.split('#', 1)[0].strip()
        title_ids.append(line)

print(f'added {len(title_ids)} games from games.txt')

print('checking games_ps5.txt for custom titles...')
with open('games_ps5.txt', 'r') as ps5_game_reader:
    for line in ps5_game_reader.readlines():
        line = line.strip()

        if line.startswith('#'):
            continue
        
        title_id = line.split('#')[0].strip()
        name = line.split('#')[1].strip()
        ps5_game_names.append(name)
        ps5_title_ids.append(title_id)

print(f'added {len(ps5_title_ids)} games from games_ps5.txt')

image_dir = 'ps4'

def create_url(title_id):
    hash = hmac.new(tmdb_key, bytes(title_id, 'utf-8'), hashlib.sha1)
    return f'https://tmdb.np.dl.playstation.net/tmdb2/{title_id}_{hash.hexdigest().upper()}/{title_id}.json'


if __name__ == '__main__':
    log = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
    handler.setLevel(logging.INFO)
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    discord_title_ids = []

    done = {"ps4": []}
    table_writer = None
    ps5_table_writer = None

    if os.path.isfile('README.template'):
        table_writer = MarkdownTableWriter()
        table_writer.headers = ["Icon", "Title"]
        table_writer.value_matrix = []
        ps5_table_writer = MarkdownTableWriter()
        ps5_table_writer.headers = ["Icon", "Title"]
        ps5_table_writer.value_matrix = []
    else:
         print('missing README.template. wont update README.md file.')

    if os.path.exists(image_dir):
        shutil.rmtree(image_dir)

    # added all the titleIds... now get their images
    for title_id in title_ids:
        url = create_url(title_id)
        print(url)
        content = requests.get(url)

        if content.status_code != 200:
            print('skipping', title_id)
            continue
        
        try:
            content = content.json()
        except ValueError:
            # Sometimes the json for a game can be empty for some reason. Just remove it from the list.
            title_ids.remove(title_id)
            print('removed')
            continue
        
        game_name = content['names'][0]['name']
        
        print(game_name)

        if not content['icons'] or len(content['icons']) == 0:
            print('\tno icons')
            continue

        game_icon = None

        for icon in content['icons']:
            if icon['type'] == '512x512':
                game_icon = icon['icon']
                break
        
        if game_icon == None:
            print('\tno 512x512 icon')
            continue

        done["ps4"].append({
            "name": game_name,
            "titleId": title_id
        })

        discord_title_ids.append(title_id.lower())

        if not os.path.exists(image_dir):
            os.mkdir(image_dir)

        icon_file = f'{image_dir}/{title_id}.png'

        if table_writer != None:
            table_writer.value_matrix.append([
                f'<img src="{icon_file}?raw=true" width="100" height="100">',
                game_name
            ])

        if os.path.exists(icon_file):
            print('\ticon file exists')
            continue

        urllib.request.urlretrieve(game_icon, icon_file)
        
        print('\tsaved')

    # don't know how to get images for PS5 games, so will need to use preuploaded file
    for index, title_id in enumerate(ps5_title_ids):
        game_name = ps5_game_names[index]
        done["ps4"].append({
            "name": game_name,
            "titleId": title_id
        })

        discord_title_ids.append(title_id.lower())

        icon_file = f'ps5/{title_id}.jpg'

        if ps5_table_writer != None:
            ps5_table_writer.value_matrix.append([
                f'<img src="{icon_file}?raw=true" width="100" height="100">',
                game_name
            ])
    
    with open("README.template", "rt") as template:
        with open('README.md', 'wt', encoding='utf-8') as readme:
            for line in template:
                readme.write(line.replace('!!games!!', table_writer.dumps()).replace('!!PS5games!!', ps5_table_writer.dumps()))
    
    with open('games.json', 'w') as games_file:
       json.dump(done, games_file)