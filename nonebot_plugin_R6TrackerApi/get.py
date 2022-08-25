from io import BytesIO
import os
import bs4, lxml
import httpx
from PIL import Image, ImageFont, ImageDraw
from PIL.PngImagePlugin import PngImageFile, PngInfo

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

params = {
    'name': '',
    'platform': ''
}

proxies = {
  'http://': 'http://localhost:15236',
  'https://': 'http://localhost:15236',
}

async def get(url):
    try:
        async with httpx.AsyncClient(headers=headers,params=params,proxies=proxies) as client:
            response = await client.get(url, timeout=30)
    except BaseException as e:
        try:
            async with httpx.AsyncClient(headers=headers,params=params) as client:
                response = await client.get(url, timeout=30)
        except BaseException as e:
            return False
    return response

async def get_r6_stats(ubi_name):
    #查询模块
    params['name'] = ubi_name
    url = 'https://r6.tracker.network/r6/search'
    res = await get(url)
    if not res:
        return "无法访问r6 tracker network呢"
    #如果用户存在
    if res.status_code in [200,302]:
        url = 'https://r6.tracker.network/profile/pc/' + ubi_name
        res = await get(url)
        if not res:
            return f"无法访问{url}呢"
        #HTML解码
        decoded = bs4.BeautifulSoup(res.text,'lxml')
        message = f"{ubi_name}的概览数据:\n"
        avatar_url = decoded.select("div[class = 'trn-profile-header__avatar trn-roundavatar trn-roundavatar--white']")[0].select("img")[0]["src"]
        PVPKDRatio = str(decoded.select("div[data-stat = 'PVPKDRatio']")[0].string).strip('\n').strip(' ').replace(',','')
        PVPDeaths = str(decoded.select("div[data-stat = 'PVPDeaths']")[0].string).strip('\n').strip(' ').replace(',','')
        PVPMatchesWon = str(decoded.select("div[data-stat = 'PVPMatchesWon']")[0].string).strip('\n').strip(' ').replace(',','')
        PVPMatchesLost = str(decoded.select("div[data-stat = 'PVPMatchesLost']")[0].string).strip('\n').strip(' ').replace(',','')
        PVPWLRatio = str(decoded.select("div[data-stat = 'PVPWLRatio']")[0].string).strip('\n').strip(' ').replace(',','')
        PVPTimePlayed = str(decoded.select("div[data-stat = 'PVPTimePlayed']")[0].string).strip('\n').strip(' ').replace(',','')
        PVPMatchesPlayed = str(decoded.select('div[data-stat = \"PVPMatchesPlayed\"]')[0].string).strip('\n').strip(' ').replace(',','')
        PVPAccuracy = str(decoded.select("div[data-stat = 'PVPAccuracy']")[0].string).strip("\n").replace(",","")
        PVPHeadshots = str(decoded.select("div[data-stat = 'PVPHeadshots']")[0].string).strip("\n").replace(",","")
        PVPMeleeKills = str(decoded.select("div[data-stat = 'PVPMeleeKills']")[0].string).strip("\n").replace(",","")
        if decoded.select("div[class = 'trn-defstat__data']")[0].select("div[class = 'trn-defstat__name']")[0].string == 'Level':
            PVPLevel = str(decoded.select("div[class = 'trn-defstat__value-stylized']")[0].string).strip('\n').strip(' ').replace(',','')
        else:
            PVPLevel = str(decoded.select("div[class = 'trn-defstat__value-stylized']")[1].string).strip('\n').strip(' ').replace(',','')
        PVPTotalXp = str(decoded.select("div[data-stat = 'PVPTotalXp']")[0].string).strip("\n").replace(",","")
        if len(decoded.select("div[class = 'r6-season__info']")[0].select("tspan")) <= 2:
            season_name = decoded.select("h2[class = 'trn-card__header-title']")[3].string
            season_ranked_MMR = decoded.select("div[class = 'r6-season__info']")[0].select("tspan")[1].string
            rank_name = decoded.select("div[class = 'r6-season__info']")[0].select("tspan")[0].string
            rank_icon_url = decoded.select("div[class = 'r6-season__info']")[0].select("image")[0]["xlink:href"]
        else:
            season_name = decoded.select("h2[class = 'trn-card__header-title']")[3].string
            season_ranked_MMR = decoded.select("div[class = 'r6-season__info']")[0].select("tspan")[2].string
            rank_name = decoded.select("div[class = 'r6-season__info']")[0].select("tspan")[1].string
            rank_icon_url = decoded.select("div[class = 'r6-season__info']")[0].select("image")[1]["xlink:href"]
        if len(decoded.select("div[class = 'r6-season']")[0].select("div[class = 'r6-season__stats']")[0].select("div[class = 'trn-defstat']")) <= 8:
            rank_max_MMR = "2500"
            rank_kd = "0.00"
            rank_kills_per_match = "0.00"
            rank_win_persent = decoded.select("div[class = 'r6-season']")[0].select("div[class = 'r6-season__stats']")[0].select("div[class = 'trn-defstat']")[0].select("div[class = 'trn-defstat__value']")[0].string
        else:
            rank_max_MMR = decoded.select("div[class = 'r6-season']")[0].select("div[class = 'r6-season__stats']")[0].select("div[class = 'trn-defstat']")[11].select("div[class = 'trn-defstat__value']")[0].string
            rank_kd = decoded.select("div[class = 'r6-season']")[0].select("div[class = 'r6-season__stats']")[0].select("div[class = 'trn-defstat']")[0].select("div[class = 'trn-defstat__value']")[0].text.split()[0]
            rank_kills_per_match = decoded.select("div[class = 'r6-season']")[0].select("div[class = 'r6-season__stats']")[0].select("div[class = 'trn-defstat']")[1].select("div[class = 'trn-defstat__value']")[0].text.split()[0]
            rank_win_persent = decoded.select("div[class = 'r6-season']")[0].select("div[class = 'r6-season__stats']")[0].select("div[class = 'trn-defstat']")[4].select("div[class = 'trn-defstat__value']")[0].string
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
        message += f"近战杀敌数: {PVPMeleeKills}\n"
        message += f"等级: {PVPLevel}\n"
        message += f"总经验: {PVPTotalXp}\n"
        message += f"---{season_name}赛季数据---\n"
        message += f"赛季排位MMR: {season_ranked_MMR}\n"
        message += f"赛季不含排位MMR: {season_unrank_MMR}\n"
    else:
        message = str(res.status_code)
    #绘图
    try:
        font170 = ImageFont.truetype(os.path.join(os.path.dirname(__file__),"ScoutCond-Italic.ttf"),170)
        font100 = ImageFont.truetype(os.path.join(os.path.dirname(__file__),"ScoutCond-Italic.ttf"),100)
        font50 = ImageFont.truetype(os.path.join(os.path.dirname(__file__),"ScoutCond-Italic.ttf"),50)
        url = avatar_url
        res = await get(url)
        if not res:
            return "无法访问育碧头像url呢(网络错误)"
        avatar = Image.open(BytesIO(res.content)).convert("RGBA")
        url = rank_icon_url
        res = await get(url)
        if not res:
            return f"无法访问{url}呢"
        rank_icon = Image.open(BytesIO(res.content))
        bg = Image.open(os.path.join(os.path.dirname(__file__),"bg.png")).convert("RGBA")
        avatar = avatar.resize((256,256))
        bg.paste(avatar,(100,100))
        draw = ImageDraw.Draw(bg)
        #general
        draw.text((400,200),"GENERAL:",fill=(250,250,250),font=font170)
        offset = round(font170.getsize("GENERAL:")[0]/2)-round(font100.getsize(ubi_name)[0]/2)
        if 400+offset <= 360:#offset out of box
            offset += 360-(400+offset)
        draw.text((400+offset,120),ubi_name,fill=(250,250,250),font=font100)
        draw.line((150,415,625,415),fill=(250,250,250),width=5)
        draw.text((100,450),f"Level:{PVPLevel}",fill=(250,250,250),font=font100)
        draw.text((400,450),f"K/D:{PVPKDRatio}",fill=(250,250,250),font=font100)
        draw.text((100,600),f"Melee Kills:{PVPMeleeKills}",fill=(250,250,250),font=font100)
        draw.text((100,750),f"Headshot %:{PVPAccuracy}",fill=(250,250,250),font=font100)
        draw.text((100,900),f"TOT Time:{PVPTimePlayed}",fill=(250,250,250),font=font100)
        draw.text((100,1050),f"TOT EXP:{PVPTotalXp}",fill=(250,250,250),font=font100)
        #ranked
        draw.text((1124,200),"RANK:",fill=(250,250,250),font=font170)
        draw.text((1434,250),f"{rank_name}",fill=(250,250,250),font=font50)
        #calculate offset
        offset = round(font50.getsize(f"{rank_name}")[0]/2)-round(rank_icon.size[0]/2)
        bg.alpha_composite(rank_icon,(1434+offset,125))
        offset = round(font50.getsize(f"{rank_name}")[0]/2)-round(font50.getsize(f"MMR:{season_ranked_MMR}")[0]/2)
        draw.text((1434+offset,300),f"MMR:{season_ranked_MMR}",fill=(250,250,250),font=font50)
        draw.line((1175,415,1570,415),fill=(250,250,250),width=5)
        draw.text((1124,450),f"MMR:{season_ranked_MMR}",fill=(250,250,250),font=font100)
        draw.text((1124,600),f"MAX MMR:{rank_max_MMR}",fill=(250,250,250),font=font100)
        draw.text((1124,750),f"WIN %:{rank_win_persent}",fill=(250,250,250),font=font100)
        draw.text((1124,900),f"K/D:{rank_kd}",fill=(250,250,250),font=font100)
        draw.text((1124,1050),f"KILLS/MATCH:{rank_kills_per_match}",fill=(250,250,250),font=font100)
        #bg.show()
        bg.save(os.path.join(os.path.dirname(__file__),"gen.png"))
        #add meta data
        image = PngImageFile(os.path.join(os.path.dirname(__file__),"gen.png"))
        metadata = PngInfo()
        metadata.add_text("made by", "marko_bot by marko1616")
        image.save(os.path.join(os.path.dirname(__file__),"gen.png"),pnginfo=metadata)

        return message
    except:
        if len(message) <= 5:
            return [f"状态码:{message}","(网络错误)"]
        else:
            return [message,"绘图错误捏(可尝试重试)"]

async def get_matches_played(ubi_name):
    params['name'] = ubi_name
    url = 'https://r6.tracker.network/r6/search'
    res = await get(url)
    if not res:
        return False
    #如果用户存在
    if res.status_code in [200,302]:
        url = 'https://r6.tracker.network/profile/pc/' + ubi_name
        res = await get(url)
        if not res:
            return False
        decoded = bs4.BeautifulSoup(res.text,'lxml')
        PVPMatchesPlayed = str(decoded.select('div[data-stat = \"PVPMatchesPlayed\"]')[0].string).strip('\n').strip(' ').replace(',','')
        return int(''.join(PVPMatchesPlayed.split(",")))
    else:
        return False