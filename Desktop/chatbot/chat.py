# -*- coding: utf-8 -*-
import json
import random
from operator import eq

from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = "xoxb-506062083639-506732709264-cUd1bdMMT6R2rywc3wpJS8S7"
slack_client_id = "506062083639.508867076838"
slack_client_secret = "5ff0651bcb23f6c276041c916361f080"
slack_verification = "VKAOLXzqaAb0POEyqh9STo93"
sc = SlackClient(slack_token)

#global variables
in_session = False
last_user = ""
deck = []
blackjack = "\n/$$$$$$$  /$$        /$$$$$$   /$$$$$$  /$$   /$$    /$$$$$  /$$$$$$   /$$$$$$  /$$   /$$" \
            + "\n" +  "| $$__  $$| $$       /$$__  $$ /$$__  $$| $$  /$$/   |__  $$ /$$__  $$ /$$__  $$| $$  /$$/"\
            + "\n" +  "| $$  | $$| $$      | $$  | $$| $$  |__/| $$ /$$/       | $$| $$  | $$| $$  |__/| $$ /$$/"\
            + "\n" +  "| $$$$$$$ | $$      | $$$$$$$$| $$      | $$$$$/        | $$| $$$$$$$$| $$      | $$$$$/"\
            + "\n" +  "| $$__  $$| $$      | $$__  $$| $$      | $$  $$   /$$  | $$| $$__  $$| $$      | $$  $$"\
            + "\n" + "| $$  | $$| $$      | $$  | $$| $$    $$| $$|  $$ | $$  | $$| $$  | $$| $$    $$| $$|  $$"\
            + "\n" + "| $$$$$$$/| $$$$$$$$| $$  | $$|  $$$$$$/| $$ |  $$|  $$$$$$/| $$  | $$|  $$$$$$/| $$ |  $$"\
            + "\n" + "|_______/ |________/|__/  |__/ |______/ |__/  |__/ |______/ |__/  |__/ |______/ |__/  |__/"


class Card:
    value = 0
    ace = False

    def __init__(self, value, ace):
        self.value = value
        self.ace = ace


class Player:
    point = 0

    def __init__(self, point):
        self.point = point

    def hit(self, value):
        self.point += value

    def blackjack(self):
        if (self.point == 21):
            return True
        else:
            return False


def game():
    setup = []

    for i in range(0, 10):
        for each in range(2, 15):
            if each <= 10:
                setup.append(Card(each, False))
            elif 11 <= each <= 13:
                    setup.append(Card(10, False))
            elif each == 14:
                    setup.append(Card(11, True))

        random.shuffle(setup)

    return setup


player = None
dealer = None


def conversation(text):
    global in_session
    global player
    global dealer
    global deck
    global blackjack

    text = text.lower()
    temp = text.split(" ")

    if len(temp) < 2:
        response = "TRY *START*"
        return response
    elif len(temp) >= 2 and eq(temp[1], ""):
        response = "TRY *START*"
        return response

    if text.find("start") != -1:
        in_session = True
        deck = game()

        player = Player(deck[0].value)
        del deck[0]

        dealer = Player(deck[0].value)
        del deck[0]

        response = ("*********************GAME START*********************\n"
                    + "PLAYER :     {0}       DEALER :     {1}       ".format(player.point, dealer.point)
                    + "CARDS REMAINING (" + str(len(deck)) + ")")

        if player.point == 21:
            return response + blackjack + "\n\nPLAYER WINS!!!"
        elif dealer.point == 21:
            return response + blackjack + "\n\nDEALER WINS!!!"

        return response

    elif text.find("hit") != -1:
        card = "*******\n" + "** " + str(deck[0].value) + " **\n" + "*******\n"

        if (deck[0].ace):
            card = "*********\n" + "** ACE **\n" + "*********\n"
            if (player.point + deck[0].value > 21):
                player.point += 1
            else:
                player.point += 11
        else:
            player.hit(deck[0].value)

        del deck[0]

        if player.point > 21:
            return (card + "PLAYER :     {0}       DEALER :     {1}       ".format(player.point, dealer.point)
                    + "CARDS REMAINING (" + str(len(deck)) + ")"
                    + "\nBUSTED! DEALER WINS!!!")

        response = card + "PLAYER :     {0}       DEALER :     {1}       ".format(player.point, dealer.point)
        return response + "CARDS REMAINING (" + str(len(deck)) + ")"

    elif text.find("stand") != -1:
        stand_response = ""
        card = ""

        while (dealer.point < 17):
            if (deck[0].ace):
                card = "*********\n" + "** ACE **\n" + "*********\n"
                if (dealer.point + deck[0].value > 21):
                    dealer.point += 1
                else:
                    dealer.point += 11
            else:
                card = "*******\n" + "** " + str(deck[0].value) + " **\n" + "*******\n"
                dealer.hit(deck[0].value)

            del deck[0]

            stand_response += card + "PLAYER :     {0}       DEALER :     {1}       ".format(player.point, dealer.point) + "CARDS REMAINING (" + str(len(deck)) + ")\n"

        if dealer.point > 21: return stand_response + "\nBUSTED! PLAYER WINS!!!"
        elif (dealer.point > player.point): return stand_response + "\nDEALER WINS!!!"
        elif (dealer.point < player.point): return stand_response + "\nPLAYER WINS!!!"
        elif (dealer.point == player.point): return stand_response + "\nTIED!!!"

    else:
        if in_session:
            response = "INVALID INPUT"
        else:
            response = "TRY *START*"
        return response


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])
    global last_user
    global in_session

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"] #채널이름 (앱이 실행되는 채널)
        text = slack_event["event"]["text"] #우리 앱 이름 + 내가 앱이름 다음에 치는 텍스트

        user = slack_event["event"]["user"]

        # user구분 - 이번에 입력한 유저가 원래 게임하던 유저 OR 게임하고있던 유저가 없음(1. 첫게임시작 / 2. 이전에 하던 사용자의 게임 종료 -새유저받기)
        if eq(user, last_user) or eq(last_user, ""):
            last_user = user
            keywords = conversation(text)

            # 여기서 keywords에 WINS나 TIED가 포함된다면,
            if keywords.find("WINS") != -1 or keywords.find("TIED") != -1:
                # last_user를 초기화시켜줍니다.
                last_user = ""
                in_session = False
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                text=keywords
            )
        else:
            keywords = "..."  # 게임이 다른 사용자와 진행중입니다 같은 문구 넣어주면 될 것같아요!
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                text=keywords
            )

        return make_response("App mention message has been sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)