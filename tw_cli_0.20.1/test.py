# flask-httpauth入れること。
#tweepyは3.10.0。 4以降は仕様が大幅に変わる
import time
import tweepy
import csv

import json
import re
import os
import flask
import urllib.error
import urllib.request
import pytz
import pathlib
import requests
import flask_login

from datetime import datetime,timezone,timedelta
#from flask_httpauth import HTTPDigestAuth
from flask import Flask, render_template, request, redirect,flash
from urllib.request import urlopen
from box import Box



showing_tweet_id = ""
retry_apis=[]
api_num=0
#twitter
CK="1つめトークン"
CS=""
AT=""
AS=""


auth = tweepy.OAuthHandler(CK, CS)
auth.set_access_token(AT, AS)
api = tweepy.API(auth, wait_on_rate_limit=False, wait_on_rate_limit_notify=False)
retry_apis.append(api)

CK="２つめトークン" #API制限かかったらこちらに切り替える。
CS=""
AT=""
AS=""

auth = tweepy.OAuthHandler(CK, CS)
auth.set_access_token(AT, AS)
api = tweepy.API(auth, wait_on_rate_limit=False, wait_on_rate_limit_notify=False)
retry_apis.append(api)

api = retry_apis[0]

my_info = api.me()

#flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Secret key here'

users = {'ユーザー名を入力': {'password': 'パスワードを入力'}}

bearer_token = "bearerトークンをここに。"




login_manager = flask_login.LoginManager()
login_manager.init_app(app)
auth =flask_login

TLmode=1

"""@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None
"""

"""@app.before_request # <- 全てのviewで前処理を行うためのdecoratorを使った関数を用意
@auth.login_required         #<- ここでDigest認証のdecoratorを使う
def before_request():
    pass"""

class User(flask_login.UserMixin):
    pass

def read_setting(key):#configファイルの読み込み
    json_open = open('config.set', 'r+',encoding="utf-8_sig")#json開く
    json_load = json.load(json_open)

    result = json_load[key]
    json_open.close()
    
    return result

def write_setting(key,value):#configファイルの書き込み
    json_open = open('config.set', 'r',encoding="utf-8_sig")#json開く
    json_load = json.load(json_open)
    json_open.close()
    json_open = open('config.set', 'w',encoding="utf-8_sig")#json開く
    print(value)
    json_load[key]=value
    json.dump(json_load, json_open ,ensure_ascii=False)
    json_open.close()
    return

@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return

    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return

    user = User()
    user.id = email

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['password'] == users[email]['password']

    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return render_template("login.html",message="")

    email = flask.request.form['email']
    try:
        if flask.request.form['password'] == users[email]['password']:
            user = User()
            user.id = email
            flask_login.login_user(user)
            print("success")
            
            if read_setting("datasaver"):
                save=1#SAVE中
            else:
                save=2
                
            return render_template('index.html',TLmode=1,datasaver=save)
    except Exception as e:
        print(e)
    
    DIFF_JST_FROM_UTC = 9
    now = datetime.utcnow() + timedelta(hours=DIFF_JST_FROM_UTC)
    IP_addr = request.remote_addr
    with open("login_fail","a") as f:
        write_text = "["+str(now)+"]["+str(IP_addr)+"]  ID: "+str(flask.request.form['email'])+"  PASSWORD: "+str(flask.request.form['password'])+"\n"
        f.write(write_text)
    return render_template("login.html",message="<script>alert('Bad ID or PASSWORD. This incident will be reported.')</script>")




@app.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'

@login_manager.unauthorized_handler
def unauthorized_handler():
    return flask.redirect(flask.url_for('login'))





def error_log(e,place):
    with open('error.log','a')as f:
        
        DIFF_JST_FROM_UTC = 9
        now = datetime.utcnow() + timedelta(hours=DIFF_JST_FROM_UTC)
        text="["+str(now)+"]["+str(place)+"] : "+str(e)+"\n"
        f.write(text)
        print(text)
def change_time_JST(u_time):#2022-07-21 15:55:11
    global api
    try:
        u_time = datetime.strptime(str(u_time), '%Y-%m-%d %H:%M:%S')#replyの一部で、strで渡される所があるので、全て一旦strにしたあと再び返す。
    except:
        u_time = datetime.strptime(str(u_time), '%a %b %d %H:%M:%S %z %Y')#このパターンもある

        
    #イギリスのtimezoneを設定するために再定義する
    utc_time = datetime(u_time.year, u_time.month,u_time.day, u_time.hour,u_time.minute,u_time.second, tzinfo=timezone.utc)
    #タイムゾーンを日本時刻に変換
    jst_time = utc_time.astimezone(pytz.timezone("Asia/Tokyo"))
    # 文字列で返す
    str_time = jst_time.strftime("%Y/%m/%d_%H:%M:%S")
    return str(str_time)


def find(string): #リンク返す
    global api
    # findall() 正規表現に一致する文字列を検索する
    url = re.findall(r'(https?://\S+)', string)
    return url

def key_follower_list():
    global api
    
    if os.path.isfile("./followers.json") and os.path.isfile("./keyuser_tl.json"):
 
        json_file = open("./followers.json","r")
        json_contents = json.load(json_file)
        followers_json_all = json_contents["all"]#不使用だけど、一応ね。
        key_followers = json_contents["key"]

        json_file2 = open("./keyuser_tl.json","r")
        json_contents2 = json.load(json_file2)
        twdic={}
        for key_follower in key_followers:

            old_top = json_contents2[str(key_follower)]["top_id"]
            olds = json_contents2[str(key_follower)]["tweets"]
            
            old_tweets=[]

            tweets = api.user_timeline(int(key_follower), count=100,since_id=old_top,tweet_mode="extended")
            if len(tweets)>0:
                top = tweets[0].id
            else:
                top=old_top

            t_list=[]
            for t in tweets:
                t_list.append(t._json)
            for old_tw in olds:
                t_list.append(old_tw)
            
            twdic[key_follower]=dict(tweets=t_list,top_id=top)

        json_dict = twdic
        json_file = open("./keyuser_tl.json","w")
        json.dump(json_dict,json_file)    

    else:
        followers_ids=[]
        key_followers=[]
        for follower_id in tweepy.Cursor(api.followers_ids, user_id=my_info.id).items():
            followers_ids.append(follower_id)
        for i in range(0, len(followers_ids), 100):
            for user in api.lookup_users(user_ids=followers_ids[i:i+100]):
                if user.protected:
                    key_followers.append(user.id)

        json_dict = dict(key=key_followers,all=followers_ids)
        json_file = open("./followers.json","w")
        json.dump(json_dict,json_file)

        twdic={}
        for key_follower in key_followers:

            tweets = api.user_timeline(key_follower, count=100,tweet_mode="extended")#新規で100個取得
            top = tweets[0].id
            t_list=[]
            for t in tweets:
                t_list.append(t._json)  
            twdic[key_follower]=dict(tweets=t_list,top_id=top)

        
        json_dict = twdic
        json_file = open("./keyuser_tl.json","w")
        json.dump(json_dict,json_file)
    
    
    return key_followers

def nitter_select(file_name):
    #nitterのリスト一覧
    nitter_list =["https://nitter.net/","https://nitter.cz/","https://nitter.ca/","https://nitter.fly.dev/","https://nitter.hu/","https://nitter.kylrth.com/","https://nitter.42l.fr/",
                  "https://nitter.kavin.rocks/","https://nitter.unixfox.eu/","https://nitter.namazso.eu/","https://nitter.moomoo.me/","https://bird.trom.tf/",
                  "https://nitter.grimneko.de/","https://twitter.076.ne.jp/","https://notabird.site/","https://nitter.weiler.rocks/","https://nitter.sethforprivacy.com/","https://nttr.stream/",
                  "https://nitter.cutelab.space/","https://nitter.nl/","https://nitter.bus-hit.me/","https://nitter.esmailelbob.xyz/","https://tw.artemislena.eu/",
                  "https://nitter.dcs0.hu/","https://twitter.dr460nf1r3.org/","https://nitter.privacydev.net/","https://nitter.foss.wtf/",
                  "https://nitter.priv.pw/","https://unofficialbird.com/","https://nitter.projectsegfau.lt/","https://singapore.unofficialbird.com/",
                  "https://canada.unofficialbird.com/","https://nitter.fprivacy.com/","https://twt.funami.tech/","https://india.unofficialbird.com/","https://nederland.unofficialbird.com/",
                  "https://uk.unofficialbird.com/","https://n.l5.ca/","https://nitter.slipfox.xyz/"]
    nitter_length=len(nitter_list)
    ascii_values = 0
    for character in file_name:
        ascii_values = ascii_values + ord(character)
    select_num = ascii_values % nitter_length #文字コード足し合わせたやつで余りを出す。これにより、ひとつの画像には必ず決まったアドレスが当たる。
    return nitter_list[select_num]


def download_img(url, file_name,download=True,original=False):
    global api
    if file_name =="default_profile_normal.png":
        return "/static/default_profile_normal.png"

    
    if download:
        if url.startswith("http://pbs.twimg.com/profile_images/"):
            nitter_url = url.replace("http://","").replace("/","%2F").replace("_normal.jpg","_mini.jpg").replace("_normal.png","_mini.png")
            
            return "https://nitter.fly.dev/pic/"+nitter_url#アイコン画像

        
        elif os.path.isfile("./static/pic/"+str(file_name)):
            return "/static/pic/"+str(file_name)
        else:
            headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0"
            }
            request = urllib.request.Request(url, headers=headers)
            try:
                web_file = urlopen(request)
                data = web_file.read()
                with open("./static/pic/"+str(file_name), mode='wb') as local_file:
                    local_file.write(data)
            except Exception as e:
                error_log(e,"download_img")
                
            return "/static/pic/"+str(file_name)
    else:
        #nitter_server_url = nitter_select(file_name)
        if read_setting("datasaver"):#データセーバーがオンなら低画質読み込み。ただし個々のツイ除く
            if original:
                pass
            else:
                return "https://nitter.fly.dev/"+"pic/media%2F"+str(file_name)+":small"
        
        return "https://nitter.fly.dev/"+"pic/orig/media%2F"+str(file_name)
    

def get_reply(tweet_id,name,get_count=None,single=False):
    global api

    if get_count is None:
        get_count=50
    replies=[]

    
    key_followers_ids = key_follower_list()
    for key_follower_id in key_followers_ids:   #通常の検索では鍵垢がひっかからないので、フォロバされてる鍵垢に限り、この条件分岐でリプを取得。
        json_file = open("./keyuser_tl.json","r")
        data = json.load(json_file)
        ts = data[str(key_follower_id)]["tweets"]#リスト形式でたくさんtweet入ってる。

        tweets=[]
        for tweet in ts:#一気にobjectにするとエラー吐くから１ずつ。
                tweet = Box(tweet)
                tweets.append(tweet)

        for tweet in tweets:
            if hasattr(tweet,"full_text"):
                tweet.text = tweet.full_text
            
            if hasattr(tweet, 'in_reply_to_status_id_str'):
                if (tweet.in_reply_to_status_id_str==str(tweet_id)):
                    replies.append(tweet)
                    if single:
                        break

        
        
        
    for tweet in tweepy.Cursor(api.search,q='to:'+name, result_type='mixed',tweet_mode="extended",timeout=999999,count = 50).items(int(get_count)):
        if hasattr(tweet,"full_text"):
            tweet.text = tweet.full_text

        if hasattr(tweet, 'in_reply_to_status_id_str'):
            if (tweet.in_reply_to_status_id_str==str(tweet_id)):
                replies.append(tweet)
                if single:
                    break
    return replies

def fav_rt_bottun(tweet,now_page):
    global api
    result =""
    if hasattr(tweet,'favorited'):#いいね Nullableらしいからこうする。
        if tweet.favorited:
            result = result +"&emsp;"*1+"<img id='_unfav/"+tweet.id_str+"' src='/static/faved.png' alt='"+tweet.id_str+"' onclick='unfav_click(\"_unfav/"+tweet.id_str+"\")'></img>"
        else:
            result = result +"&emsp;"*1+"<img id='_fav/"+tweet.id_str+"' src='/static/fav.png' alt='"+tweet.id_str+"' onclick='fav_click(\"_fav/"+tweet.id_str+"\")'></img>"
    else:
        result = result +"&emsp;"*1+"<img id='_fav/"+tweet.id_str+"' src='/static/fav.png' alt='"+tweet.id_str+"' onclick='fav_click(\"_fav/"+tweet.id_str+"\")'></img>"

    if not tweet.user.protected:#鍵垢にはリツイート表示しない。
        if tweet.retweeted:#リツイート
            result = result +"&emsp;"*1+"<img id='_unrt/"+tweet.id_str+"' src='/static/retweeted.png' alt='"+tweet.id_str+"' onclick='unrt_click(\"_unrt/"+tweet.id_str+"\")'></img>"
        else:
            result = result +"&emsp;"*1+"<img id='_rt/"+tweet.id_str+"' src='/static/retweet.png' alt='"+tweet.id_str+"' onclick='rt_click(\"_rt/"+tweet.id_str+"\")'></img>"
    return result 

def tweet_process(tweet,mode="normal",original=False):
        global api
        result="<div id="+tweet.id_str+"></div>"
        

        if hasattr(tweet,"full_text"):
            tweet.text = tweet.full_text

        prof_url = tweet.user.profile_image_url
        prof_name = prof_url[prof_url.rfind('/') + 1:]

        prof_file = download_img(prof_url,prof_name)

        if mode=="reply":
            result = result+'<a href="/user/'+tweet.user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><img src='+prof_file+' width=45px align="left"><font size="4"><b>'+tweet.user.name+'</b></font></a><br><font size="1" color="#333333">@'+tweet.user.screen_name+'</font><br><div class="reply-container"><div class="tatesen"></div><div class="reply-box"><br><a href=/tweet/'+str(tweet.id)+' style="text-decoration: none; color:#000000; word-break: break-all;">'+str(tweet.text).replace("\n","<br>")+'<br><br></a>'

        else:
            result = result+'<a href="/user/'+tweet.user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><img src='+prof_file+' width=45px align="left"><font size="4"><b>'+tweet.user.name+'</b></font></a><br><font size="1" color="#333333">@'+tweet.user.screen_name+'</font><br><br><a href=/tweet/'+str(tweet.id)+' style="text-decoration: none; color:#000000; word-break: break-all;">'+str(tweet.text).replace("\n","<br>")+'<br><br></a>'

        #画像ツイなどにあるhttps://t.coみたいなURLが邪魔なので取り除く

        tcourls = find(str(tweet.text))
        if 'tcourls':
            for url_tco in tcourls:
                result = result.replace(url_tco,"")

        #ツイートがURLを含むなら、aタグで囲む
        if 'urls' in tweet.entities:
            for twurl in tweet.entities['urls']:
                tw_link = twurl['expanded_url']
                if tw_link.startswith('https://twitter.com/') and ('/i/' not in tw_link):#引用の処理
                    moto_tweet_id = tw_link[tw_link.rfind('/') + 1:]
                    moto_tweet_id = re.findall(r"\d+", moto_tweet_id)[0]#リンクの後ろに?とかついてても対応できるように。
                    result = result + '<div style="padding: 10px; margin-bottom: 10px; border: 1px solid #333333;">'
                    try:
                    
                        moto_tweet = api.get_status(int(moto_tweet_id),tweet_mode="extended")#取得
                        if hasattr(moto_tweet,"full_text"):
                            moto_tweet.text = moto_tweet.full_text
                        
                        moto_prof_url = moto_tweet.user.profile_image_url
                        moto_prof_name = moto_prof_url[moto_prof_url.rfind('/') + 1:]
                        moto_prof_file = download_img(moto_prof_url,moto_prof_name)
                        
                        result = result+'<a href="/user/'+moto_tweet.user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><img src='+moto_prof_file+' width=25px align="left"><font size="3"><b>'+moto_tweet.user.name+'</b></font></a><br><br><br><a href=/tweet/'+str(moto_tweet.id)+' style="text-decoration: none; color:#000000; word-break: break-all;">'+str(moto_tweet.text)+'<br></a>'
                        tcourls = find(str(moto_tweet.text))
                        if 'tcourls':
                            for url_tco in tcourls:
                                result = result.replace(url_tco,"")#URLは全部抹消
                        if 'media' in moto_tweet.entities:
                                for media in moto_tweet.extended_entities['media']:#これは、複数枚写真取得してるわけではない！！！for内は2行で正しい！！
                                    mediatype = media["type"]
                                    media_obj=media
                                if mediatype=="video":
                                    media_url  = [variant['url'] for variant in media_obj['video_info']['variants'] if variant['content_type'] == 'video/mp4'][0]
                                    media_name = media_url[media_url.rfind('/') + 1:media_url.rfind('?')]
                                    
                                    local_link = download_img(media_url,media_name,download=True,original=original)
                                    result=result+"<video controls src="+local_link+" width=400px></video>"
                                    
                                elif mediatype=="animated_gif":
                                    media_url = media['media_url']
                                    media_name = media_url[media_url.rfind('/') + 1:]#media_urlのreplace前にこれを置け！
                                    local_link = download_img(media_url,media_name,original=original)
                                    result=result+"<img src='"+local_link+"' width=200px>"
                                    
                                else:
                                    for media in moto_tweet.extended_entities['media']:
                                        media_url = media['media_url']
                                        media_name = media_url[media_url.rfind('/') + 1:]#media_urlのreplace前にこれを置け！
                                        

                                        #media_url = media_url.replace(".jpg","?format=jpg&name=4096x4096").replace(".png","?format=png&name=4096x4096")
                                        #local_link = download_img(media_url,media_name,download=True,original=original)

                                        local_link = download_img(media_url,media_name,download=False,original=original)

                                        result=result+"<img src='"+local_link+"' width=200px>"
                        
                    except Exception as e:
                        error_log(e,"tweet_process")
                        try:
                            result = result + "<font color='#ff0000'>"+e.args[0][0]['message']+"</font>"
                        except:
                            result = result + "<font color='#ff0000'>Failed to load</font>"

                        
                    result = result+'</div>'
                    
                else:
                    
                    link_url = twurl['expanded_url']
                    result=result+"<a href="+link_url+" style='word-break: break-all;'>"+link_url+"</a><br>"

        #画像があるならimgタグで貼る。        
        if 'media' in tweet.entities:
                for media in tweet.extended_entities['media']:#これは、複数枚写真取得してるわけではない！！！for内は2行で正しい！！
                    mediatype = media["type"]
                    media_obj=media
                if mediatype=="video":
                    media_url  = [variant['url'] for variant in media_obj['video_info']['variants'] if variant['content_type'] == 'video/mp4'][0]
                    media_name = media_url[media_url.rfind('/') + 1:media_url.rfind('?')]
                    local_link = download_img(media_url,media_name,original=original)
                    result=result+"<video controls src='"+local_link+"' width=400px></video>"
                    
                elif mediatype=="animated_gif":
                    media_url = media['media_url']
                    media_name = media_url[media_url.rfind('/') + 1:]#media_urlのreplace前にこれを置け！
                    media_url = media_url.replace(".jpg","?format=jpg&name=4096x4096").replace(".png","?format=png&name=4096x4096")
                    
                    local_link = download_img(media_url,media_name,original=original)
                    result=result+"<img src='"+local_link+"' width=200px>"
                    
                else:
                    for media in tweet.extended_entities['media']:#複数枚の写真取得
                        media_url = media['media_url']
                        media_name = media_url[media_url.rfind('/') + 1:]#media_urlのreplace前にこれを置け！

                        #media_url = media_url.replace(".jpg","?format=jpg&name=4096x4096").replace(".png","?format=png&name=4096x4096")
                        #local_link = download_img(media_url,media_name,download=True,original=original)
                        local_link = download_img(media_url,media_name,download=False,original=original)


                        result=result+"<img src='"+local_link+"' width=200px>"
        if mode=="reply":
            result=result+"</div></div>"
        else:
            pass
        
        return result


def get_one_tweet(id,deep=False):
    global api
    global showing_tweet
    result=""
    tweet = api.get_status(int(id),tweet_mode="extended")#取得
    showing_tweet=tweet
    #while hasattr(tweet, 'in_reply_to_status_id_str'):
    #     tweet = api.get_status(tweet.in_reply_to_status_id,tweet_mode="extended")#リプライ元のツイート取得
         
    if hasattr(tweet,"full_text"):
        tweet.text = tweet.full_text
                        
    result = result + tweet_process(tweet,original=True)
    #いいねRT数
    if tweet.user.protected:
        result=result+"<br><u><font size='2'>"+str(tweet.favorite_count)+" 件のいいね</font></u><br><font color='#009900' size='2' style='backglound-color: #cccccc;'>https://twitter.com/"+tweet.user.screen_name+"/status/"+str(tweet.id)+"</font>"

    else:
        result=result+"<br><u><font size='2'><a href='/rtuser/"+str(tweet.id)+"'>"+str(tweet.retweet_count)+" 件のリツイート</a><br><a href='/favuser/"+str(tweet.id)+"'>"+str(tweet.favorite_count)+" 件のいいね</a></font></u><br><font color='#009900' size='2' style='backglound-color: #cccccc;'>https://twitter.com/"+tweet.user.screen_name+"/status/"+str(tweet.id)+"</font>"


    #最終処理
    result=result + "<font size='1' color='#888888'><br>"+change_time_JST(tweet.created_at)+"</font><br>"

    result = result+fav_rt_bottun(tweet,"/tweet/"+tweet.id_str)+"<hr>"

        
    result = result + "<form action='/send_rep/@"+tweet.user.screen_name+"/"+str(tweet.id)+"' method='POST' enctype='multipart/form-data'><textarea class='reply-textlines' name ='reply' placeholder='返信をツイート'></textarea><input type='file' name='reply_file' multiple='multiple' accept='image/*'></input><div align='right'><input type='submit' value='リプライ' onclick='DisableButton(this);'></div><br></form><hr><br>"

    if hasattr(tweet,"in_reply_to_status_id"):#もしもこれがツイートの途中なら
        moto_tweet = tweet
        result ="<hr><hr>"+result
        #try:
        if True:
            while hasattr(tweet,"in_reply_to_status_id"):

                try:
                    if tweet.in_reply_to_status_id is None:
                        break
                    tweet = api.get_status(tweet.in_reply_to_status_id,tweet_mode="extended")#大元のツイートまで1個ずつ取得

                    if hasattr(tweet,"full_text"):
                        tweet.text = tweet.full_text
                    result = tweet_process(tweet,mode="reply",original=True) +fav_rt_bottun(tweet,"/tweet/"+tweet.id_str)+"<br>"+ result
                    
                except Exception as e:
                    error_log(e,"get_one_tweet")
                    result = "<font color='#ff0000'>取得失敗! やーいツイ廃ｗｗｗｗｗ</font>"+str(e)+"<hr>" + result
                    break
        '''except:
            result = "省略...<br>" + result'''
        
        tweet = moto_tweet
            
       
    
    return result
def get_user_tw(Account,mode):#mode: fav, picture , rep , noRT , onlyRT , normal
    global api
    global my_info
    
    result=""
    try:
        twuser = api.get_user(Account)
    except:
        return ""
    if  (twuser.protected and twuser.following) or twuser.protected==False or my_info.id==twuser.id:
        if mode=="fav":
            tweets = api.favorites(screen_name=Account, count=100,tweet_mode="extended")
        else:
            tweets = api.user_timeline(Account, count=100,tweet_mode="extended")

    else:
        pass
    
        

    #プロフ情報書き込み

    if not hasattr(twuser,"profile_image_url"):#初期アイコンなら
        local_prof_link ="default_profile_normal.png"
    else:
        prof_url = twuser.profile_image_url
        prof_name = prof_url[prof_url.rfind('/') + 1:]
        prof_file = download_img(prof_url,prof_name,original=True)
    if not hasattr(twuser,"profile_banner_url"):#トプ画未設定なら
        banner_file="/static/banner.png"
    else:
        banner_url = twuser.profile_banner_url
        banner_name = banner_url[banner_url.rfind('/') + 1:]
        banner_file = download_img(banner_url,banner_name,original=True)
        
    
    result = "<div style='padding: 10px; margin-bottom: 10px; border: 5px double #333333;'><img src="+banner_file+" width=100%><br><img src='"+prof_file+"' width=100px align='left' alt=\"NO BANNER\" onerror='this.onerror = null; this.src=\"\";'><font size='6'><b>"+twuser.name+"</b></font>"

    if twuser.following:        
        result = result + "<a href='/unfollow/"+str(twuser.id)+"' ><img src='/static/following.png' height=40px align='right'></a><br><font size='3' color='#333333'>@"+twuser.screen_name+"</font><br>"
    elif my_info.id==twuser.id:
        result = result + "<br><font size='3' color='#333333'>@"+twuser.screen_name+"</font><br>"#自分の垢のとき。将来的に設定ボタンおいてもいいかも。
    else:
        result = result + "<a href='/follow/"+str(twuser.id)+"' ><img src='/static/follow.png' height=40px align='right'></a><br><font size='3' color='#333333'>@"+twuser.screen_name+"</font><br>"
        
    if hasattr(twuser,"description"):
        result = result + "<br><br><div style='padding: 10px; margin-bottom: 10px; border: 1px dotted #333333; border-radius: 5px;'>"+twuser.description+"</div>"
    else:
        result=result+"<br><br>"
    result = result + "<br>ID: "+twuser.id_str+"<br><u><a href='/followings/"+twuser.id_str+"' style='text-decoration: none; color:#000000;'>"+str(twuser.friends_count)+"　フォロー中<br></a><a href='/followers/"+twuser.id_str+"' style='text-decoration: none; color:#000000;'>"+str(twuser.followers_count)+"　フォロワー</a></u><br>"+str(twuser.listed_count)+"　個のリストに加入<br>"+str(twuser.favourites_count)+"　件のいいね<br>"+str(twuser.statuses_count)+"　件のツイート<br>垢作成日："+change_time_JST(twuser.created_at)+"<br><br></div>"
    

    #ここまでプロフ情報
    if  (twuser.protected and twuser.following) or twuser.protected==False or my_info.id==twuser.id:
        
        #表示条件指定のりんく
        result = result + '<div class ="flex-container"><div class ="flex-item"><a href=/user/'+twuser.screen_name+'/normal style="text-decoration: none; color:#000000;">|ツイート|</a></div><div class ="flex-item"><a href=/user/'+twuser.screen_name+'/noRT style="text-decoration: none; color:#000000;">|RT除外|</a></div><div class ="flex-item"><a href=/user/'+twuser.screen_name+'/onlyRT style="text-decoration: none; color:#000000;">|RTのみ|</a></div></div>'
        result = result + '<div class ="flex-container"><div class ="flex-item"><a href=/user/'+twuser.screen_name+'/rep style="text-decoration: none; color:#000000;">|返信含|</a></div><div class ="flex-item"><a href=/user/'+twuser.screen_name+'/picture style="text-decoration: none; color:#000000;">|画像|</a></div><div class ="flex-item"><a href=/user/'+twuser.screen_name+'/fav style="text-decoration: none; color:#000000;">|いいね|</a></div></div><hr>'
        if mode=="picture":#メディアツイのみ抽出するモードなら
            result = result.replace("|画像|","<b>|画像|</b>")
            
        elif mode == "noRT":#リツイート除外
            result = result.replace("|RT除外|","<b>|RT除外|</b>")

        elif mode == "normal":#ノーマル（リプ除外）
            result = result.replace("|ツイート|","<b>|ツイート|</b>")

        elif mode == "onlyRT":#リツイートのみ
            result = result.replace("|RTのみ|","<b>|RTのみ|</b>")

        elif mode == "fav":
            result = result.replace("|いいね|","<b>|いいね|</b>")

        elif mode == "rep":
            result = result.replace("|返信含|","<b>|返信含|</b>")
        

        #ツイート本文
        for tweet in tweets:
            if hasattr(tweet,"full_text"):
                tweet.text = tweet.full_text
            if mode=="picture":#メディアツイのみ抽出するモードなら
                if 'media' not in tweet.entities:#画像ツイ含まれてないならパスさせる。RTも除外。
                    continue
                if "RT @" in tweet.text[0:4]:
                    continue
            elif mode == "noRT":#リツイート除外
                if "RT @" in tweet.text[0:4]:
                    continue
            elif mode == "normal":#ノーマル（リプ除外）
                if "@" in tweet.text[0:1]:
                    continue
            elif mode== "onlyRT":#リツイートのみ
                if not "RT @" in tweet.text[0:4]:
                    continue

                
            #アイコン、ユーザー名、本文など。RTかどうかで分岐
            
            if hasattr(tweet, "retweeted_status"):#RTのとき
                result = result+'<a href="/user/'+tweet.retweeted_status.user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><font size="2">'+tweet.user.name+'さんがリツイート</font><br>'+ tweet_process(tweet.retweeted_status)
                #最終処理
                result=result+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.retweeted_status.created_at)+"</font><br>"+fav_rt_bottun(tweet,"/user/"+tweet.retweeted_status.user.screen_name+"/normal")+"<br><hr>"
            else:
                result = result + tweet_process(tweet)
                #最終処理
                result=result+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.created_at)+"</font><br>"+fav_rt_bottun(tweet,"/user/"+tweet.user.screen_name+"/normal")+"<br><hr>"


    else:
        result = result+"鍵垢のため表示できません。"
    return result



def get_serch_tw(query,mode,count=60,since_id=None):
    global api
    result=""
    res_d={}
    picture = False
    dict_res=False
    
    if mode=="picture":
        picture=True
        mode="mixed"
    elif mode=="notice":
        dict_res=True
        mode="recent"

        
    tweets=[]
    try:
        if since_id is None:
            tweets= api.search(q=query, result_type=mode,tweet_mode="extended", timeout=999999,count=count)
        else:
            tweets= api.search(q=query, result_type=mode,tweet_mode="extended", timeout=999999,count=count,since_id=since_id)

    except Exception as e:
        error_log(e,"get_serch_tw")
        if dict_res:
            return "error"
        else:
            return "<font color='#ff0000'>取得失敗! やーいツイ廃ｗｗｗｗｗ<br>"+str(e)+"</font>"
    for tweet in tweets:
        if hasattr(tweet,"full_text"):
            tweet.text = tweet.full_text
        if not hasattr(tweet,"retweeted_status"):
   
            if picture:#メディアツイのみ抽出するモードがTrueなら
                if 'media' not in tweet.entities:#画像ツイ含まれてないならパスさせる。
                    continue
                    
            result = result + tweet_process(tweet)

            #最終処理
            result = result+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.created_at)+"</font><br>"+fav_rt_bottun(tweet,"nothing")+"<br><hr>"#ここのリダイレクト先URLは適当。

            if dict_res:

                res_d[tweet.id_str]=tweet_process(tweet)+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.created_at)+"</font><br>"+fav_rt_bottun(tweet,"nothing")+"<br><hr>"
        else:
            if dict_res:#noticeのときだけ、RTも含める。

                if tweet.retweeted_status.user.id==my_info.id:
                        
                    prof_url = tweet.user.profile_image_url
                    prof_name = prof_url[prof_url.rfind('/') + 1:]
                    prof_file = download_img(prof_url,prof_name)
                        
                    res_d[tweet.id_str] = '<br><a href="/user/'+tweet.user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><img src='+prof_file+' width=30px align="left"><b>'+tweet.user.name+'</b></a>さんがリツイートしました💔<br><br><font size="2" color="#888888"><a href=/tweet/'+str(tweet.retweeted_status.id)+' style="text-decoration: none; color:#000000; word-break: break-all;">'+str(tweet.text).replace("\n","<br>").replace("RT @"+my_info.screen_name+":","")+'<br></a></font><hr>'

                    #ここ変えたら、notice内の鍵垢のやつも変えてね
    if dict_res:
        return res_d
    else:
        return result


"""def get_timeline():
    result=""
    if os.path.isfile("./timeline.json"):
        json_file = open("./timeline.json","r")
        json_contents = json.load(json_file)
        top_tweet = json_contents["top_tweet"]
        json_result = json_contents["result"]


    else:
        top_tweet = ""
        json_result=""

    if top_tweet != "":       #timeline.jsonが存在しているとき。
        print("json-exist!")
        print("top-tweet = "+str(top_tweet))
        
        try:
            tweets = api.home_timeline(since_id=int(top_tweet),count=200,tweet_mode="extended")
            new_top_tweet=tweets[0].id
            print("="*40)
            print(len(tweets))
        except Exception as e:
            result ="<font color='#ff0000'>取得失敗"+str(e)+"</font><br><hr>"+json_result
            return result

        tl_page = 1
        while len(tweets)>0:


            for tweet in tweets:
                try:
                    if hasattr(tweet, "retweeted_status"):#RTのとき
                        result = result+'<a href="/user/'+tweet.retweeted_status.user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><font size="2">'+tweet.user.name+'さんがリツイート</font><br>'+ tweet_process(tweet.retweeted_status)
                        #最終処理
                        result=result+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.retweeted_status.created_at)+"</font><br>"+fav_rt_bottun(tweet.retweeted_status,"/center2.html")+"<br><hr>"
                    else:
                        result = result + tweet_process(tweet)
                        #最終処理
                        result=result+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.created_at)+"</font><br>"+fav_rt_bottun(tweet,"/center2.html")+"<br><hr>"
                except Exception as e:
                    result =result +"<font color='#ff0000'>取得失敗"+str(e)+"</font><br><hr>"
            
            print("*"*40)
            tl_page = tl_page + 1
            print(tl_page)
            try:
                tweets = api.home_timeline(since_id=int(top_tweet),count=200,tweet_mode="extended",page=tl_page)
                print("tweets-len = "+str(len(tweets)))
                if len(tweets)==0:
                    break
                print("="*40)
                print(len(tweets))
            except Exception as e:
                result =result +"<font color='#ff0000'>取得失敗"+str(e)+"</font><br><hr>"
                break


        print("@"*40)
        try:
            top_tweet = new_top_tweet
        except:
            pass
        result = result + json_result
        

            
    else:           #timeline.jsonが存在しないなら、まとめて100件取ってきていつも通り処理する。
        try:
            tweets = api.home_timeline(count=100,tweet_mode="extended",page=1)
        except Exception as e:
            result ="<font color='#ff0000'>取得失敗"+str(e)+"</font><br><hr>"+result
            return result
        for tweet in tweets:
            if hasattr(tweet,"full_text"):
                tweet.text = tweet.full_text
            if hasattr(tweet, "retweeted_status"):#RTのとき
                result = result+'<a href="/user/'+tweet.retweeted_status.user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><font size="2">'+tweet.user.name+'さんがリツイート</font><br>'+ tweet_process(tweet.retweeted_status)
                #最終処理
                result=result+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.retweeted_status.created_at)+"</font><br>"+fav_rt_bottun(tweet.retweeted_status,"/center2.html")+"<br><hr>"
            else:
                result = result + tweet_process(tweet)
                #最終処理
                result=result+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.created_at)+"</font><br>"+fav_rt_bottun(tweet,"/center2.html")+"<br><hr>"
        top_tweet = tweets[0].id

    json_dict = dict(top_tweet=top_tweet,result=result)
    json_file = open("./timeline.json","w")
    json.dump(json_dict,json_file)
    print("write!"+str(top_tweet))
    return result"""


def get_timeline(add=False,new=False):
    global api
    result=""
    
    if add:#追加読み込みの時
        json_file = open("./tl_tweets.json","r")
        data = json.load(json_file)
        json_bottom_tweet = data["bottom_tweet"]
        json_top_tweet = data["top_tweet"]
        ##
        
        loop_count = 0
        while True:
            try:
                tweets = api.home_timeline(max_id=int(json_bottom_tweet)-1,count=200,tweet_mode="extended")
                break
            except Exception as e:
                loop_count=loop_count+1
                if len(retry_apis) <= loop_count:
                    error_log(e,"get_timeline")
                    result ="<font color='#ff0000'>取得失敗! やーいツイ廃ｗｗｗｗｗ"+str(e)+"</font><br><hr>"

                    return str(e)
                else:
                    print(str(e))
                    api = retry_apis[loop_count]
                    print("changed api key")
        ##
        top_tweet = json_top_tweet

    elif new:
        json_file = open("./tl_tweets.json","r")
        data = json.load(json_file)
        json_bottom_tweet = data["bottom_tweet"]
        json_top_tweet = data["top_tweet"]
        ##
        
        loop_count = 0
        while True:
            try:
                tweets = api.home_timeline(since_id=int(json_top_tweet),count=200,tweet_mode="extended")
                break
            except Exception as e:
                loop_count=loop_count+1
                if len(retry_apis) <= loop_count:
                    error_log(e,"get_timeline")
                    result ="<font color='#ff0000'>取得失敗! やーいツイ廃ｗｗｗｗｗ"+str(e)+"</font><br><hr>"
                    print("追加ロード時のエラー："+str(e))
                    return str(e)
                else:
                    print(str(e))
                    api = retry_apis[loop_count]
                    print("changed api key")
        ##
        try:
            top_tweet = tweets[0].id
        except:
            top_tweet = ""
                    
    else:
        ##
        
        loop_count = 0
        while True:
            try:
                tweets = api.home_timeline(count=50,tweet_mode="extended")
                break
            except Exception as e:
                loop_count=loop_count+1
                if len(retry_apis) <= loop_count:
                    error_log(e,"get_timeline")
                    result ="<font color='#ff0000'>取得失敗! やーいツイ廃ｗｗｗｗｗ"+str(e)+"</font><br><hr>"
                    print("追加ロード時のエラー："+str(e))
                    return str(e)
                else:
                    print(str(e))
                    api = retry_apis[loop_count]
                    print("changed api key")
        ##
        top_tweet = tweets[0].id









    for tweet in tweets:
        try:
            if hasattr(tweet, "retweeted_status"):#RTのとき
                result = result+'<a href="/user/'+tweet.retweeted_status.user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><font size="2">'+tweet.user.name+'さんがリツイート</font><br>'+ tweet_process(tweet.retweeted_status)
                #最終処理
                result=result+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.retweeted_status.created_at)+"</font><br>"+fav_rt_bottun(tweet.retweeted_status,"/center2.html")+"<br><hr>"
            else:
                result = result + tweet_process(tweet)
                #最終処理
                result=result+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.created_at)+"</font><br>"+fav_rt_bottun(tweet,"/center2.html")+"<br><hr>"
        except Exception as e:
            error_log(e,"get_timeline")
            result =result +"<font color='#ff0000'>取得失敗! やーいツイ廃ｗｗｗｗｗ"+str(e)+"</font><br><hr>"

    try:
        bottom_tweet = tweets[-1].id
    except:
        bottom_tweet = ""
    if bottom_tweet !="" or top_tweet !="":
        json_dict = dict(bottom_tweet=bottom_tweet,top_tweet=top_tweet)
        json_file = open("./tl_tweets.json","w")
        json.dump(json_dict,json_file)
        print("write!")
    else:
        print("not write!")
    limit = api.rate_limit_status()
    print("TL ratelimit source:"+str(limit["resources"]["statuses"]["/statuses/home_timeline"]["remaining"]))

    return result
        






















# ホームページ

@app.route('/gonotice')
@auth.login_required      #それぞれに、これ必須。ないと誰でも見れてしまう。

def notice_bottun():
    global api
    global TLmode
    TLmode=4
    if read_setting("datasaver"):
        save=1#SAVE中
    else:
        save=2
                
    return render_template('index.html',TLmode=4,datasaver=save)


@app.route('/')
@auth.login_required      #それぞれに、これ必須。ないと誰でも見れてしまう。

def index():
    global api
    global TLmode
    print(TLmode)
    print()
    if read_setting("datasaver"):
        save=1#SAVE中
    else:
        save=2
                
    return render_template('index.html',TLmode=TLmode,datasaver=save)



"""@app.route('/left.html')

def show_l1():
    return flask.send_file('left.html')


@app.route('/right1.html')

def show_r1():
    return flask.send_file('right1.html')"""
@app.route('/tl_load_first')
@auth.login_required
def tl_load_first():
    global api
    global allow_load_TL
    """if allow_load_TL:

        allow_load_TL=False #なぜか二回読むので強引にこうするしかない
        return 
    else:
        print("#"*80)
        result = get_timeline()
        return result"""
    result = get_timeline()
    return result
    
@app.route('/tl_load_add')
@auth.login_required
def tl_load_add():
    global api
    
    result = get_timeline(add=True)
    print("add_load")
    return result

@app.route('/tl_load_new')
@auth.login_required
def tl_load_new():
    global api
    
    result = get_timeline(new=True)
    print("new_load")
    return result

@app.route('/reply_load_first')
@auth.login_required
def reply_load_first():
    global showing_tweet_id
    res = get_one_tweet(showing_tweet_id)
    return res

@app.route('/reply_load_add')
@auth.login_required
def reply_load_add():
    global showing_tweet
    result=""
    #自身より下の階層のリプライの取得
    try:
        replies = get_reply( str(showing_tweet.id),showing_tweet.user.screen_name)
    except:
        result=result +"<font color='#ff0000'>取得失敗! やーいツイ廃ｗｗｗｗｗ</font><hr>"
        return result

    
    count=0
    for reply in replies:
        try:
            if count>3:#同じ階層にあるリプが多すぎる場合
                result=result+"<hr><br>省略..."
                break
            reply_to_reply = get_reply(str(reply.id),reply.user.screen_name)


            
            try:#リプライ深くあさるモード
                if len(reply_to_reply)>0:
                    result = result + tweet_process(reply,mode="reply")
                    result = result+fav_rt_bottun(reply,"nothing")+"<br>"
                    while True:
                        if len(reply_to_reply)==0:#これ以上深いところにリプがないなら
                            
                            break
                        else:

                            if len(reply_to_reply)>1:
                                result=result+"<font color='#0000ff' size='2'>他のリプライが"+str(len(reply_to_reply)-1)+"件<br></font>"
                            
                            reply_old = reply_to_reply[0]

                            reply_to_reply = get_reply(str(reply_to_reply[0].id),reply_to_reply[0].user.screen_name)
                            if len(reply_to_reply)==0:
                                result = result + tweet_process(reply_old)
                            else:
                                result = result + tweet_process(reply_old,mode="reply")
                            result = result+fav_rt_bottun(reply_old,"nothing")+"<br>"

                else:
                    result = result + tweet_process(reply_to_reply[0])
                    result = result+fav_rt_bottun(reply_to_reply[0],"nothing")+"<br>"


            except Exception as e:
                
                if len(reply_to_reply)>0:
                    result = result + tweet_process(reply,mode="reply")
                    result = result+fav_rt_bottun(reply,"nothing")+"<br>"
                    if count==0:
                        to_2reply =get_reply(str(reply_to_reply[0].id),reply_to_reply[0].user.screen_name)
                        if len(to_2reply)>0:
                            result = result + tweet_process(reply_to_reply[0],mode="reply") +"<br><a href='/deeptweet/"+str(tweet.id)+"' style='text-decoration: none; color:#0000ff;'><u>追加読み込み...</u></a>"
                        else:
                            result = result + tweet_process(reply_to_reply[0])
                        result = result+fav_rt_bottun(reply_to_reply[0],"nothing この引数つかってないから消してもいいよ")+"<br>"
                
                
                else:
                    result = result + tweet_process(reply)
                    result = result+fav_rt_bottun(reply,"nothing")+"<br>"
        except Exception as e:
            error_log(e,"reply_load_add")
            result = result+"<font color='#ff0000'>取得失敗! やーいツイ廃ｗｗｗｗｗ"+str(e)+"</font>"

        #re最終処理
        
        #result=result+"<font size='1' color='#888888'>"+change_time_JST(reply.created_at)+"</font><br><hr>"

        result=result+"<br><hr>"#リプには日付時刻いらないかな
        count=count+1
    return result
    

@app.route('/ver')
@auth.login_required
def show_ver():
    with open("version.txt","r",encoding="utf_8") as f:
        version_text="<font size=1>"+f.read().replace("\n","<br>")+"</font>"
    return version_text

@app.route('/center2.html')
@auth.login_required      #それぞれに、これ必須。ないと誰でも見れてしまう。

def show_c1():
    
    global api
    global TLmode
    global serch_txt
    global user_txt
    #global allow_load_TL
    #allow_load_TL=True #なぜか二回読むので強引にこうするしかない
    #text = request.form.get('search')
    print(TLmode)
    if TLmode==1:#通常のタイムライン。

        return flask.render_template('timeline.html')
    
    if TLmode==2:#フリーワード検索
        try:
            tweets = '<div class ="flex-container"><div class ="flex-item"><a href=/search/mixed style="text-decoration: none; color:#000000;"><b>ー話題ー</b></a></div><div class ="flex-item"><a href=/search/recent style="text-decoration: none; color:#000000;">ー最新ー</a></div>'
            tweets= tweets +'<div class ="flex-item"><a href=/search/picture style="text-decoration: none; color:#000000;">ー画像ー</a></div></div><hr>'
            tweets = tweets + get_serch_tw(serch_txt,mode="mixed")
        except Exception as e:
            error_log(e,"show_c1(TLmode=2)")
            try:
                tweets ="<h1>Error Code: "+str(e.args[0][0]['code'])+"</h1><p><h2>"+e.args[0][0]['message']+"</h2>"
            except:
                tweets ="<font color='#ff0000'>検索に失敗しました。APIの制限の場合は、最大15分お待ちを。</font>"
        return flask.render_template('center2.html' ,tweet=tweets)
    if TLmode==3:#ユーザー検索
        try:
            tweets = get_user_tw(user_txt,"normal")
        except Exception as e:
            error_log(e,"show_c1(TLmode=3)")
            try:
                tweets ="<h1>Error Code: "+str(e.args[0][0]['code'])+"</h1><p><h2>"+e.args[0][0]['message']+"</h2>"
            except:
                tweets ="<font color='#ff0000'>検索に失敗しました。存在しないか鍵垢の可能性があります。APIの制限の場合は最大15分お待ちを。</font>"
        #return flask.render_template('center2.html' ,tweet=tweets)
        return redirect("/user/"+user_txt+"/normal")
    
    if TLmode==4:#通知欄
        return redirect("/notice")







@app.route('/notice')#通知欄　検索条件：「url:https://twitter.com/username/ OR @username」
@auth.login_required      #それぞれに、これ必須。ないと誰でも見れてしまう。
def notice():
    global api
    global my_info
    res_d={}
    result=""
    old_result=""
    nosave=False
    
    query = "url:https://twitter.com/"+my_info.screen_name+"/ OR @"+my_info.screen_name+" OR RT @"+my_info.screen_name
    if os.path.isfile("./notice.json"):#notice.jsonがあるなら
        json_file = open("./notice.json","r")
        old_notice = json.load(json_file)
        top_notice = old_notice["top_notice"]
        old_result = old_notice["tweets"]

        
        res_d = get_serch_tw(query,"notice",count=30,since_id=int(top_notice))#通常検索
        if res_d=="error":
            res_d={}
            nosave =True
        ##########
        
        key_followers_ids = key_follower_list()
        json_file = open("./keyuser_tl.json","r")
        data = json.load(json_file)
        for key_follower_id in key_followers_ids:   #通常の検索では鍵垢がひっかからないので、フォロバされてる鍵垢に限り、この条件分岐で取得。
            
            ts = data[str(key_follower_id)]["tweets"]#リスト形式でたくさんtweet入ってる。

            tweets=[]
            for tweet in ts:#一気にobjectにするとエラー吐くから１ずつ。
                    if tweet["id"]<=int(top_notice):
                        continue
                    
                    tweet = Box(tweet)
                    tweets.append(tweet)

            for tweet in tweets:
                
                if hasattr(tweet,"full_text"):
                    tweet.text = tweet.full_text
                if "https://twitter.com/"+my_info.screen_name+"/" in tweet.text:#鍵からの引用
                    temp_res = tweet_process(tweet)+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.created_at)+"</font><br>"+fav_rt_bottun(tweet,"nothing")+"<br><hr>"
                    res_d[tweet.id_str]=temp_res
                    
                if not hasattr(tweet, "retweeted_status"):
                    if "@"+my_info.screen_name in tweet.text:#鍵からのリプライ
                        temp_res = tweet_process(tweet)+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.created_at)+"</font><br>"+fav_rt_bottun(tweet,"nothing")+"<br><hr>"
                        res_d[tweet.id_str]=temp_res
                        

                else:#単なるRTの通知（鍵垢のみ）

                    if tweet.retweeted_status.user.screen_name==my_info.screen_name:
                        
                        prof_url = tweet.user.profile_image_url
                        prof_name = prof_url[prof_url.rfind('/') + 1:]
                        prof_file = download_img(prof_url,prof_name)
                            
                        temp_res = '<br><a href="/user/'+tweet.user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><img src='+prof_file+' width=30px align="left"><b>'+tweet.user.name+'</b></a>さんがリツイートしました💔<br><br><font size="2" color="#888888"><a href=/tweet/'+str(tweet.retweeted_status.id)+' style="text-decoration: none; color:#000000; word-break: break-all;">'+str(tweet.text).replace("\n","<br>").replace("RT @"+my_info.screen_name+":","")+'<br></a></font><hr>'
                        
                        res_d[tweet.id_str]=temp_res
                    
                   
        ##########






    else:#ないなら作成！
        print("notice-non-exist")
        

        res_d = get_serch_tw(query,"notice",count=30)#通常検索
        if res_d=="error":
            res_d={}
            nosave =True

        ##########
        
        key_followers_ids = key_follower_list()
        json_file = open("./keyuser_tl.json","r")
        data = json.load(json_file)
        for key_follower_id in key_followers_ids:   #通常の検索では鍵垢がひっかからないので、フォロバされてる鍵垢に限り、この条件分岐で取得。

            ts = data[str(key_follower_id)]["tweets"]#リスト形式でたくさんtweet入ってる。
                
            tweets=[]
            for tweet in ts:#一気にobjectにするとエラー吐くから１ずつ。
                    tweet = Box(tweet)
                    tweets.append(tweet)

            for tweet in tweets:
                
                if hasattr(tweet,"full_text"):
                    tweet.text = tweet.full_text
                if not hasattr(tweet, "retweeted_status"):
                    if "https://twitter.com/"+my_info.screen_name+"/" in tweet.text or "@"+my_info.screen_name in tweet.text:
                        temp_res = tweet_process(tweet)+"<font size='1' color='#888888'><br>"+change_time_JST(tweet.created_at)+"</font><br>"+fav_rt_bottun(tweet,"nothing")+"<br><hr>"
                        res_d[tweet.id_str]=temp_res
                else:#単なるRTの通知(鍵垢のみ)

                    if tweet.retweeted_status.user.screen_name==my_info.screen_name:
                        
                        prof_url = tweet.user.profile_image_url
                        prof_name = prof_url[prof_url.rfind('/') + 1:]
                        prof_file = download_img(prof_url,prof_name)
                            
                        temp_res = '<br><a href="/user/'+tweet.user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><img src='+prof_file+' width=30px align="left"><b>'+tweet.user.name+'</b></a>さんがリツイートしました💔<br><br><font size="2" color="#888888"><a href=/tweet/'+str(tweet.retweeted_status.id)+' style="text-decoration: none; color:#000000; word-break: break-all;">'+str(tweet.text).replace("\n","<br>").replace("RT @"+my_info.screen_name+":","")+'<br></a></font><hr>'
                        
                        res_d[tweet.id_str]=temp_res
                        
                    
        
                    
        ##########
    res_d = dict(sorted(res_d.items(), key=lambda x:x[0], reverse=True))#id順にならびかえ

    if len(res_d.keys())==0:
        try:
            top_notice=top_notice
        except:
            return flask.render_template('center2.html',tweet = "ERROR")
    else:
        top_notice = list(res_d.keys())[0]

    for tweet_html in res_d.values():
        result = result + tweet_html
            
    
    result = result+old_result


    if nosave:
        pass
    else:
        json_dict = dict(tweets=result,top_notice=top_notice)
        json_file = open("./notice.json","w")
        json.dump(json_dict,json_file)

    result ="<a href='/notice' style='text-decoration: none; color:#000000;'><h2 align='center'>通知</h2></a><hr><hr>"+result
    return flask.render_template('center2.html',tweet = result)
    



        
        
@app.route('/settings/<setting_key>')#valueというbool値と一緒に投げること。
@auth.login_required
def settings(setting_key):
    value =  request.args.get('value')
    if value=="True":
        value=True
    elif value=="False":
        value=False
    write_setting(setting_key,value)
    return redirect("/")

    
@app.route('/_fav/<tweet_id>')
@auth.login_required
def fav_ch(tweet_id):
    global api

    
    try:
        api.create_favorite(int(tweet_id))
        
    except:
        try:
            api.destroy_favorite(int(tweet_id))
            
        except Exception as e:
            error_log(e,"fav_ch")
            print("failed"+str(e))
    #redirect_link = request.args.get('redirect')

        
    return ""


@app.route('/_rt/<tweet_id>')
@auth.login_required
def retweet_ch(tweet_id):
    global api
    
    try:
        api.retweet(int(tweet_id))
    except:
        try:
            api.unretweet(int(tweet_id))
        except:
            pass

    return ""


@app.route('/_unfav/<tweet_id>')
@auth.login_required
def faved_ch(tweet_id):
    global api
    
    try:
        api.destroy_favorite(int(tweet_id))
    except:
        try:
            api.create_favorite(int(tweet_id))
        except:
            pass

    return ""
    
@app.route('/_unrt/<tweet_id>')
@auth.login_required
def retweeted_ch(tweet_id):

    
    try:
        api.unretweet(int(tweet_id))
    except:
        try:
            api.retweet(int(tweet_id))
        except:
            pass
        
    return ""


    
@app.route('/followers/<user_id>')
@auth.login_required
def followers(user_id):
    global api
    try:
        result =""
        friends_ids = []
        # フォローした人のIDを全取得
        # Cursor使うとすべて取ってきてくれるが，配列ではなくなるので配列に入れる
        for friend_id in tweepy.Cursor(api.followers_ids, user_id=int(user_id)).items():
            friends_ids.append(friend_id)

        # 100IDsずつに詳細取得
        for i in range(0, len(friends_ids), 100):
            for user in api.lookup_users(user_ids=friends_ids[i:i+100]):
                prof_url = user.profile_image_url
                prof_name = prof_url[prof_url.rfind('/') + 1:]
                prof_file = download_img(prof_url,prof_name)
                
                result = result + '<a href="/user/'+user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><img src='+prof_file+' width=45px align="left"><font size="4"><b>'+user.name+'</b></font></a><br><font size="1" color="#333333">@'+user.screen_name+'</font><br><hr>'
    except Exception as e:
        error_log(e,"followers")
        result = result+"<font color='#ff0000'>取得失敗! やーいツイ廃ｗｗｗｗｗ"+str(e)+"</font>"

    return flask.render_template('center2.html',tweet = result)
@app.route('/followings/<user_id>')
@auth.login_required
def followings(user_id):
    global api
    try:
        result =""
        friends_ids = []
        # フォローした人のIDを全取得
        # Cursor使うとすべて取ってきてくれるが，配列ではなくなるので配列に入れる
        for friend_id in tweepy.Cursor(api.friends_ids, user_id=int(user_id)).items():
            friends_ids.append(friend_id)

        # 100IDsずつに詳細取得
        for i in range(0, len(friends_ids), 100):
            for user in api.lookup_users(user_ids=friends_ids[i:i+100]):
                prof_url = user.profile_image_url
                prof_name = prof_url[prof_url.rfind('/') + 1:]
                prof_file = download_img(prof_url,prof_name)
                
                result = result + '<a href="/user/'+user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><img src='+prof_file+' width=45px align="left"><font size="4"><b>'+user.name+'</b></font></a><br><font size="1" color="#333333">@'+user.screen_name+'</font><br><hr>'
    except Exception as e:
        error_log(e,"followings")
        result = result+"<font color='#ff0000'>取得失敗! やーいツイ廃ｗｗｗｗｗ"+str(e)+"</font>"

    return flask.render_template('center2.html',tweet = result)
        
@app.route('/center1.html')
@auth.login_required
def show_dotw():
    global api
    
    return flask.render_template('center1.html',message="")


@app.route('/deeptweet/<tweet_id>')
@auth.login_required
def deeptweet(tweet_id):#リプの深追い
    global api
    
    one_tweet = get_one_tweet(tweet_id,deep=True)
    one_tweet = '<font size="3"><b><a href="/center2.html">←</a></b></font><br>'+one_tweet
    return flask.render_template('center2.html',tweet = one_tweet)



@app.route('/follow/<user_id>')
@auth.login_required
def follow(user_id):
    global api
    
    try:
        api.create_friendship(user_id)
    except:
        pass
    return redirect('/user/'+user_id+'/normal')

@app.route('/unfollow/<user_id>')
@auth.login_required
def unfollow(user_id):
    global api
    
    try:
        api.destroy_friendship(user_id)#自分自身をフォローすることの防止
    except:
        pass
    return redirect('/user/'+user_id+'/normal')

@app.route('/rtuser/<tweet_id>')#リツイートしたユーザーを表示
@auth.login_required
def rtuser(tweet_id):
    global api
    
    try:
        result =""
        retweets = api.retweets(id=int(tweet_id))
        
        for tweet in retweets:
            prof_url = tweet.user.profile_image_url
            prof_name = prof_url[prof_url.rfind('/') + 1:]
            prof_file = download_img(prof_url,prof_name)
            
            result = result + '<a href="/user/'+tweet.user.screen_name+'/normal" style="text-decoration: none; color:#000000;"><img src='+prof_file+' width=45px align="left"><font size="4"><b>'+tweet.user.name+'</b></font></a><br><font size="1" color="#333333">@'+tweet.user.screen_name+'</font><br><hr>'
    except Exception as e:
        error_log(e,"rtuser")
        result = result+"<font color='#ff0000'>取得失敗! やーいツイ廃ｗｗｗｗｗ"+str(e)+"</font>"

    return flask.render_template('center2.html',tweet = result)
            
@app.route('/favuser/<tweet_id>')
@auth.login_required
def favuser(tweet_id):#いいねしたユーザーを表示。
    global api
    global bearer_token
    try:
        
        headers = {"Authorization": "Bearer {}".format(bearer_token)}
        params = {
              "user.fields": "created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld"
              }
        url = "https://api.twitter.com/2/tweets/{}/liking_users".format(tweet_id)
        res = requests.get(url, headers=headers, params = params)
        res_text = res.text
        res_json = json.loads(res_text)
        if "errors" in res_json:#エラーなら
            if res_json['type']== 'https://api.twitter.com/2/problems/not-authorized-for-resource':
                result = "鍵垢のいいね、リツイートは取得できません。"
                return flask.render_template('center2.html',tweet = result)
            else:
                result = res_json["detail"]
                return flask.render_template('center2.html',tweet = result)
            
        else:
            likes = res_json["data"]

        result =""

        print(likes)
        for tweet in likes:
            prof_url = tweet["profile_image_url"]
            prof_name = prof_url[prof_url.rfind('/') + 1:]
            prof_file = download_img(prof_url,prof_name)
            
            result = result + '<a href="/user/'+tweet["username"]+'/normal" style="text-decoration: none; color:#000000;"><img src='+prof_file+' width=45px align="left"><font size="4"><b>'+tweet["name"]+'</b></font></a><br><font size="1" color="#333333">@'+tweet["username"]+'</font><br><hr>'
    except Exception as e:
        error_log(e,"favuser")
        result = result+"<font color='#ff0000'>取得失敗! やーいツイ廃ｗｗｗｗｗ"+str(e)+"</font>"

    return flask.render_template('center2.html',tweet = result)









@app.route('/tweet/<tweet_id>')
@auth.login_required      #それぞれに、これ必須。ないと誰でも見れてしまう。

def tweets(tweet_id):
    global api
    global showing_tweet_id
    showing_tweet_id = tweet_id
    """try:
        one_tweet = get_one_tweet(tweet_id)
        one_tweet = '<font size="3"><b><a href="/center2.html">←</a></b></font><br>'+one_tweet
    except Exception as e:
        error_log(e,"tweets")
        try:
            one_tweet ="<h1>Error Code: "+str(e.args[0][0]['code'])+"</h1><p><h2>"+e.args[0][0]['message']+"</h2>"#エラーメッセージ
        except:
            one_tweet = "表示中にエラーが発生しました。<br>場所：tweets()"
    """

    return flask.render_template('reply.html')

@app.route('/search/<mode>')#center2.html内のリンクから飛んできた。モード指定。
@auth.login_required      #それぞれに、これ必須。ないと誰でも見れてしまう。

def search_othermode(mode):
    global api
    

    tweets = '<div class ="flex-container"><div class ="flex-item"><a href=/search/mixed style="text-decoration: none; color:#000000;">ー話題ー</a></div><div class ="flex-item"><a href=/search/recent style="text-decoration: none; color:#000000;">ー最新ー</a></div>'
    tweets= tweets +'<div class ="flex-item"><a href=/search/picture style="text-decoration: none; color:#000000;">ー画像ー</a></div></div><hr>'

    if mode=="picture":#画像
        try:
            tweets = tweets.replace("ー画像ー","<b>ー画像ー</b>")#選ばれてる項目だけ太文字にする。
            tweets = tweets + get_serch_tw(serch_txt,mode="picture")#検索、追記
        except Exception as e:
            error_log(e,"search_othermode (mode=picture)")
            tweets ="<h1>Error Code: "+str(e.args[0][0]['code'])+"</h1><p><h2>"+e.args[0][0]['message']+"</h2>"#エラーメッセージ

        
    elif mode=="mixed":#話題
        try:
            tweets = tweets.replace("ー話題ー","<b>ー話題ー</b>")
            tweets = tweets + get_serch_tw(serch_txt,mode="mixed")
        except Exception as e:
            error_log(e,"search_othermode (mode=mixed)")
            tweets ="<h1>Error Code: "+str(e.args[0][0]['code'])+"</h1><p><h2>"+e.args[0][0]['message']+"</h2>"

    elif mode=="recent":#最新
        try:
            tweets = tweets.replace("ー最新ー","<b>ー最新ー</b>")
            tweets = tweets + get_serch_tw(serch_txt,mode="recent")
        except Exception as e:
            error_log(e,"search_othermode (mode=recent)")
            tweets ="<h1>Error Code: "+str(e.args[0][0]['code'])+"</h1><p><h2>"+e.args[0][0]['message']+"</h2>"



    else:
        tweets = tweets+"<br><h1>Bad Search-Type!</h1>"
        
    return flask.render_template('center2.html' ,tweet=tweets)



@app.route('/send_rep/<screen_name>/<tweet_id>', methods=['GET', 'POST'])
@auth.login_required

def send_rep(screen_name,tweet_id):
    global api
    

    """if request.method == 'POST':
        reply_txt = request.form.get('reply')
        if reply_txt is not None:
            reply = screen_name +" "+ reply_txt
            try:
                api.update_status(status=reply,in_reply_to_status_id=tweet_id)
                time.sleep(0.1)
            except:
                pass
        return redirect('/tweet/'+tweet_id)""" #ここらへんのは、画像なしの時代。


    
    if request.method == 'POST':
        upload_files = request.files.getlist('reply_file')
        
        if pathlib.Path(upload_files[0].filename).suffix !="":
            try:
                
                media_ids = []
                for file in upload_files:
                    filename = "img"+pathlib.Path(upload_files[0].filename).suffix
                    file.save(filename)
                    img = api.media_upload(filename)
                    media_ids.append(img.media_id)
                text = request.form['reply']
                text = screen_name +" "+ text
                
            except Exception as e:
                error_log(e,"send_rep")
                
                return redirect('/tweet/'+tweet_id)
            try:
                api.update_status(status=text, media_ids=media_ids,in_reply_to_status_id=tweet_id)
                
            except Exception as e:
                error_log(e,"send_rep")
                return redirect('/tweet/'+tweet_id)
            return redirect('/tweet/'+tweet_id)
        else:
            
            
            
            text = request.form['reply']
            if text is None:
                return redirect('/tweet/'+tweet_id) #画像無しなのに、文章も空白なとき
            else:
                text = screen_name +" "+ text

                
            try:
                api.update_status(status=text,in_reply_to_status_id=tweet_id)
            except Exception as e:
                error_log(e,"send_rep")
                return redirect('/tweet/'+tweet_id)
            time.sleep(0.1)
            
            return redirect('/tweet/'+tweet_id)

    # POSTメソッド以外なら、index.htmlに飛ばす
    else:
        return redirect('/tweet/'+tweet_id)

    
@app.route('/search', methods=['GET', 'POST'])#search/mixedみたいに後ろにつけるリンクを貼り付けて置き、そのうしろのをそのまま検索モードにする。　右側の検索から飛んできた。リロードかけて中央のに反映。
@auth.login_required      #それぞれに、これ必須。ないと誰でも見れてしまう。

def search():
    global api
    
    global TLmode
    global serch_txt
    serch_txt = request.form.get('search')
    if serch_txt is None:
        return "None"
    if request.method == 'POST':
        
        
        #return index()
        if read_setting("datasaver"):
            save=1#SAVE中
        else:
            save=2
            
        TLmode = 2
                
        return render_template('index.html',TLmode=2,datasaver=save)


@app.route('/user/<user_screen_name>/<mode>')#center2.html内のリンクから飛んできた。モード指定。
@auth.login_required      #それぞれに、これ必須。ないと誰でも見れてしまう。
def user_img(user_screen_name,mode):
    global api



    tweets = get_user_tw(user_screen_name,mode)
    TLmode=2
    return flask.render_template('center2.html' ,tweet=tweets,message="")

@app.route('/user', methods=['GET', 'POST'])#右側の検索から飛んできた。リロードかけて中央のに反映。
@auth.login_required      #それぞれに、これ必須。ないと誰でも見れてしまう。
def user():
    global api
    global TLmode
    global user_txt
    
    if request.method == 'POST':
        
        user_txt = request.form.get('user')
        #return index()
        
        if read_setting("datasaver"):
            save=1#SAVE中
        else:
            save=2
        TLmode = 3
        return render_template('index.html',TLmode=3,datasaver=save,message="")

    
#アクセスできるか確認ページ
@app.route('/testpage_01', methods=['GET'])
#@auth.login_required
def testpage_01():
    nitter_list =["https://nitter.net/","https://nitter.cz/","https://nitter.ca/","https://nitter.fly.dev/","https://nitter.hu/","https://nitter.kylrth.com/","https://nitter.42l.fr/",
                  "https://nitter.kavin.rocks/","https://nitter.unixfox.eu/","https://nitter.namazso.eu/","https://nitter.moomoo.me/","https://bird.trom.tf/",
                  "https://nitter.grimneko.de/","https://twitter.076.ne.jp/","https://notabird.site/","https://nitter.weiler.rocks/","https://nitter.sethforprivacy.com/","https://nttr.stream/",
                  "https://nitter.cutelab.space/","https://nitter.nl/","https://nitter.bus-hit.me/","https://nitter.esmailelbob.xyz/","https://tw.artemislena.eu/",
                  "https://nitter.dcs0.hu/","https://twitter.dr460nf1r3.org/","https://nitter.privacydev.net/","https://nitter.foss.wtf/",
                  "https://nitter.priv.pw/","https://unofficialbird.com/","https://nitter.projectsegfau.lt/","https://singapore.unofficialbird.com/",
                  "https://canada.unofficialbird.com/","https://nitter.fprivacy.com/","https://twt.funami.tech/","https://india.unofficialbird.com/","https://nederland.unofficialbird.com/",
                  "https://uk.unofficialbird.com/","https://n.l5.ca/","https://nitter.slipfox.xyz/"]
    result ="<h1>nitterアクセス確認ぺぇじ</h1>"
    for nitter_url in nitter_list:
        result = result + "<br>" + nitter_url + "<br><img src='" + nitter_url +"pic/pbs.twimg.com%2Fprofile_images%2F1522261990944952320%2FGCgDBnwT.jpg' width='100px'><br>"
    return result

# 入力値の表示ページ
@app.route('/result', methods=['GET', 'POST'])#ツイート用
@auth.login_required
def result():
    global retry_apis
    api = retry_apis[0]
    
    # index.htmlのinputタグ内にあるname属性itemを取得し、textに格納した
    #text = request.form.get('serch')
    #tweets = get_user_tw(text,"normal")
    #print(tweets)
    # もしPOSTメソッドならresult.htmlに値textと一緒に飛ばす
    if request.method == 'POST':
        upload_files = request.files.getlist('upload_file')
        
        if pathlib.Path(upload_files[0].filename).suffix !="":
            try:
                
                media_ids = []
                for file in upload_files:
                    filename = "img"+pathlib.Path(upload_files[0].filename).suffix
                    file.save(filename)
                    img = api.media_upload(filename)
                    media_ids.append(img.media_id)
                text = request.form['tweet_content']
            except Exception as e:
                error_log(e,"result (media tweet)")
                return flask.render_template('center1.html',message="<script>alert('"+str(e)+"')</script>")
            try:
                api.update_status(status=text, media_ids=media_ids)
                
            except Exception as e:
                error_log(e,"result (media tweet)")
                return flask.render_template('center1.html',message="<script>alert('"+str(e)+"')</script>")
            return flask.render_template('center1.html',message="")
        else:
            
            
            text = request.form['tweet_content']
            try:
                api.update_status(text)
            except Exception as e:
                error_log(e,"result (text tweet)")
                return flask.render_template('center1.html',message="<script>alert('"+str(e)+"')</script>")
            time.sleep(0.1)
            
            return flask.render_template('center1.html',message="")

    # POSTメソッド以外なら、index.htmlに飛ばす
    else:
        return flask.render_template('center1.html',message="")


if __name__=='__main__':
    app.run(debug=False,host='0.0.0.0',port='8080')
