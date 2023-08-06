class Youtube_Video_Bili():
    def __init__(self, vid, title, desc):
        self.vid = vid
        self.title = title
        self.desc = desc  # 简介
        self.link = "https://www.youtube.com/watch?v={vid}".format(vid=vid)
        self.tags = []


def getVideoList(uid):
    url =  "https://www.youtube.com/@{uid}/videos".format(uid=uid)
    import requests
    resp  = requests.get(url)
    print(resp.text)

if __name__ == '__main__':
    getVideoList("user-nc9xp1tb1u")

