import bs4, lxml
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

params = {
    'name': '',
    'platform': ''
}

proxies = {
  'http': 'http://localhost:15236',
  'https': 'http://localhost:15236',
}

async def get_r6_stats(ubi_name):
    #查询模块
    params['name'] = ubi_name
    url = 'https://r6.tracker.network/r6/search'
    try:
        res = requests.get(url=url,params=params,headers=headers)
    except:
        try:
            res = requests.get(url=url,params=params,headers=headers,proxies=proxies)
        except:
            return "啊实在上不去r6 tracker network了呢"
    #如果用户存在
    if res.status_code == 200:
        url = 'https://r6.tracker.network/profile/pc/' + ubi_name
        try:
            res = requests.get(url=url,params=params,headers=headers)
        except:
            try:
                res = requests.get(url=url,params=params,headers=headers,proxies=proxies)
            except:
                return "啊实在上不去r6 tracker network了呢"
        #HTML解码
        decoded = bs4.BeautifulSoup(res.text,'lxml')
        message = f"{ubi_name}的概览数据:\n"
        PVPKDRatio = str(decoded.select("div[data-stat = 'PVPKDRatio']")[0].string).strip('\n').strip(' ').replace(',','')
        PVPDeaths = str(decoded.select("div[data-stat = 'PVPDeaths']")[0].string).strip('\n').strip(' ').replace(',','')
        PVPMatchesWon = str(decoded.select("div[data-stat = 'PVPMatchesWon']")[0].string).strip('\n').strip(' ').replace(',','')
        PVPMatchesLost = str(decoded.select("div[data-stat = 'PVPMatchesLost']")[0].string).strip('\n').strip(' ').replace(',','')
        PVPWLRatio = str(decoded.select("div[data-stat = 'PVPWLRatio']")[0].string).strip('\n').strip(' ').replace(',','')
        PVPTimePlayed = str(decoded.select("div[data-stat = 'PVPTimePlayed']")[0].string).strip('\n').strip(' ').replace(',','')
        PVPMatchesPlayed = str(decoded.select('div[data-stat = \"PVPMatchesPlayed\"]')[0].string).strip('\n').strip(' ').replace(',','')
        PVPAccuracy = str(decoded.select("div[data-stat = 'PVPAccuracy']")[0].string).strip("\n").replace(",","")
        PVPHeadshots = str(decoded.select("div[data-stat = 'PVPHeadshots']")[0].string).strip("\n").replace(",","")
        if decoded.select("div[class = 'trn-defstat__data']")[0].select("div[class = 'trn-defstat__name']")[0].string == 'Level':
            PVPLevel = str(decoded.select("div[class = 'trn-defstat__value-stylized']")[0].string).strip('\n').strip(' ').replace(',','')
        else:
            PVPLevel = str(decoded.select("div[class = 'trn-defstat__value-stylized']")[1].string).strip('\n').strip(' ').replace(',','')
        PVPTotalXp = str(decoded.select("div[data-stat = 'PVPTotalXp']")[0].string).strip("\n").replace(",","")
        season_name = decoded.select("h2[class = 'trn-card__header-title']")[3].string
        season_ranked_MMR = decoded.select("div[class = 'r6-season__info']")[0].select("tspan")[1].string
        season_unrank_MMR = decoded.select("div[class = 'r6-season__info']")[1].select("tspan")[1].string
        message += f"KD: {PVPKDRatio}\n"
        message += f"总死亡次数: {PVPDeaths}\n"
        message += f"总获胜次数: {PVPMatchesWon}\n"
        message += f"总失败次数: {PVPMatchesLost}\n"
        message += f"胜利占比: {PVPWLRatio}\n"
        message += f"总游玩时间: {PVPTimePlayed}\n"
        message += f"总局数: {PVPMatchesPlayed}\n"
        message += f"爆头率: {PVPAccuracy}\n"
        message += f"总爆头次数: {PVPHeadshots}\n"
        message += f"等级: {PVPLevel}\n"
        message += f"总经验: {PVPTotalXp}\n"
        message += f"---{season_name}赛季数据---\n"
        message += f"赛季排位MMR: {season_ranked_MMR}\n"
        message += f"赛季不含排位MMR: {season_unrank_MMR}\n"
    else:
        message = "404"
    return message
