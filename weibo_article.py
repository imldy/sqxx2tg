import requests
from lxml import etree
from requests.cookies import cookiejar_from_dict


class SQ_Article_Weibo():
    def __init__(self, mid, title, cover_pic_link, link):
        self.mid = mid
        self.title = title
        self.cover_pic_link = cover_pic_link
        self.link = link
        self.tags = []


def get_tid(headers):
    import requests
    """
    获取tid,c,w
    :return:tid
    """
    tid_url = "https://passport.weibo.com/visitor/genvisitor"
    data = {
        "cb": "gen_callback",
        "fp": {
            "os": "3",
            # 未完成的自动获取浏览器标识的功能
            # re.findall("Chrome/(.*?) ", headers["User-Agent"])[0].replace(".", ",")
            "browser": "Chrome87,0,4280,88",
            "fonts": "undefined",
            "screenInfo": "1920*1080*24",
            "plugins": "Portable Document Format::internal-pdf-viewer::Chrome PDF Plugin|::mhjfbmdgcfjbbpaeojofohoefgiehjai::Chrome PDF Viewer|::internal-nacl-plugin::Native Client"
        }
    }
    req = requests.post(url=tid_url, data=data, headers=headers)

    if req.status_code == 200:
        ret = eval(req.text.replace("window.gen_callback && gen_callback(", "").replace(");", "").replace("true", "1"))
        return ret.get('data').get('tid')
    return None


def get_cookie(headers):
    """
    获取完整的cookie
    :return: cookie
    """
    import requests
    import random
    tid = get_tid(headers)
    if not tid:
        return None

    cookies = {
        "tid": tid + "__095"  # + tid_c_w[1]
    }
    url = "https://passport.weibo.com/visitor/visitor?a=incarnate&t={tid}" \
          "&w=2&c=095&gc=&cb=cross_domain&from=weibo&_rand={rand}"
    req = requests.get(url.format(tid=tid, rand=random.random()),
                       cookies=cookies, headers=headers)
    if req.status_code != 200:
        return None

    ret = eval(req.text.replace("window.cross_domain && cross_domain(", "").replace(");", "").replace("null", "1"))

    try:
        sub = ret['data']['sub']
        if sub == 1:
            return None
        subp = ret['data']['subp']
    except KeyError:
        return None
    return sub, subp


def getWeiboCookie(user_agent):
    headers = {
        "User-Agent": user_agent,
    }

    # 循环到Cookie不是Node为止
    while True:
        try:
            res = get_cookie(headers)
            if res is not None:
                return res
        except:
            continue


def getNewWeiboCookie():
    sub, subp = getWeiboCookie(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    cookiejar = cookiejar_from_dict({
        "SUB": sub,
        "SUBP": subp
    })
    return cookiejar


def get_article_cover_link_by():
    return "暂无"


def get_article_obj(Info_Source_CONF):
    column_url = Info_Source_CONF["weibo_column_url"]
    if column_url == "" or column_url is None:
        return
    resp = requests.get(url=column_url, cookies=cookiejar)
    # print(resp.text)
    html = etree.HTML(resp.text)
    article_html_list = html.xpath('//div[@class="UG_list_b"]')
    article_list = []
    for i in article_html_list:
        mid = i.xpath("@mid")[0]
        try:
            # 获取封面链接，可能会被微博返回不正常数据
            cover_pic_link = i.xpath("div[1]/img/@src")[0]
            title = i.xpath("div[2]/h3/a/text()")[0]
            link = i.xpath("@href")[0]
        except IndexError as e:
            cover_pic_link = get_article_cover_link_by()
            title = i.xpath("div[1]/h3/text()")[0].replace("发布了头条文章：《", "").replace("》", "")
            link = i.xpath("div[1]/h3/a[2]/@href")[0]
        sq_article_weibo = SQ_Article_Weibo(mid, title, cover_pic_link, link)
        sq_article_weibo.tags = ["睡前消息文章"]
        article_list.append(sq_article_weibo)
    return article_list[::-1]


cookiejar = getNewWeiboCookie()

# article_list = get_article_obj()
# for i in article_list:
#     print(i.__dict__)
