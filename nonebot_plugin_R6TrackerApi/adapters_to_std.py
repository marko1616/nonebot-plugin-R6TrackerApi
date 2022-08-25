import requests
try:
    import ujson as json
except ImportError:
    import json

from nonebot.log import logger
from nonebot.adapters.kaiheila import Event as kaiheila_Event
from nonebot.adapters.onebot.v11 import Event as onebot_v11_Event
from nonebot.adapters.kaiheila.event import MessageEvent as kaiheila_MessageEvent, ChannelMessageEvent as kaiheila_ChannelMessageEvent
from nonebot.adapters.onebot.v11.event import MessageEvent as onebot_v11_MessageEvent, GroupMessageEvent as onebot_v11_GroupMessageEvent
from nonebot.adapters.kaiheila import Bot as kaiheila_Bot
from nonebot.adapters.onebot.v11 import Bot as onebot_v11_Bot
from nonebot.adapters.kaiheila.message import Message as kaiheila_Message
from nonebot.adapters.onebot.v11.message import Message as onebot_v11_Message
from nonebot.adapters.kaiheila.message import MessageSegment as kaiheila_MessageSegment
from nonebot.adapters.onebot.v11.message import MessageSegment as onebot_v11_MessageSegment
from nonebot.adapters import Event

async def get_group_member_list(bot,group_id):
    """
    返回(适配器类型(str),用户列表(list))
    PS:此函数为异步函数
    列表结构为:
    [
        {
            'user_id':xxx
            'nickname':xxx
        }
    ]
    """
    if isinstance(bot,kaiheila_Bot):
        res = await bot.call_api("guild/user-list",query={"guild_id":group_id})
        user_list = []
        for item in res["items"]:
            user_list.append({'user_id':item['id'],'nickname':item['nickname']})
        return (kaiheila_Bot,user_list)
    elif isinstance(bot,onebot_v11_Bot):
        return (onebot_v11_Bot,await bot.get_group_member_list(group_id=group_id))
    else:
        logger.debug(f"[callapi to std] | not valid bot{type(bot)}")

def get_msg(event) -> str:
    """
    返回str类型的消息
    """
    if isinstance(event,kaiheila_MessageEvent):
        return str(event.get_message())
    elif isinstance(event,onebot_v11_MessageEvent):
        return event.raw_message
    else:
        logger.debug(f"[event to std] | not valid event{type(event)}")

def is_what_adapter(event):
    if isinstance(event,kaiheila_Event):
        return "kook"
    elif isinstance(event,onebot_v11_Event):
        return "onebot_v11"
    else:
        logger.debug(f"[event adapter to std] | not valid event {type(event)}")


def is_group_msg(event):
    """
    返回(适配器类型(str),群号,发送者ID)或False(开黑啦返回服务器ID)
    """
    if isinstance(event,kaiheila_ChannelMessageEvent):
        return ('kaiheila',event.extra.guild_id,event.user_id)
    elif isinstance(event,onebot_v11_GroupMessageEvent):
        return ('onebot_v11',event.group_id,event.user_id)
    return False

def append_MessageSegment(adapter_type:str,type:str,data:str,Message=None):
    """
    返回(消息)
    """
    if adapter_type == "kook":
        if Message == None:
            Message = kaiheila_Message()
        if type == "text":
            return Message + kaiheila_MessageSegment.text(data)
        elif type == "image":
            return Message + kaiheila_MessageSegment.Card(json.dumps(
                [
                    {
                        "type": "card",
                        "theme": "secondary",
                        "size": "lg",
                        "modules": [
                            {
                                "type": "image-group",
                                "elements": [
                                    {
                                        "type": "image",
                                        "src": data
                                    }
                                ]
                            }
                        ]
                    }
                ]))
    elif adapter_type == "onebot_v11":
        if Message == None:
            Message = onebot_v11_Message()
        if type == "text":
            return Message + onebot_v11_MessageSegment.text(data)
        elif type == "image":
            return Message + onebot_v11_MessageSegment.image(data)

async def send_media(bot,type:str,data:str):
    if isinstance(bot,kaiheila_Bot):
        if type == "image":
            with open(data,'rb') as file:
                res = requests.request("POST","https://www.kaiheila.cn/api/v3/asset/create",headers={"Authorization":f"Bot {bot.token}"},files={"file":file.read()})
                return json.loads(res.text)["data"]["url"]

        