# -*- coding: utf-8 -*-

#v2.13.0

# Nastavení
# Počet dní (1-15)
days = 3

# Počet dní zpětně (0-7)
days_back = 1

# Výběr zdroje kanálů
# 1 = povolit
# 0 = zakázat
TV_SMS_CZ = 1
T_MOBILE_TV_GO = 1
MAGIO_GO = 1
O2_TV_SPORT = 1
MUJ_TV_PROGRAM_CZ = 1
SLEDOVANITV_CZ = 1
SLEDOVANIETV_SK = 1
TV_SPIEL = 1
OTT_PLAY = 1

# Seznam vlastních kanálů
# Seznam id kanálů oddělené čárkou (např.: "2,3,32,94")
# Pro všechny kanály ponechte prázdné
TV_SMS_CZ_IDS = ""
T_MOBILE_TV_GO_IDS = ""
MAGIO_GO_IDS = ""
O2_TV_IDS = ""
MUJ_TV_PROGRAM_IDS = ""
SLEDOVANI_TV_CZ_IDS = ""
SLEDOVANIE_TV_SK_IDS = ""
TV_SPIEL_IDS = ""
OTT_PLAY_IDS = ""


#Nahrát EPG na ftp server
#Ano = 1
#Ne = 0
ftp_upload = 0
ftp_server = "server.cz"
ftp_port = 21
ftp_login = "login"
ftp_password = "heslo"
ftp_folder = "/"

#Auto aktualizace
#Ano = 1
#Ne = 0
update = 0
#Každých x hodin
interval = 12


import logging
logging.basicConfig(filename='log.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
try:
    import sys
    import os
    import xmltv
    import requests
    import xml.etree.ElementTree as ET
    import unicodedata
    import time
    from urllib.parse import quote
    from datetime import datetime, timedelta, date
    from ftplib import FTP
    import time
    import schedule
    from bs4 import BeautifulSoup
except Exception as ex:
    print(ex)
    logging.error("365 EPG Generator - %s" % ex)
    input("Pro ukončení stiskněte libovolnou klávesu")
    sys.exit(0)


dn = os.path.dirname(os.path.realpath(__file__))
fn = os.path.join(dn,"epg.xml")
custom_names_path = os.path.join(dn,"custom_names.txt")
now = datetime.now()
local_now = now.astimezone()
TS = " " + str(local_now)[-6:].replace(":", "")


def encode(string):
    string = str(unicodedata.normalize('NFKD', string).encode('ascii', 'ignore'), "utf-8")
    return string


custom_names = []
try:
    f = open(custom_names_path, "r", encoding="utf-8").read().splitlines()
    for x in f:
        x = x.split("=")
        custom_names.append((x[0], x[1]))
except:
    pass


def replace_names(value):
    for v in custom_names:
        if v[0] == value:
            value = v[1]
    return value


def get_stvsk_programmes(stv_ids, d, d_b):
    if d_b > 7:
        d_b = 7
    if d > 15:
        d = 15
    channels = []
    programmes = []
    stv_channels = {"markiza": "Markíza", "joj": "JOJ", "jojplus": "JOJ Plus", "doma": "Doma", "joj_sport": "JOJ Šport", "dajto": "Dajto", "rik2": "Rik", "rik": "Jojko", "wau": "WAU", "novaint": "Nova International", "primaplus": "Prima PLUS", "stv4": "RTVS Šport", "tv_osem": "Televizia Osem", "m1": "M1", "m2": "M2", "m4": "M4 Sport", "arcadia": "Arcadia World", "karpaty": "TV Karpaty", "tv_liptov": "TV Liptov", "tv_central": "Central", "tv_lux": "TV Lux", "ruzomberok": "TV Ružomberok"}
    if stv_ids == "":
        stv_id = "".join('{},'.format(k) for k in stv_channels.keys())[:-1]
    else:
        stv_id = stv_ids
    for k, v in stv_channels.items():
        if k in stv_id.split(","):
            channels.append({'display-name': [(replace_names(v), u'cs')], 'id': 'stvsk-' + k,'icon': [{'src': 'https://sledovanietv.sk/cache/biglogos/' + k + '.png'}]})
    now = datetime.now()
    st = 1
    for i in range(d_b*-1, d):
        next_day = now + timedelta(days = i)
        date_from = next_day.strftime("%Y-%m-%d")
        date_ = next_day.strftime("%d.%m.%Y")
        print(date_)
        req = requests.get("http://felixtv.wz.cz/epg/stv_sk.php?ch=" + stv_id + "&d=" + date_from).json()["channels"]
        for k in req.keys():
            for x in req[k]:
                programm = {'channel': "stvsk-" + k, 'start': x["startTime"].replace("-", "").replace(" ", "").replace(":", "") + "00" + TS, 'stop': x["endTime"].replace("-", "").replace(" ", "").replace(":", "") + "00" + TS, 'title': [(x["title"], u'')], 'desc': [(x["description"], u'')]}
                try:
                    icon = x["poster"]
                except:
                    icon = None
                if icon != None:
                    programm['icon'] = [{"src": icon}]
                if programm not in programmes:
                    programmes.append(programm)
        sys.stdout.write('\x1b[1A')
        print(date_ + "  OK")
    print("\n")
    return channels, programmes


def get_stv_programmes(stv_ids, d, d_b):
    if d_b > 7:
        d_b = 7
    if d > 15:
        d = 15
    channels = []
    programmes = []
    stv_channels = {"ct1": "ČT1", "ct2": "ČT2", "ct3": "ČT3", "ct24": "ČT24", "ctdecko": "Déčko", "ctart": "ČT art", "ct4sport": "ČT Sport", "nova": "Nova", "novacinema": "Nova Cinema", "fanda": "Nova Action", "smichov": "Nova Fun", "nova_lady": "Nova Lady", "telka": "Nova Gold", "primafamily": "Prima", "primacool": "Prima COOL", "prima_max": "Prima Max", "primalove": "Prima Love", "prima_krimi": "Prima Krimi", "prima_show": "Prima Show", "prima_star": "Prima Star", "primazoom": "Prima Zoom", "prima_news": "CNN Prima News", "primacomedy": "Paramount Network", "barrandov": "TV Barrandov", "barrandovplus": "Barrandov Krimi", "kinobarrandov": "Kino Barrandov", "Seznam": "Televize Seznam", "pohoda": "Relax", "tvnoe": "TV Noe", "stv1": "Jednotka", "stv2": "Dvojka", "stv3": "Trojka", "markizaint": "Markíza International", "jojfamily": "JOJ Family", "ta3": "TA3", "tv_lux": "TV Lux", "TVlife": "Life TV", "HBO": "HBO", "HBO2": "HBO 2", "hbo_comedy": "HBO 3", "cinemax1": "Cinemax 1", "cinemax2": "Cinemax 2", "jojcinema": "JOJ Cinema", "amc": "AMC", "film_plus": "Film+", "filmbox": "FilmBox", "FilmboxHD": "Filmbox Extra HD", "FilmboxExtra": "FilmBox Premium", "filmboxplus": "Filmbox Stars", "FilmboxFamily": "FilmBox Family", "FilmboxArthouse": "Filmbox Arthouse", "Film_Europe": "Film Europe", "Kino_CS": "Film Europe + HD", "axn": "AXN", "axnwhite": "AXN White", "axnblack": "AXN Black", "cs_film": "CS Film", "horor_film": "CS Horror", "haha_tv": "HaHa TV", "spektrum": "Spektrum", "NGC_HD": "National Geographic HD", "nat_geo_wild": "National Geographic Wild", "animal_planet": "Animal Planet", "Discovery": "Discovery", "Science": "Discovery Science", "world": "Discovery Turbo Xtra", "ID": "Investigation Discovery", "TLC": "Discovery : TLC", "sat_crime_invest": "Crime and Investigation", "history": "History Channel", "viasat_explore": "Viasat Explore", "viasat_history": "Viasat History", "viasat_nature": "Viasat Nature", "love_nature": "Love Nature", "travelxp": "Travelxp", "travelhd": "Travel Channel HD", "fishinghunting": "Fishing&Hunting", "kinosvet": "CS Mystery", "war": "CS History", "tv_paprika": "TV Paprika", "mnamtv": "TV Mňam", "hobby": "Hobby TV", "natura": "TV Natura", "DocuBoxHD": "DocuBox", "FashionboxHD": "FashionBox", "nasatv": "NASA TV", "nasatv_uhd": "NASA TV UHD", "Eurosport": "Eurosport", "Eurosport2": "Eurosport2", "Sport1": "Sport1", "Sport2": "Sport2", "nova_sport": "Nova Sport 1", "nova_sport2": "Nova Sport 2", "slovak_sport": "Arena sport 1", "slovak_sport2": "Arena sport 2", "sport5": "Sport 5", "auto_motor_sport": "Auto Motor Sport", "golf": "Golf Channel", "FightboxHD": "FightBox", "chucktv": "Chuck TV", "Fastnfunbox": "Fast & Fun Box", "lala_tv": "Lala TV", "rik2": "Rik", "Jim_Jam": "Jim Jam", "Nickelodeon": "Nickelodeon", "nicktoons": "Nicktoons", "nickjr": "Nick JR", "nick_jr_en": "Nick JR EN", "Minimax": "Minimax", "Disney_Channel": "Disney Channel", "disney_junior": "Disney Junior", "cartoon_cz": "Cartoon Network CZ", "cartoon_network_hd": "Cartoon Network HD", "cartoon": "Cartoon Network EN", "boomerang": "Boomerang", "baby_tv": "Baby TV", "ockoHD": "Óčko HD", "ocko_starHD": "Óčko STAR HD", "ocko_expresHD": "Óčko EXPRES HD", "ocko_blackHD": "Óčko BLACK HD", "retro": "Retro", "rebel": "Rebel", "mtv": "MTV", "mtv_hits": "MTV Hits", "360TuneBox": "360TuneBox", "deluxe": "Deluxe Music", "lounge": "Lounge TV", "i_concerts": "iConcerts", "mezzo": "Mezzo", "mezzo_live": "Mezzo Live HD", "slagr": "Šláger Originál", "slagr2": "Šláger Muzika", "slagr_premium": "Šláger Premium HD", "ct1sm": "ČT1 SM", "ct1jm": "ČT1 JM", "regiotv": "regionalnitelevize.cz", "rt_jc": "Regionální televize jižní Čechy", "rt_ustecko": "RT Ústecko", "praha": "TV Praha", "brno1": "TV Brno 1", "info_tv_brno": "Info TV Brno a jižní morava", "Polar": "Polar", "slovacko": "TVS", "v1tv": "V1 TV", "plzen_tv": "Plzeň TV", "zaktv": "ZAK TV", "kladno": "Kladno.1 TV", "filmpro": "Filmpro", "rtm_plus_liberec": "RTM+ (Liberecko)", "orf1": "ORF eins", "orf2": "ORF zwei", "cnn": "CNN", "sky_news": "Sky News", "bbc": "BBC World", "france24": "France 24", "france24_fr": "France 24 (FR)", "tv5": "TV5MONDE", "russiatoday": "Russia Today", "rt_doc": "RT Documentary", "uatv": "UA TV", "mnau": "TV Mňau", "zoo_brno_a_vesnice": "Zoo Brno - Africká vesnice", "zoo_brno_m_kamcatsky": "Zoo Brno - Medvěd kamčatský", "zoo_brno_m_ledni": "Zoo Brno - Medvěd lední", "komentovana_krmeni": "Zoo Brno - Komentovaná krmení", "zvirata_v_zoo": "Zoo Brno - Život v zoo", "loop_naturetv-galerie-zvirat": "Galerie zvířat", "loop_naturetv-osetrovani-mladat": "Ošetřování mláďat", "uscenes_cat_cafe": "Kočičí kavárna", "stork_nest": "Čapí hnízdo", "uscenes_hammock_beach": "Pláž", "uscenes_coral_garden": "Korálová zahrada", "loop_naturetv_mumlava_waterfalls": "Mumlavské vodopády", "night_prague": "Noční Praha", "fireplace": "Krb", "eroxHD": "Erox", "eroxxxHD": "Eroxxx", "leo_gold": "Leo TV Gold", "extasy_4k": "Extasy 4K", "radio_cro1": "ČRo Radiožurnál", "radio_cro2": "ČRo Dvojka", "radio_wave": "ČRo Radio Wave", "radio_evropa2": "Evropa 2", "radio_impuls": "Impuls", "radio_frekvence1": "Frekvence 1", "radio_kiss": "Kiss", "radio_fajn": "Fajn Radio", "radio_orlicko": "Rádio Orlicko", "radio_krokodyl": "Krokodýl", "radio_cernahora": "Černá Hora", "radio_signal": "Signál rádio", "radio_spin": "Rádio Spin", "radio_country": "Rádio Country", "radio_beat": "Rádio BEAT", "radio_1": "Rádio 1", "radio_dychovka": "Radio Dychovka", "radio_dechovka": "Radio Dechovka", "radio_slovensko": "Rádio Slovensko", "radio_fm": "Rádio FM", "radio_regina_sk": "Rádio Regina Západ", "radio_expres": "Rádio Expres", "radio_fun": "Rádio Fun", "radio_jemne": "Rádio Jemné", "radio_vlna": "Rádio Vlna", "radio_bestfm": "Rádio Best FM", "radio_kosice": "Rádio Košice", "radio_wow_sk": "Radio WOW", "radio_lumen": "Rádio Lumen", "radio_regina_vy": "Rádia Regina Východ", "radio_devin": "Rádio Devín", "radio_patria": "Rádio Patria", "radio_fit_family": "Fit family rádio", "radio_nonstop": "NON-STOP rádio", "radio_cro3": "ČRo Vltava", "radio_cro6": "ČRo Plus", "radio_jazz": "ČRo Jazz", "radio_junior": "ČRo Junior", "radio_ddur": "ČRo D-Dur", "radio_brno": "ČRo Brno", "radio_praha": "ČRo Radio Praha", "radio_ceskebudejovice": "ČRo České Budějovice", "radio_hk": "ČRo Hradec Králové", "radio_olomouc": "ČRo Olomouc", "radio_ostrava": "ČRo Ostrava", "radio_pardubice": "ČRo Pardubice", "radio_plzen": "ČRo Plzeň", "radio_region": "ČRo Region - Středočeský kraj", "radio_vysocina": "ČRo Region - Vysočina", "radio_sever": "ČRo Sever", "radio_liberec": "ČRo Sever - Liberec", "radio_regina": "ČRo Regina", "radior": "RadioR", "radio_blatna": "Rádio Otava", "radio_proglas": "Proglas", "ivysocina_stream_zs": "i-Vysočina", "tvbeskyd": "TV Beskyd", "cms_tv": "cms:tv", "panorama_tv": "Panorama TV", "jihoceska_televize": "Jihočeská televize", "tik_bohumin": "Tik Bohumín", "DorceltvHD": "Dorcel TV", "DorcelHD": "Dorcel XXX", "playboy": "Playboy TV", "radio_cro_pohoda": "ČRo Pohoda", "radio_jih": "Rádio Jih", "radio_jihlava": "Rádio Jihlava", "radio_free": "Free Rádio", "radio_jukej": "JuKej Radio", "radio_pigy_disko": "PiGy Disko Trysko", "radio_pigy_pisnicky": "PiGy Pohádkové písničky", "radio_pigy_pohadky": "PiGy Pohádky", "radio_z": "Radio Z", "radio_cas": "Radio Čas", "radio_dance": "Dance Rádio", "radio_hit_desitka": "Hitrádio Desítka", "radio_hitradio_80": "Hitradio Osmdesatka", "radio_hitradio_90": "Hitradio Devadesátka", "radio_hitradio_orion": "Hitradio Orion", "radio_blanik": "Rádio Blaník", "radio_rock_radio": "Rock Rádio", "radio_cro_sport": "ČRo Radiožurnál Sport", "radio_cro_zlin": "ČRo Zlín", "radio_cro_kv": "ČRo Karlovy Vary", "radio_color": "Radio Color", "radio_hey": "Radio Hey", "seejay": "SeeJay", "russia_channel1": "Pervij kanal", "dom_kino": "Dom Kino", "dom_kino_premium": "Dom Kino Premium", "vremya": "Vremya", "poehali": "Poekhali!", "muzika_pervogo": "Muzika Pervogo", "bobyor": "Bobyor", "telekanal_o": "O!", "telecafe": "Telecafe", "karousel": "Karusel", "x-mo": "X-mo", "brazzers": "Brazzers TV Europe", "leo": "Leo TV", "extasy": "Extasy", "privatetv": "Private HD", "realitykings": "Reality Kings", "true_amateurs": "True Amateurs", "babes_tv": "Babes TV", "redlight": "Redlight"}
    if stv_ids == "":
        stv_id = "".join('{},'.format(k) for k in stv_channels.keys())[:-1]
    else:
        stv_id = stv_ids
    for k, v in stv_channels.items():
        if k in stv_id.split(","):
            channels.append({'display-name': [(replace_names(v), u'cs')], 'id': 'stv-' + k,'icon': [{'src': 'https://sledovanitv.cz/cache/biglogos/' + k + '.png'}]})
    now = datetime.now()
    for i in range(d_b*-1, d):
        next_day = now + timedelta(days = i)
        date_from = next_day.strftime("%Y-%m-%d")
        date_ = next_day.strftime("%d.%m.%Y")
        print(date_)
        req = requests.get("http://felixtv.wz.cz/epg/stv.php?ch=" + stv_id + "&d=" + date_from).json()["channels"]
        for k in req.keys():
            for x in req[k]:
                programm = {'channel': "stv-" + k, 'start': x["startTime"].replace("-", "").replace(" ", "").replace(":", "") + "00" + TS, 'stop': x["endTime"].replace("-", "").replace(" ", "").replace(":", "") + "00" + TS, 'title': [(x["title"], u'')], 'desc': [(x["description"], u'')]}
                try:
                    icon = x["poster"]
                except:
                    icon = None
                if icon != None:
                    programm['icon'] = [{"src": icon}]
                if programm not in programmes:
                    programmes.append(programm)
        sys.stdout.write('\x1b[1A')
        print(date_ + "  OK")
    print("\n")
    return channels, programmes


def get_ott_play_programmes(ids):
    channels = []
    f = {"7:2777": "fox-tv", "7:2779": "fox-tv", "7:2528": "fox-tv", "ITbas:SuperTennis.it": "korona"}
    ids_ = ids.split(",")
    c = {'display-name': [(replace_names('Penthouse Gold'), u'cs')], 'id': '7:2777','icon': [{'src': 'http://pics.cbilling.pw/streams/penthouse1-hd.png'}]}, {'display-name': [(replace_names('Penthouse Quickies'), u'cs')], 'id': '7:2779','icon': [{'src': 'http://pics.cbilling.pw/streams/penthouse2-hd.png'}]}, {'display-name': [(replace_names('Vivid Red'), u'cs')], 'id': '7:2528','icon': [{'src': 'http://pics.cbilling.pw/streams/vivid-red-hd.png'}]}, {'display-name': [(replace_names('Super Tennis'), u'cs')], 'id': 'ITbas:SuperTennis.it','icon': [{'src': 'https://guidatv.sky.it/logo/5246supertennishd_Light_Fit.png?checksum=13f5cbb1646d848fde3af6fccba8dd4c'}]}
    for x in c:
        if x["id"] in ids_:
            channels.append(x)
    programmes = []
    headers = {"User-Agent": "Mozilla/5.0 (Linux; U; Android 12; cs-cz; Xiaomi 11 Lite 5G NE Build/SKQ1.211006.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/89.0.4389.116 Mobile Safari/537.36 XiaoMi/MiuiBrowser/12.16.3.1-gn", "Host": "epg.ott-play.com", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", "Connection": "keep-alive"}
    for id in ids_:
        r = requests.get("http://epg.ott-play.com/php/show_prog.php?f=" + f[id] + "/epg/" + id + ".json", headers = headers)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find_all('table')[0]
        tr = table.find_all("tr")
        data = []
        for td in tr:
           cols = td.find_all("td")
           cols = [ele.text.strip() for ele in cols]
           data.append([ele for ele in cols if ele])
        for d in data[1:]:
            dat = d[0].split("/")
            dat = dat[2] + dat[1] + dat[0]
            ts = d[1][:5].replace(":", "") + "00"
            te = d[1][6:11].replace(":", "") + "00"
            timestart = dat + ts
            timeend = dat + te
            title = d[2]
            try:
                if "|" in d[3]:
                    descr = d[3].split(" | ")[1][2:]
                else:
                    descr = d[3]
            except:
                descr = ""
            programmes.append({"channel": id, "start": timestart + TS, "stop": timeend + TS, "title": [(title, "")], "desc": [(descr, u'')]})
    print("OK\n")
    return channels, programmes


def get_tv_spiel_programmes(ids, d, d_b):
    ids = ids.split(",")
    if d_b > 7:
        d_b = 7
    if d > 14:
        d = 14
    channels = []
    programmes = []
    ids_ = {'display-name': [(replace_names('Eurosport 1 (DE)'), u'cs')], 'id': 'EURO','icon': [{'src': 'http://live.tvspielfilm.de/static/images/channels/large/EURO.png'}]}, {'display-name': [(replace_names('Eurosport 2 (DE)'), u'cs')], 'id': 'EURO2','icon': [{'src': 'http://live.tvspielfilm.de/static/images/channels/large/EURO2.png'}]}, {'display-name': [(replace_names('Sky Sport 1 (DE)'), u'cs')], 'id': 'HDSPO','icon': [{'src': 'http://live.tvspielfilm.de/static/images/channels/large/HDSPO.png'}]}, {'display-name': [(replace_names('Sky Sport 2 (DE)'), u'cs')], 'id': 'SHD2','icon': [{'src': 'http://live.tvspielfilm.de/static/images/channels/large/SHD2.png'}]}, {'display-name': [(replace_names('Sky Sport Austria1'), u'cs')], 'id': 'SPO-A','icon': [{'src': 'http://live.tvspielfilm.de/static/images/channels/large/SPO-A.png'}]}, {'display-name': [(replace_names('ORF Sport+'), u'cs')], 'id': 'ORFSP','icon': [{'src': 'http://live.tvspielfilm.de/static/images/channels/large/ORFSP.png'}]}
    for x in ids_:
        if x["id"] in ids:
            channels.append(x)
    now = datetime.now()
    for x in range(d_b*-1, d):
        next_day = now + timedelta(days = x)
        date_ = next_day.strftime("%d.%m.%Y")
        date = next_day.strftime("%Y-%m-%d")
        print(date_)
        for y in ids:
            html = requests.get("https://live.tvspielfilm.de/static/broadcast/list/" + y + "/" + date).json()
            for x in html:
                start = time.strftime('%Y%m%d%H%M%S', time.localtime(int(x['timestart'])))
                stop = time.strftime('%Y%m%d%H%M%S', time.localtime(int(x['timeend'])))
                try:
                    desc = x['text']
                except:
                    desc = ""
                programm = {"channel": y, "start": str(start) + TS, "stop": str(stop) + TS, "title": [(x['title'], "")], "desc": [(desc, u'')]}
                try:
                    icon = x["images"][0]["size2"]
                except:
                    icon = None
                if icon != None:
                    programm['icon'] = [{"src": icon}]
                if programm not in programmes:
                    programmes.append(programm)
        sys.stdout.write('\x1b[1A')
        print(date_ + "  OK")
    print("\n")
    return channels, programmes


def get_muj_tv_programmes(ids, d, d_b):
    ids = ids.split(",")
    if d_b > 1:
        d_b = 1
    if d > 10:
        d = 10
    channels = []
    programmes = []
    ids_ = {'723': '723-skylink-7', '233': '233-stingray-classica', '234': '234-stingray-iconcerts', '110': '110-stingray-cmusic', '40': '40-orf1', '41': '41-orf2', '49': '49-rtl', '50': '50-rtl2', '39': '39-polsat', '37': '37-tvp1', '38': '38-tvp2', '174': '174-pro7', '52': '52-sat1', '54': '54-kabel1', '53': '53-vox', '393': '393-zdf', '216': '216-zdf-neo', '46': '46-3sat', '408': '408-sat1-gold', '892': '892-vixen'}
    channels = []
    c = {'display-name': [(replace_names('Skylink 7'), u'cs')], 'id': '723-skylink-7','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=ac6c69625699eaecc9b39f7ea4d69b8c&amp;p2=80'}]}, {'display-name': [(replace_names('Stingray Classica'), u'cs')], 'id': '233-stingray-classica','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=661af53f8f3b997611c29f844c7006fd&amp;p2=80'}]}, {'display-name': [(replace_names('Stingray iConcerts'), u'cs')], 'id': '234-stingray-iconcerts','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=99c87946872c81f46190c77af7cd1d89&amp;p2=80'}]}, {'display-name': [(replace_names('Stingray CMusic'), u'cs')], 'id': '110-stingray-cmusic','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=b323f2ad3200cb938b43bed58dd8fbf9&amp;p2=80'}]}, {'display-name': [(replace_names('ORF1'), u'cs')], 'id': '40-orf1','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=422162d3082a84fc97a7fb9b3ad6823f&amp;p2=80'}]}, {'display-name': [(replace_names('ORF2'), u'cs')], 'id': '41-orf2','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=477dcc38e54309f5db7aec56b62b4cdf&amp;p2=80'}]}, {'display-name': [(replace_names('RTL'), u'cs')], 'id': '49-rtl','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=7cb9005e66956c56fd0671ee79ee2471&amp;p2=80'}]}, {'display-name': [(replace_names('RTL2'), u'cs')], 'id': '50-rtl2','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=418e0d04529ea3aaa2bc2c925ddf5982&amp;p2=80'}]}, {'display-name': [(replace_names('Polsat'), u'cs')], 'id': '39-polsat','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=f54e290782e8352303cfe43ce949d339&amp;p2=80'}]}, {'display-name': [(replace_names('TVP1'), u'cs')], 'id': '37-tvp1','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=770431539d1fa662f705c1c05a0dd943&amp;p2=80'}]}, {'display-name': [(replace_names('TVP2'), u'cs')], 'id': '38-tvp2','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=e2ce4065f27ce199f7613f38878cef72&amp;p2=80'}]}, {'display-name': [(replace_names('Pro7'), u'cs')], 'id': '174-pro7','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=e23a7fb8caff9ff514f254c43a39d9b6&amp;p2=80'}]}, {'display-name': [(replace_names('SAT1'), u'cs')], 'id': '52-sat1','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=97dd916e0164fff141065c3fba71c291&amp;p2=80'}]}, {'display-name': [(replace_names('Kabel1'), u'cs')], 'id': '54-kabel1','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=be6dc88dd3c1c243ba4f28cccb8f1d34&amp;p2=80'}]}, {'display-name': [(replace_names('VOX'), u'cs')], 'id': '53-vox','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=d2c68d2b145a5f2e20e5c05c20a9679e&amp;p2=80'}]}, {'display-name': [(replace_names('ZDF'), u'cs')], 'id': '393-zdf','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=dad48d516fbdb30321564701cc3faa04&amp;p2=80'}]}, {'display-name': [(replace_names('ZDF Neo'), u'cs')], 'id': '216-zdf-neo','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=cd5b8935893b0e4cde41bc3720435f14&amp;p2=80'}]}, {'display-name': [(replace_names('3SAT'), u'cs')], 'id': '46-3sat','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=58d350c6065d9355a52c6dbc3b31b185&amp;p2=80'}]}, {'display-name': [(replace_names('SAT.1 GOLD'), u'cs')], 'id': '408-sat1-gold','icon': [{'src': ''}]}, {'display-name': [(replace_names('Vixen'), u'cs')], 'id': '892-vixen','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=4499ebafb26a915859febcb4306703ca&amp;p2=80'}]}
    for x in c:
        if x["id"].split("-")[0] in ids:
            channels.append(x)
    now = datetime.now()
    for x in range(d_b*-1, d):
        next_day = now + timedelta(days = x)
        date_ = next_day.strftime("%d.%m.%Y")
        print(date_)
        for y in ids:
            html = requests.post("https://services.mujtvprogram.cz/tvprogram2services/services/tvprogrammelist_mobile.php", data = {"channel_cid": y, "day": str(x)}).content
            root = ET.fromstring(html)
            for i in root.iter("programme"):
                programmes.append({"channel": ids_[y],  "start": time.strftime('%Y%m%d%H%M%S', time.localtime(int(i.find("startDateTimeInSec").text))) + TS, "stop": time.strftime('%Y%m%d%H%M%S', time.localtime(int(i.find("endDateTimeInSec").text))) + TS, "title": [(i.find("name").text, "")], "desc": [(i.find("shortDescription").text, "")]})
        sys.stdout.write('\x1b[1A')
        print(date_ + "  OK")
    print("\n")
    return channels, programmes


def get_o2_programmes(o2, d, d_b):
    channelKeys = o2.split(",")
    channels = []
    o2_idd = []
    for x in channelKeys:
        o2_idd.append(x.replace(" HD", "").replace("Eurosport3", "Eurosport 3").replace("Eurosport4", "Eurosport 4").replace("Eurosport5", "Eurosport 5"))
    c = {"display-name": [(replace_names("O2 Sport"), u"cs")], "id": "o2tv-sport", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/o2-sport-hd.png'}]}, {"display-name": [(replace_names("O2 Fotbal"), u"cs")], "id": "o2tv-fotbal", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/o2-tv-fotbal-hd.png'}]}, {"display-name": [(replace_names("O2 Tenis"), u"cs")], "id": "o2tv-tenis", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/o2-tv-tenis-hd.png'}]}, {"display-name": [(replace_names("O2 Sport1"), u"cs")], "id": "o2tv-sport1", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/o2-sport-hd.png'}]}, {"display-name": [(replace_names("O2 Sport2"), u"cs")], "id": "o2tv-sport2", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/o2-sport-hd.png'}]}, {"display-name": [(replace_names("O2 Sport3"), u"cs")], "id": "o2tv-sport3", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/o2-sport-hd.png'}]}, {"display-name": [(replace_names("O2 Sport4"), u"cs")], "id": "o2tv-sport4", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/o2-sport-hd.png'}]}, {"display-name": [(replace_names("O2 Sport5"), u"cs")], "id": "o2tv-sport5", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/o2-sport-hd.png'}]}, {"display-name": [(replace_names("O2 Sport6"), u"cs")], "id": "o2tv-sport6", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/o2-sport-hd.png'}]}, {"display-name": [(replace_names("O2 Sport7"), u"cs")], "id": "o2tv-sport7", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/o2-sport-hd.png'}]}, {"display-name": [(replace_names("O2 Sport8"), u"cs")], "id": "o2tv-sport8", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/o2-sport-hd.png'}]}, {"display-name": [(replace_names("Eurosport 3"), u"cs")], "id": "eurosport-3", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/eurosport-3.png'}]}, {"display-name": [(replace_names("Eurosport 4"), u"cs")], "id": "eurosport-4", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/eurosport-4.png'}]}, {"display-name": [(replace_names("Eurosport 5"), u"cs")], "id": "eurosport-5", "icon": [{"src": 'http://www.o2tv.cz/assets/images/tv-logos/original/eurosport-5.png'}]}
    for x in c:
        if x["display-name"][0][0] in o2_idd:
            channels.append(x)
    params = ""
    for channelKey in channelKeys:
        params = params + ("&channelKey=" + quote(channelKey))
    programmes = []
    for i in range(int(d_b)*-1, int(d)):
        next_day = datetime.combine(date.today(), datetime.min.time()) + timedelta(days = i)
        date_ = next_day.strftime("%d.%m.%Y")
        to_day = next_day  + timedelta(minutes = 1439)
        dt_from = int(time.mktime(next_day.timetuple()))
        dt_to = int(time.mktime(to_day.timetuple()))
        print(date_)
        url = "https://api.o2tv.cz/unity/api/v1/epg/depr/?forceLimit=true&limit=500" + params + "&from=" + str(dt_from*1000) + "&to=" + str(dt_to*1000)
        req = requests.get(url).json()
        for it in req["epg"]["items"]:
            ch_name= it["channel"]["name"].replace(" HD", "").replace(" ", "-").lower()
            for e in it["programs"]:
                name = e["name"]
                start = datetime.fromtimestamp(int(e["start"])/1000).strftime('%Y%m%d%H%M%S')
                stop = datetime.fromtimestamp(int(e["end"])/1000).strftime('%Y%m%d%H%M%S')
                if e["npvr"] == True:
                    req = requests.get("https://api.o2tv.cz/unity/api/v1/programs/" + str(e["epgId"]) + "/").json()
                    try:
                        desc = req["shortDescription"]
                    except:
                        desc = ""
                    programmes.append({"channel": ch_name, "start": start + TS, "stop": stop + TS, "title": [(name, "")], "desc": [(desc, u'')]})
                else:
                    programmes.append({"channel": ch_name, "start": start + TS, "stop": stop + TS, "title": [(name, "")]})
        sys.stdout.write('\x1b[1A')
        print(date_ + "  OK")
    print("\n")
    return channels, programmes


def get_tm_programmes(tm_ids, d, d_b, lng):
    if d > 10:
        d = 10
    if lng == "cz":
        prfx = "tm-"
    else:
        prfx = "mag-"
    tm_ids_list = tm_ids.split(",")
    programmes2 = []
    params={"dsid": "c75536831e9bdc93", "deviceName": "Redmi Note 7", "deviceType": "OTT_ANDROID", "osVersion": "10", "appVersion": "3.7.0", "language": lng.upper()}
    headers={"Host": lng + "go.magio.tv", "authorization": "Bearer", "User-Agent": "okhttp/3.12.12", "content-type":  "application/json", "Connection": "Keep-Alive"}
    req = requests.post("https://" + lng + "go.magio.tv/v2/auth/init", params=params, headers=headers, verify=True).json()
    token = req["token"]["accessToken"]
    headers2={"Host": lng + "go.magio.tv", "authorization": "Bearer " + token, "User-Agent": "okhttp/3.12.12", "content-type":  "application/json"}
    req1 = requests.get("https://" + lng + "go.magio.tv/v2/television/channels?list=LIVE&queryScope=LIVE", headers=headers2).json()["items"]
    channels2 = []
    ids = ""
    tvch = {}
    for y in req1:
        id = str(y["channel"]["channelId"])
        if tm_ids_list == [""]:
            name = y["channel"]["name"]
            logo = str(y["channel"]["logoUrl"])
            ids = ids + "," + id
            tm = str(ids[1:])
            tvch[name] = prfx + id + "-" + encode(name).replace(" HD", "").lower().replace(" ", "-")
            channels2.append(({"display-name": [(replace_names(name.replace(" HD", "")), u"cs")], "id": prfx + id + "-" + encode(name).replace(" HD", "").lower().replace(" ", "-"), "icon": [{"src": logo}]}))
        else:
            if id in tm_ids_list:
                name = y["channel"]["name"]
                logo = str(y["channel"]["logoUrl"])
                ids = ids + "," + id
                tm = str(ids[1:])
                tvch[name] = prfx + id + "-" + encode(name).replace(" HD", "").lower().replace(" ", "-")
                channels2.append(({"display-name": [(name.replace(" HD", ""), u"cs")], "id": prfx + id + "-" + encode(name).replace(" HD", "").lower().replace(" ", "-"), "icon": [{"src": logo}]}))
    tvch["Trojka HD"] = "tm-4516-:24"
    now = datetime.now()
    for i in range(d_b*-1, d):
        next_day = now + timedelta(days = i)
        back_day = (now + timedelta(days = i)) - timedelta(days = 1)
        date_to = next_day.strftime("%Y-%m-%d")
        date_from = back_day.strftime("%Y-%m-%d")
        date_ = next_day.strftime("%d.%m.%Y")
        print(date_)
        req = requests.get("https://" + lng + "go.magio.tv/v2/television/epg?filter=channel.id=in=(" + tm + ");endTime=ge=" + date_from + "T23:00:00.000Z;startTime=le=" + date_to + "T23:59:59.999Z&limit=" + str(len(channels2)) + "&offset=0&lang=" + lng.upper(), headers=headers2).json()["items"]
        for x in range(0, len(req)):
            for y in req[x]["programs"]:
                channel = y["channel"]["name"]
                start_time = y["startTime"].replace("-", "").replace("T", "").replace(":", "")
                stop_time = y["endTime"].replace("-", "").replace("T", "").replace(":", "")
                title = y["program"]["title"]
                desc = y["program"]["description"]
                epi = y["program"]["programValue"]["episodeId"]
                if epi != None:
                    title = title + " (" + epi + ")"
                programm = {'channel': tvch[channel], 'start': start_time + TS, 'stop': stop_time + TS, 'title': [(title, u'')], 'desc': [(desc, u'')]}
                if programm not in programmes2:
                    programmes2.append(programm)
        sys.stdout.write('\x1b[1A')
        print(date_ + "  OK")
    print("\n")
    return channels2, programmes2


class Get_channels_sms:

    def __init__(self):
        self.channels = []
        headers = {"user-agent": "SMSTVP/1.7.3 (242;cs_CZ) ID/ef284441-c1cd-4f9e-8e30-f5d8b1ac170c HW/Redmi Note 7 Android/10 (QKQ1.190910.002)"}
        self.html = requests.get("http://programandroid.365dni.cz/android/v6-tv.php?locale=cs_CZ", headers = headers).text
        self.ch = {}

    def all_channels(self):
        try:
            root = ET.fromstring(self.html)
            for i in root.iter("a"):
                self.ch[i.attrib["id"]] = encode((i.attrib["id"] + "-" + i.find("n").text).replace(" ", "-").lower())
                try:
                    icon = "http://sms.cz/kategorie/televize/bmp/loga/velka/" + i.find("o").text
                except:
                    icon = ""
                self.channels.append({"display-name": [(replace_names(i.find("n").text), u"cs")], "id": encode((i.attrib["id"] + "-" + i.find("n").text).replace(" ", "-").lower()), "icon": [{"src": icon}]})
            self.f.close()
        except:
            pass
        return self.ch, self.channels

    def cz_sk_channels(self):
        try:
            root = ET.fromstring(self.html)
            for i in root.iter("a"):
                if i.find("p").text == "České" or i.find("p").text == "Slovenské":
                    self.ch[i.attrib["id"]] = encode((i.attrib["id"] + "-" + i.find("n").text).replace(" ", "-").lower())
                    try:
                        icon = "http://sms.cz/kategorie/televize/bmp/loga/velka/" + i.find("o").text
                    except:
                        icon = ""
                    self.channels.append({"display-name": [(replace_names(i.find("n").text), u"cs")], "id": encode((i.attrib["id"] + "-" + i.find("n").text).replace(" ", "-").lower()), "icon": [{"src": icon}]})
        except:
            pass
        return self.ch, self.channels

    def own_channels(self, cchc):
        try:
            root = ET.fromstring(self.html)
            cchc = cchc.split(",")
            for i in root.iter("a"):
                if i.attrib["id"] in cchc:
                    self.ch[i.attrib["id"]] = encode((i.attrib["id"] + "-" + i.find("n").text).replace(" ", "-").lower())
                    try:
                        icon = "http://sms.cz/kategorie/televize/bmp/loga/velka/" + i.find("o").text
                    except:
                        icon = ""
                    self.channels.append({"display-name": [(replace_names(i.find("n").text), u"cs")], "id": encode((i.attrib["id"] + "-" + i.find("n").text).replace(" ", "-").lower()), "icon": [{"src": icon}]})
        except:
            pass
        return self.ch, self.channels


class Get_programmes_sms:

    def __init__(self, days_back, days):
        self.programmes_sms = []
        self.days_back = days_back
        self.days = days

    def data_programmes(self, ch):
        if ch != {}:
            chl = ",".join(ch.keys())
            now = datetime.now()
            for i in range(self.days_back*-1, self.days):
                next_day = now + timedelta(days = i)
                date = next_day.strftime("%Y-%m-%d")
                date_ = next_day.strftime("%d.%m.%Y")
                headers = {"user-agent": "SMSTVP/1.7.3 (242;cs_CZ) ID/ef284441-c1cd-4f9e-8e30-f5d8b1ac170c HW/Redmi Note 7 Android/10 (QKQ1.190910.002)"}
                print(date_)
                html = requests.get("http://programandroid.365dni.cz/android/v6-program.php?datum=" + date + "&id_tv=" + chl, headers = headers).text
                root = ET.fromstring(html)
                root[:] = sorted(root, key=lambda child: (child.tag,child.get("o")))
                for i in root.iter("p"):
                    n = i.find("n").text
                    try:
                        k = i.find("k").text
                    except:
                        k = ""
                    if i.attrib["id_tv"] in ch:
                        self.programmes_sms.append({"channel": ch[i.attrib["id_tv"]].replace("804-ct-art", "805-ct-:d"), "start": i.attrib["o"].replace("-", "").replace(":", "").replace(" ", "") + TS, "stop": i.attrib["d"].replace("-", "").replace(":", "").replace(" ", "") + TS, "title": [(n, "")], "desc": [(k, "")]})
                sys.stdout.write('\x1b[1A')
                print(date_ + "  OK")
        print("\n")
        return self.programmes_sms


def main():
    os.system('cls||clear')
    channels = []
    programmes = []
    cchc = ""
    tm_id = ""
    o2_id = ""
    if TV_SMS_CZ == 1:
        try:
            print("TV.SMS.cz kanály")
            print("Stahuji data...")
            g = Get_channels_sms()
            if TV_SMS_CZ_IDS == "":
                ch, channels_sms = g.all_channels()
            else:
                ch, channels_sms = g.own_channels(TV_SMS_CZ_IDS)
            channels.extend(channels_sms)
            gg = Get_programmes_sms(days_back, days)
            programmes_sms = gg.data_programmes(ch)
            programmes.extend(programmes_sms)
        except Exception as ex:
            print("Chyba\n")
            logging.error("TV.SMS.cz kanály - %s" % ex)
    if T_MOBILE_TV_GO == 1:
        try:
            print("T-Mobile TV Go kanály")
            print("Stahuji data...")
            if T_MOBILE_TV_GO_IDS == "":
                tm_id = ""
            else:
                tm_id = T_MOBILE_TV_GO_IDS
            channels_tm, programmes_tm = get_tm_programmes(tm_id, days, days_back, "cz")
            channels.extend(channels_tm)
            programmes.extend(programmes_tm)
        except Exception as ex:
            print("Chyba\n")
            logging.error("T-Mobile TV Go kanály - %s" % ex)
    if MAGIO_GO == 1:
        try:
            print("Magio Go kanály")
            print("Stahuji data...")
            if MAGIO_GO_IDS == "":
                mag_id = ""
            else:
                mag_id = MAGIO_GO_IDS
            channels_mag, programmes_mag = get_tm_programmes(mag_id, days, days_back, "sk")
            channels.extend(channels_mag)
            programmes.extend(programmes_mag)
        except Exception as ex:
            print("Chyba\n")
            logging.error("Magio Go kanály - %s" % ex)
    if O2_TV_SPORT == 1:
        try:
            print("O2 TV Sport kanály")
            print("Stahuji data...")
            if O2_TV_IDS == "":
                o2_id = "O2 Sport HD,O2 Fotbal HD,O2 Tenis HD,O2 Sport1 HD,O2 Sport2 HD,O2 Sport3 HD,O2 Sport4 HD,O2 Sport5 HD,O2 Sport6 HD,O2 Sport7 HD,O2 Sport8 HD,Eurosport3,Eurosport4,Eurosport5"
            else:
                o2_id = O2_TV_IDS
            channels_o2, programmes_o2 = get_o2_programmes(o2_id, days, days_back)
            channels.extend(channels_o2)
            programmes.extend(programmes_o2)
        except Exception as ex:
            print("Chyba\n")
            logging.error("O2 TV Sport kanály - %s" % ex)
    if MUJ_TV_PROGRAM_CZ == 1:
        try:
            print("můjTVprogram.cz kanály")
            print("Stahuji data...")
            if MUJ_TV_PROGRAM_IDS == "":
                mujtv_id = "723,233,234,110,40,41,49,50,39,37,38,174,52,54,53,393,216,46,408,892"
            else:
                mujtv_id = MUJ_TV_PROGRAM_IDS
            channels_mujtv, programmes_mujtv = get_muj_tv_programmes(mujtv_id, days, days_back)
            channels.extend(channels_mujtv)
            programmes.extend(programmes_mujtv)
        except Exception as ex:
            print("Chyba\n")
            logging.error("můjTVprogram.cz kanály - %s" % ex)
    if SLEDOVANITV_CZ == 1:
        try:
            print("SledovaniTV.cz kanály")
            print("Stahuji data...")
            if SLEDOVANI_TV_CZ_IDS == "":
                stv_id = ""
            else:
                stv_id = SLEDOVANI_TV_CZ_IDS
            channels_stv, programmes_stv = get_stv_programmes(stv_id, days, days_back)
            channels.extend(channels_stv)
            programmes.extend(programmes_stv)
        except Exception as ex:
            print("Chyba\n")
            logging.error("SledovaniTV.cz kanály - %s" % ex)
    if SLEDOVANIETV_SK == 1:
        try:
            print("SledovanieTV.sk kanály")
            print("Stahuji data...")
            if SLEDOVANIE_TV_SK_IDS == "":
                stv_id = ""
            else:
                stv_id = SLEDOVANIE_TV_SK_IDS
            channels_stvsk, programmes_stvsk = get_stvsk_programmes(stv_id, days, days_back)
            channels.extend(channels_stvsk)
            programmes.extend(programmes_stvsk)
        except Exception as ex:
            print("Chyba\n")
            logging.error("SledovanieTV.sk kanály - %s" % ex)
    if TV_SPIEL == 1:
        try:
            print("TV Spiel kanály")
            print("Stahuji data...")
            if TV_SPIEL_IDS == "":
                tv_spiel_id = "EURO,EURO2,HDSPO,SHD2,SPO-A,ORFSP"
            else:
                tv_spiel_id = TV_SPIEL_IDS
            channels_tv_spiel, programmes_tv_spiel = get_tv_spiel_programmes(tv_spiel_id, days, days_back)
            channels.extend(channels_tv_spiel)
            programmes.extend(programmes_tv_spiel)
        except Exception as ex:
            print("Chyba\n")
            logging.error("TV Spiel kanály - %s" % ex)
    if OTT_PLAY == 1:
        try:
            print("OTT Play kanály")
            print("Stahuji data...")
            if OTT_PLAY_IDS == "":
                ott_play_id = "7:2777,7:2779,7:2528,ITbas:SuperTennis.it"
            else:
                ott_play_id =OTT_PLAY_IDS
            channels_ott_play, programmes_ott_play = get_ott_play_programmes(ott_play_id)
            channels.extend(channels_ott_play)
            programmes.extend(programmes_ott_play)
        except Exception as ex:
            print("Chyba\n")
            logging.error("OTT Play kanály - %s" % ex)
    if channels != []:
        print("Celkem kanálů: " + str(len(channels)))
        print("Generuji...")
        try:
            w = xmltv.Writer(encoding="utf-8", source_info_url="http://www.funktronics.ca/python-xmltv", source_info_name="Funktronics", generator_info_name="python-xmltv", generator_info_url="http://www.funktronics.ca/python-xmltv")
            for c in channels:
                w.addChannel(c)
            for p in programmes:
                w.addProgramme(p)
            w.write(fn, pretty_print=True)
            sys.stdout.write('\x1b[1A')
            sys.stdout.write('\x1b[2K')
            now = datetime.now()
            dt = now.strftime("%d.%m.%Y %H:%M")
            if update == 1:
                print("Hotovo (" + dt + ")\n\n")
            else:
                print("Hotovo\n\n")
        except Exception as ex:
            sys.stdout.write('\x1b[1A')
            print("Chyba\n")
            logging.error("xmltv.Writer - %s" % ex)
        if ftp_upload == 1:
            try:
                ftp = FTP()
                ftp.set_debuglevel(2)
                ftp.connect(ftp_server, ftp_port)
                ftp.login(ftp_login, ftp_password)
                ftp.cwd(ftp_folder)
                file = open(fn, "rb")
                ftp.storbinary('STOR ' + "epg.xml", file)
                file.close()
                ftp.quit()
            except Exception as ex:
                print("Chyba\n")
                logging.error("FTP - %s" % ex)
        input("Pro ukončení stiskněte libovolnou klávesu")
        sys.exit(0)
    else:
        sys.stdout.write('\x1b[1A')
        sys.stdout.write('\x1b[2K')
        print("Žádné kanály\n\n")


if __name__ == "__main__":
    main()
    try:
        schedule.every(interval).hours.do(main)
        while update:
            schedule.run_pending()
            time.sleep(1)
    except Exception as ex:
        print(ex)
