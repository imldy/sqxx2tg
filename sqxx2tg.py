import json
import requests
import telegram


class SQ_Video_Bili():
    def __init__(self, avid, bvid, title, desc, dynamic):
        self.avid = avid
        self.bvid = bvid
        self.title = title
        self.desc = desc  # 实际是主要内容
        self.dynamic_str = dynamic  # 实际是简介
        self.link = "https://www.bilibili.com/video/{bvid}".format(bvid=bvid)
        self.tags = []


class SQ_Dynamic_Bili():
    def __init__(self, dynamic_id, type, timestamp, bvid, card):
        self.dynamic_id = dynamic_id
        self.type = type  # type = 8 才是视频发布动态
        self.timestamp = timestamp
        self.bvid = bvid
        self.card = card  # 实际是简介


def load_conf():
    return json.loads(open("conf.json").read().strip())


CONF = load_conf()
Telegram_CONF = CONF["Telegram"]
Info_Source_CONF = CONF["Info_Source"]


def get_dynamics():
    url = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={uid}".format(
        uid=Info_Source_CONF["bilibili_uid"])
    resp = requests.get(url)
    dynamic_list = resp.json()["data"]["cards"]
    return dynamic_list


def get_dynamics_obj():
    sq_dynamic_bili_list = []
    for dynamic in dynamics:
        # print(dynamic["card"])
        dynamic_desc = dynamic["desc"]  # 提取动态元数据
        if dynamic_desc["type"] == 8:  # 等于8意味着是视频发布
            card_obj = json.loads(dynamic["card"])  # 将卡片字符串转为Python对象
            sq_video_bili = SQ_Video_Bili(
                card_obj["aid"]
                , dynamic_desc["bvid"]
                , card_obj["title"]
                , card_obj["desc"]
                , card_obj["dynamic"]
            )  #
            sq_dynamic_bili = SQ_Dynamic_Bili(
                dynamic_desc["dynamic_id"]
                , dynamic_desc["type"]
                , dynamic_desc["timestamp"]
                , dynamic_desc["bvid"]
                , sq_video_bili
            )
            # 给对象添加tag
            if sq_dynamic_bili.card.title.startswith("【睡前消息"):
                sq_dynamic_bili.card.tags = ["睡前消息视频"]
            elif sq_dynamic_bili.card.title.startswith("【万物由来"):
                sq_dynamic_bili.card.tags = ["万物由来"]
            elif sq_dynamic_bili.card.title.startswith("【睡前故事"):
                sq_dynamic_bili.card.tags = ["睡前故事"]

            # print(sq_dynamic_bili.type, sq_dynamic_bili.card.title)
            sq_dynamic_bili_list.append(sq_dynamic_bili)
    return sq_dynamic_bili_list


def push_message_2_TG(bot, sq_dynamic_bili_list):
    for sq_dynamic_bili in sq_dynamic_bili_list:
        sq_video_bili = sq_dynamic_bili.card
        resp = bot.send_message(
            chat_id=Telegram_CONF["Publish_Channel_ID"]
            , text="{video_title}\n【介绍】：{video_introduce}\n【主要内容】：{video_desc}\n【视频链接】：{video_link}\n\n#{tag_str}"
                .format(video_title=sq_video_bili.title
                        , video_introduce=sq_video_bili.dynamic_str
                        , video_desc=sq_video_bili.desc
                        , video_link=sq_video_bili.link
                        , tag_str=" #".join(sq_video_bili.tags)  # 多个tag时自动添加
                        )
            , parse_mode=telegram.ParseMode.MARKDOWN
        )
        print(resp.text)


dynamics = get_dynamics()  # 直接接口返回的数据

sq_dynamic_bili_list = get_dynamics_obj()  # 处理后，整理为对象的数据

bot = telegram.Bot(token=Telegram_CONF["Bot_Token"])
push_message_2_TG(bot, sq_dynamic_bili_list)
print("结束")