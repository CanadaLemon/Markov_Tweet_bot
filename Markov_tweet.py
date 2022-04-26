import json
import re
import sys

import markovify
from janome.tokenizer import Tokenizer
from requests_oauthlib import OAuth1Session

import Twitter_auth_key
import Twitter_info


def main(self1, self2):
    """ツイートする関数

    主にタイムラインからツイートを取得する処理と、ツイートを元にマルコフ連鎖でツイートを生成する処理を行う
    引数はセルフなので省略
    """

    # 認証処理
    CK = Twitter_auth_key.CK
    CS = Twitter_auth_key.CS
    AT = Twitter_auth_key.AT
    ATS = Twitter_auth_key.ATS
    twitter = OAuth1Session(CK, CS, AT, ATS)

    # タイムライン取得
    text_from_timeline = get_timeline(twitter)
    # ツイート用の文章作成
    tweet_to_post = generate_text(text_from_timeline)

    url = "https://api.twitter.com/1.1/statuses/update.json"
    params = {"status": tweet_to_post}
    res_main = twitter.post(url, params=params)

    if res_main.status_code == 200:
        print("---------------------------")
        print("今回のツイート")
        print(tweet_to_post)
        print("---------------------------")

    else:
        print("ツイートを送信する際のレスポンスが正常でないため、処理を終了します")
        print("status_code: %d" % res_main.status_code)
        sys.exit()


def get_timeline(twitter):
    """タイムラインから文章を取得する

    Args:
        twitter (OAuth1Session): Twitterの認証情報

    Returns:
        text_from_timeline (str): タイムラインから取得したツイート
    """

    url = "https://api.twitter.com/1.1/statuses/home_timeline.json"
    params = {
        "count": 100,  # ツイート取得数
        "include_rts": False,  # False→RTを含まない
        "exclude_replies": True,  # True→リプライを含まない
    }
    res_get_timeline = twitter.get(url, params=params)

    if res_get_timeline.status_code == 200:
        text_from_timeline = ""
        timeline = json.loads(res_get_timeline.text)

        # 取得したタイムラインからツイートを取り出し、記号などを除外して文字列に格納する
        for tweet in timeline:
            if (
                tweet["user"]["screen_name"] != Twitter_info.screen_name
            ):  # 自分のツイートを取得対象外にするため、screen_nameにbotのIDを格納しておく
                text = re.sub(
                    r"http\S+|#(\w+)|\^|\n| |[^ぁ-ん ァ-ン 一-龥|^a-zA-Z0-91]",  # 記号などを除外する
                    "",
                    tweet["text"],
                )
                text_from_timeline += text + "。"  # 後に文章を分割する処理を行うため、ツイートの最後に句点をつける

    else:
        print("タイムラインを取得する際のレスポンスが正常でないため、処理を終了します")
        print("status_code: %d" % res_get_timeline.status_code)
        sys.exit()

    print("---------------------------")
    print("今回のタイムライン")
    print(text_from_timeline)
    print("---------------------------")

    return text_from_timeline


def generate_text(text_from_timeline):
    """タイムラインのツイートからマルコフ連鎖で文章を生成する

    Args:
        text_from_timeline (str): タイムラインのツイート

    Returns:
        tweet_to_post (str): ツイートする文章
    """

    splitted_text = split(text_from_timeline)

    sentence = None
    while sentence is None:

        # モデルの生成
        text_model = markovify.NewlineText(
            splitted_text, state_size=2, well_formed=False
        )

        # モデルを基にして文章を生成
        sentence = text_model.make_sentence(tries=10)

    tweet_to_post = "".join(sentence.split())  # 文章を結合する
    tweet_to_post = tweet_to_post.replace("。", "")  # ツイート用に句点を抜く

    return tweet_to_post


def split(text_from_timeline):
    """文章を分割する

    Args:
        text_from_timeline (str): タイムラインから取得したツイート

    Returns:
        splitted_text (str): 分割されたツイート
    """

    # 単語をバラバラに分割し、1つのリストに格納する
    tk = Tokenizer()
    tokenized_result = tk.tokenize(text_from_timeline, wakati=True)
    words_list = list(tokenized_result)

    splitted_text = ""

    # リスト内のバラバラの単語を、文字列として格納していく
    for i, words_list in enumerate(words_list):
        splitted_text += words_list

        if words_list != "。":
            splitted_text += " "
        elif words_list == "。":  # 句点が来た場合、改行する
            splitted_text += "\n"

    return splitted_text
