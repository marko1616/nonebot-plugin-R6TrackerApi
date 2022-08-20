import os

from nonebot import get_driver,on_command
from nonebot.log import logger
from nonebot.adapters import Bot, Event
from nonebot.params import CommandArg, ArgPlainText
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Message
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from nonebot_plugin_apscheduler import scheduler

from .config import Config
from .get import get_r6_stats
from .contributions import contributions as contribution_obj

try:
    import ujson as json
except ModuleNotFoundError:
    import json

def write_cache_to_json(data):
    with open(ubi_name_cache_file, "w", encoding="utf-8") as file:
        file.write(json.dumps(data))

ubi_name_cache_file = os.path.join("data", "ubi_name_cache_file.json")
self_strs = ["我","自己","私","wo","me","self","watashi"]#表示自己的词

global_config = get_driver().config
config = Config.parse_obj(global_config)

if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists(ubi_name_cache_file):
    write_cache_to_json({"groups": {}, "friends":{}})

contribution = contribution_obj(open(os.path.join("data", "contributions_data.json"),"w+"))

file = open(ubi_name_cache_file, "r", encoding="utf-8")
ubi_name_cache = json.loads(file.read())
file.close()

#每小时统计群肝量
@scheduler.scheduled_job("cron", minute="*")
async def do_the_statistics():
    for group in ubi_name_cache["groups"]:
        for member in ubi_name_cache["groups"][group]:
            #get_r6_stats(ubi_name_cache["groups"][group][member]["ubi_name"])
            pass

search_r6_data = on_command("r6战绩查询",priority=5)
@search_r6_data.handle()
async def search_r6_data_handle(matcher: Matcher, bot: Bot, event: Event, args : Message = CommandArg()):
    #初始化每一次的事件处理用标识变量
    Config.at_flag = False#是否强制使用缓存@或表示自己
    Config.use_cache_flag = False#缓存存在标识

    plain_text = args.extract_plain_text()
    if "[CQ:at,qq=" in event.raw_message:
        matcher.set_arg("ubi_name", Message(event.raw_message.split("=")[1].split("]")[0]))#获取@里面的QQ号当参数
        Config.at_flag = True

    if plain_text:
        matcher.set_arg("ubi_name", args)

@search_r6_data.got("ubi_name", prompt='名称は?')
async def get_data(bot: Bot, event: Event,ubi_name: str = ArgPlainText("ubi_name")):
    if "[CQ:at,qq=" in event.raw_message:
        ubi_name =  event.raw_message.split("=")[1].split("]")[0]
        Config.at_flag = True
    if ubi_name in self_strs:
        Config.at_flag = True
    #校验是否是群名称
    if type(event) == GroupMessageEvent:
        #查询是否是QQ群名或者@
        group_id = str(event.group_id)
        member_list = await bot.get_group_member_list(group_id=group_id)

        if group_id in ubi_name_cache["groups"]:
            for member in member_list:
                if str(member['user_id']) in ubi_name_cache["groups"][group_id]:
                    if str(member['user_id']) == ubi_name or member['card'] == ubi_name or member['nickname'] == ubi_name or (ubi_name in self_strs and member == event.get_user_id()):
                        ubi_name = ubi_name_cache["groups"][group_id][str(member['user_id'])]["ubi_name"]
                        await search_r6_data.send(f"检测到是群名/自我查询自动使用已缓存的UBI名称{ubi_name}")
                        Config.use_cache_flag = True
        else:
            ubi_name_cache["groups"][group_id] = {}
            write_cache_to_json(ubi_name_cache)
    
    elif Config.at_flag:#如果是好友且查询自己
        friend_id = str(event.get_user_id())
        if friend_id in ubi_name_cache["friends"]:
            ubi_name = ubi_name_cache["friends"][friend_id]["ubi_name"]
            Config.use_cache_flag = True

    if not Config.use_cache_flag and Config.at_flag:#如果在@的情况下没找到缓存
        #search_r6_data.send("检测到你在使用@，但缓存并没有对应的UBI用户名。请输入UBI用户名:")
        await search_r6_data.finish("检测到你在使用@或者查询自己，但缓存并没有对应的UBI用户名。请提醒他使用(/设置育碧名称)设置自己的UBI名称")

    await search_r6_data.send("开始请求r6 tracker network")
    message = await get_r6_stats(ubi_name)
    if message != "404":
        await search_r6_data.send(message)
    else:#404处理
        if Config.use_cache_flag:
            await search_r6_data.send(f"うえ？对{ubi_name}的缓存查询的结果404了!快检查是不是育碧名称设置错了")
        else:
            await search_r6_data.send(f"没有对{ubi_name}的查询结果捏~")

set_ubi_name = on_command("设置育碧名称",priority=5)
@set_ubi_name.handle()
async def set_ubi_name_handle(matcher: Matcher, bot: Bot, event: Event, args : Message = CommandArg()):
    plain_text = args.extract_plain_text()
    if plain_text:
        matcher.set_arg("ubi_name", args)

@set_ubi_name.got("ubi_name", prompt='育碧名称是?')
async def get_and_set_ubi_name(bot: Bot, event: Event,ubi_name: str = ArgPlainText("ubi_name")):
    if type(event) == GroupMessageEvent:
        user_id = str(event.user_id)
        group_id = str(event.group_id)
        if not group_id in ubi_name_cache["groups"]:
            ubi_name_cache["groups"][group_id] = {}
        ubi_name_cache["groups"][group_id][user_id] = {}
        ubi_name_cache["groups"][group_id][user_id]["user_id"] = user_id
        ubi_name_cache["groups"][group_id][user_id]["ubi_name"] = ubi_name
        write_cache_to_json(ubi_name_cache)
        await set_ubi_name.finish(f"已经成功将你({str(user_id)})的育碧名称设置成{ubi_name}")
    else:#好友名称设置
        friend_id = str(event.get_user_id())
        if not friend_id in ubi_name_cache["friends"]:
            ubi_name_cache["friends"][friend_id] = {}
        ubi_name_cache["friends"][friend_id]["ubi_name"] = ubi_name
        write_cache_to_json(ubi_name_cache)
        await set_ubi_name.finish(f"已经成功将你({str(friend_id)})的育碧名称设置成{ubi_name}")

