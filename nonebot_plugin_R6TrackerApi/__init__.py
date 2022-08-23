import os,time
from PIL import Image, ImageDraw, ImageFont

from nonebot import get_driver,on_command,require
from nonebot.log import logger
from nonebot.adapters import Bot, Event
from nonebot.params import CommandArg, ArgPlainText
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Message
from adapters_to_std import get_msg, is_group_msg, get_group_member_list, is_what_adapter

from nonebot_plugin_apscheduler import scheduler

from .config import Config
from .get import get_r6_stats, get_matches_played
from .contributions import contributions as contributions_obj

try:
    import ujson as json
except ModuleNotFoundError:
    import json

require("nonebot_plugin_apscheduler")

def write_cache_to_json(data):
    with open(ubi_name_cache_file, "w", encoding="utf-8") as file:
        file.write(json.dumps(data))

ubi_name_cache_file = os.path.join("data", "ubi_name_cache_file.json")
self_strs = ["我","自己","私","wo","me","self","watashi"]#表示自己的词

global_config = get_driver().config
config = Config.parse_obj(global_config)
at_flag = False
use_cache_flag = False

if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists(ubi_name_cache_file):
    write_cache_to_json({"onebot_v11":{"groups": {}, "friends":{}},"kook":{"groups": {}, "friends":{}}})

contribution_manager = contributions_obj(os.path.join("data", "r6_contributions_data.json"))

file = open(ubi_name_cache_file, "r", encoding="utf-8")
ubi_name_cache = json.loads(file.read())
file.close()

search_r6_data = on_command("r6战绩查询",aliases={"r6d"},priority=5)
@search_r6_data.handle()
async def search_r6_data_handle(matcher: Matcher, bot: Bot, event: Event, args : Message = CommandArg()):
    global at_flag
    global use_cache_flag
    #初始化每一次的事件处理用标识变量
    at_flag = False#是否强制使用缓存@或表示自己
    use_cache_flag = False#缓存存在标识

    plain_text = args.extract_plain_text()
    if "[CQ:at,qq=" in get_msg(event):
        matcher.set_arg("ubi_name", Message(get_msg(event).split("=")[1].split("]")[0]))#获取@里面的QQ号当参数
        at_flag = True

    if plain_text:
        matcher.set_arg("ubi_name", args)

@search_r6_data.got("ubi_name", prompt='名称は?')
async def get_data(bot: Bot, event: Event,ubi_name: str = ArgPlainText("ubi_name")):
    global at_flag
    global use_cache_flag
    adapter_type = is_what_adapter(event)
    if "[CQ:at,qq=" in get_msg(event):
        ubi_name =  get_msg(event).split("=")[1].split("]")[0]
        at_flag = True
    if ubi_name in self_strs:   
        at_flag = True
    #校验是否是群名称
    if is_group_msg(event):
        #查询是否是QQ群名或者@
        group_id = str(is_group_msg(event)[1])
        member_list = (await get_group_member_list(bot,group_id=group_id))[1]
        if group_id in ubi_name_cache[adapter_type]["groups"]:
            for member in member_list:
                if str(member['user_id']) in ubi_name_cache[adapter_type]["groups"][group_id]:
                    if str(member['user_id']) == ubi_name or member['card'] == ubi_name or member['nickname'] == ubi_name or (ubi_name in self_strs and str(member["user_id"]) == event.get_user_id()):
                        ubi_name = ubi_name_cache[adapter_type]["groups"][group_id][str(member['user_id'])]["ubi_name"]
                        await search_r6_data.send(f"检测到是群名/自我查询自动使用已缓存的UBI名称{ubi_name}")
                        use_cache_flag = True
        else:
            ubi_name_cache[adapter_type]["groups"][group_id] = {}
            write_cache_to_json(ubi_name_cache)
    
    elif at_flag:#如果是好友且查询自己
        friend_id = str(event.get_user_id())
        if friend_id in ubi_name_cache[adapter_type]["friends"]:
            ubi_name = ubi_name_cache[adapter_type]["friends"][friend_id]["ubi_name"]
            use_cache_flag = True

    if not use_cache_flag and at_flag:#如果在@的情况下没找到缓存
        #search_r6_data.send("检测到你在使用@，但缓存并没有对应的UBI用户名。请输入UBI用户名:")
        await search_r6_data.finish("检测到你在使用@或者查询自己，但缓存并没有对应的UBI用户名。请提醒他使用(/设置育碧名称)设置自己的UBI名称")

    await search_r6_data.send("开始请求r6 tracker network")
    message = await get_r6_stats(ubi_name)
    if message != "404":
        if len(message) >= 50 and message != list:#如果非网络错误
            await search_r6_data.send(Message(message))
            await search_r6_data.send(Message(f'[CQ:image,file=file:///{os.path.join(os.path.dirname(__file__),"gen.png")}]'))
        elif message == list:
            await search_r6_data.send(Message(message[0]))
            await search_r6_data.send(Message(message[1]))
        else:
            await search_r6_data.send(Message(message))
    else:#404处理
        if use_cache_flag:
            await search_r6_data.send(f"うえ？对{ubi_name}的缓存查询的结果404了!快检查是不是育碧名称设置错了")
        else:
            await search_r6_data.send(f"没有对{ubi_name}的查询结果捏~")

set_ubi_name = on_command("设置育碧名称",aliases={"stubi"},priority=5)
@set_ubi_name.handle()
async def set_ubi_name_handle(matcher: Matcher, bot: Bot, event: Event, args : Message = CommandArg()):
    plain_text = args.extract_plain_text()
    if plain_text:
        matcher.set_arg("ubi_name", args)

@set_ubi_name.got("ubi_name",prompt='育碧名称是?')
async def get_and_set_ubi_name(bot: Bot, event: Event,ubi_name: str = ArgPlainText("ubi_name")):
    adapter_type = is_what_adapter(event)
    if is_group_msg(event):
        user_id = str(event.user_id)
        group_id = str(is_group_msg(event)[1])
        if not group_id in ubi_name_cache[adapter_type]["groups"]:
            ubi_name_cache[adapter_type]["groups"][group_id] = {}
        ubi_name_cache[adapter_type]["groups"][group_id][user_id] = {}
        ubi_name_cache[adapter_type]["groups"][group_id][user_id]["user_id"] = user_id
        ubi_name_cache[adapter_type]["groups"][group_id][user_id]["ubi_name"] = ubi_name
        write_cache_to_json(ubi_name_cache)
        await set_ubi_name.finish(f"已经成功将你({str(user_id)})的育碧名称设置成{ubi_name}")
    else:#好友名称设置
        friend_id = str(event.get_user_id())
        if not friend_id in ubi_name_cache[adapter_type]["friends"]:
            ubi_name_cache[adapter_type]["friends"][friend_id] = {}
        ubi_name_cache[adapter_type]["friends"][friend_id]["ubi_name"] = ubi_name
        write_cache_to_json(ubi_name_cache)
        await set_ubi_name.finish(f"已经成功将你({str(friend_id)})的育碧名称设置成{ubi_name}")

get_today_r6data = on_command("今日群r6数据",aliases={"tr6d"},priority=5)
@get_today_r6data.handle()
async def _():
    res = contribution_manager.get_data_today()
    await get_today_r6data.send(str(res))
    res.sort(key=lambda x:x[1],reverse=True)
    img = Image.new('RGBA',(2048,2048),(25,25,25))
    draw = ImageDraw.Draw(img)
    font50 = ImageFont.truetype(os.path.join(os.path.dirname(__file__),"ScoutCond-Italic.ttf"),50)
    pixel_y = 100
    draw.text((100,25),"data will update 1 time per two hours",fill=(250,250,250),font=font50)
    for data in res:
        draw.text((100,pixel_y),f"{data[0]}({data[1]} rounds)",fill=(250,250,250),font=font50)
        fill_green = int(data[1] * 25.5)
        if fill_green > 255:
            fill_green = 255
        draw.rectangle(((500, pixel_y),(500+int(data[1])*50, pixel_y+50)), fill=(255-fill_green,255,255-fill_green), width=5)
        pixel_y += 75
    img.save(os.path.join(os.path.dirname(__file__),"gen.png"))
    await search_r6_data.send(Message(f'[CQ:image,file=file:///{os.path.join(os.path.dirname(__file__),"gen.png")}]'))

#肝量数据统计
manual_update = on_command("手动更新r6数据",aliases={"r6u"},permission=SUPERUSER)
@manual_update.handle()
@scheduler.scheduled_job("cron", day="*", hour="23", minute="40")#减少过天误差
@scheduler.scheduled_job("cron", hour="*/2",minute="30")
async def contribute():
    for adapter_type in ["onebot_v11","kook"]:
        ubi_name_list = []
        for group in ubi_name_cache[adapter_type]["groups"]:
            for user in ubi_name_cache[adapter_type]["groups"][group]:
                ubi_name = ubi_name_cache[adapter_type]["groups"][group][user]["ubi_name"]
                if ubi_name not in ubi_name_list:
                    ubi_name_list.append(ubi_name)
        now_time = time.time()
        for ubi_name in ubi_name_list:
            succ_flag = False
            for t in range(3):
                matches_played = await get_matches_played(ubi_name)
                if matches_played:
                    contribution_manager.update_data(now_time,matches_played,ubi_name)
                    logger.debug(f"[R6TrackerApi] | 将时间{now_time}下育碧名称为{ubi_name}的总对战数设置为{matches_played}")
                    succ_flag = True
                    break
            if not succ_flag:
                logger.error(f"[R6TrackerApi] | 无法获取用户{ubi_name}的对战数量(在三次重试后)无法统计")

@scheduler.scheduled_job("cron", day="*", hour="23", minute="50")#减少过天误差
async def contribute():
    logger.debug(f"[R6TrackerApi] | 已统计今日r6数据")
    contribution_manager.write_today_data()