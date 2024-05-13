import json
import time
import requests
import telegram
import weibo_article
from urllib.parse import quote


def get_datetime():
    local_time = time.localtime()
    dt = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    return dt


def log(str: str):
    print("{} - {}".format(get_datetime(), str))


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


def get_dynamics():
    uid_list = Info_Source_CONF["bilibili_uid_list"]
    dynamic_list = []
    max_count = 3
    headers = {
        "Cookie": Info_Source_CONF["bilibili_cookie"],
        "User-Agent": Info_Source_CONF["User-Agent"]
    }
    for uid in uid_list:
        offset_dynamic_id = None
        count = 0
        while (True):
            url = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
            params = {
                "host_mid": uid,
                "offset": offset_dynamic_id
            }
            resp = requests.get(url, params=params, headers=headers)
            rj = resp.json()
            if rj["data"]["has_more"] == 0:
                # 没有更多了，也代表本次没有获取到新数据
                break
            try:
                dynamic_list += rj["data"]["items"]
            except KeyError as ke:
                log("取动态卡片报错，不存在")
                break
            count += 1
            if rj["data"]["offset"] != 0 and count < max_count:
                offset_dynamic_id = rj["data"]["offset"]
            else:
                break
    return dynamic_list


def get_dynamics_obj(dynamics):
    sq_dynamic_bili_list = []
    for dynamic in dynamics:
        # log(dynamic["card"])
        if dynamic["basic"]["comment_type"] == 1:  # 等于8意味着是视频发布
            card_obj = dynamic["modules"]["module_dynamic"]["major"]["archive"]  # 将卡片字符串转为Python对象
            sq_video_bili = SQ_Video_Bili(
                card_obj["aid"]
                , card_obj["bvid"]
                , card_obj["title"]
                , None
                , card_obj["desc"]
            )  #
            if dynamic["modules"]["module_dynamic"]["desc"] != None:
                sq_video_bili.desc = dynamic["modules"]["module_dynamic"]["desc"]["text"]
            sq_dynamic_bili = SQ_Dynamic_Bili(
                dynamic["id_str"]
                , dynamic["basic"]["comment_type"]
                , dynamic["modules"]["module_author"]["pub_ts"]
                , card_obj["bvid"]
                , sq_video_bili
            )
            # 给对象添加tag
            if sq_dynamic_bili.card.title.startswith("【睡前消息"):
                sq_dynamic_bili.card.tags = ["睡前消息视频"]
            elif sq_dynamic_bili.card.title.startswith("【万物由来"):
                sq_dynamic_bili.card.tags = ["万物由来"]
            elif sq_dynamic_bili.card.title.startswith("【睡前故事"):
                sq_dynamic_bili.card.tags = ["睡前故事"]
            elif sq_dynamic_bili.card.title.startswith("【参考信息"):
                sq_dynamic_bili.card.tags = ["参考信息"]
            elif sq_dynamic_bili.card.title.startswith("【讲点黑话"):
                sq_dynamic_bili.card.tags = ["讲点黑话"]
            elif sq_dynamic_bili.card.title.startswith("【高见"):
                sq_dynamic_bili.card.tags = ["高见"]

            # log(sq_dynamic_bili.type, sq_dynamic_bili.card.title)
            sq_dynamic_bili_list.append(sq_dynamic_bili)
    return sq_dynamic_bili_list[::-1]


def is_pushed(sq_dynamic_bili):
    # 判断是否bvid已经在这个文件中
    bvid_list = open("pushed_bvid.txt").read().strip().split("\n")
    if sq_dynamic_bili.bvid in bvid_list:
        return True
    return False


def article_is_pushed(sq_article_weibo):
    # 判断是否weibo_mid已经在这个文件中
    weibo_mid_list = open("pushed_weibo_mid.txt").read().strip().split("\n")
    if sq_article_weibo.mid in weibo_mid_list:
        return True
    return False


def save_pushed_log(sq_dynamic_bili):
    open("pushed_bvid.txt", "a").write(sq_dynamic_bili.bvid + "\n")


def save_article_pushed_log(sq_article_weibo):
    open("pushed_weibo_mid.txt", "a").write(sq_article_weibo.mid + "\n")


def push_message_2_TG(bot, sq_dynamic_bili_list):
    for sq_dynamic_bili in sq_dynamic_bili_list:
        # 判断当前视频是否已经推送到TG
        if is_pushed(sq_dynamic_bili):
            # 已推送过，跳过此视频
            log("视频：{video_title} 已推送过".format(video_title=sq_dynamic_bili.card.title))
            continue
        sq_video_bili = sq_dynamic_bili.card
        resp = bot.send_message(
            chat_id=Telegram_CONF["Publish_Channel_ID"]
            , text="*{video_title}*\n"
                   "【主要内容】：{video_desc}\n"
                   "【内容介绍】：{video_introduce}\n"
                   "【视频链接】：[bilibili]({video_link})|[YouTube]({youtube_video_link})\n"
                   "\n"
                   "#{tag_str}"
                .format(video_title=sq_video_bili.title
                        , video_introduce=sq_video_bili.dynamic_str
                        , video_desc=sq_video_bili.desc
                        , video_link=sq_video_bili.link
                        , youtube_video_link="https://www.youtube.com/results?search_query=" + quote(sq_video_bili.title)
                        , tag_str=" #".join(sq_video_bili.tags)  # 多个tag时自动添加
                        )
            , parse_mode=telegram.ParseMode.MARKDOWN
        )
        save_pushed_log(sq_video_bili)
        log(resp.text)


def get_article_obj():
    # 专栏页面
    return weibo_article.get_article_obj(Info_Source_CONF)


def push_article_2_TG(bot, sq_article_weibo_list):
    for sq_article_weibo in sq_article_weibo_list:
        # 判断当前视频是否已经推送到TG
        if article_is_pushed(sq_article_weibo):
            # 已推送过，跳过此视频
            log("文章：{video_title} 已推送过".format(video_title=sq_article_weibo.title))
            continue
        resp = bot.send_message(
            chat_id=Telegram_CONF["Publish_Channel_ID"]
            , text="*{article_title}*\n【文章链接】：{article_link}\n【封面】：[封面链接]({article_cover_pic_link})\n\n#{tag_str}"
                .format(article_title=sq_article_weibo.title
                        , article_link=sq_article_weibo.link
                        , article_cover_pic_link=sq_article_weibo.cover_pic_link
                        , tag_str=" #".join(sq_article_weibo.tags)  # 多个tag时自动添加
                        )
            , parse_mode=telegram.ParseMode.MARKDOWN
        )
        save_article_pushed_log(sq_article_weibo)
        log(resp.text)


def start():
    global CONF, Telegram_CONF, Info_Source_CONF
    CONF = load_conf()
    Telegram_CONF = CONF["Telegram"]
    Info_Source_CONF = CONF["Info_Source"]

    dynamics = get_dynamics()  # 直接接口返回的数据

    sq_dynamic_bili_list = get_dynamics_obj(dynamics)  # 处理后，整理为对象的数据

    bot = telegram.Bot(token=Telegram_CONF["Bot_Token"])
    push_message_2_TG(bot, sq_dynamic_bili_list)

    sq_article_weibo_list = get_article_obj()
    if sq_article_weibo_list is None:
        log("sq_article_weibo_list is None")
    else:
        push_article_2_TG(bot, sq_article_weibo_list)

    log("结束")


def tencent_SCF(a, b):
    start()


start()
