# -*- coding: utf-8 -*-
import os
import logging
import http.cookies

import asyncio
from typing import *

import aiohttp

#import config
#config.init()
#cfg = config.get_config()

logger = logging.getLogger(__name__)

# 不带这堆头部有时候也能成功请求，但是带上后成功的概率更高
BILIBILI_COMMON_HEADERS = {
    'Origin': 'https://www.bilibili.com',
    'Referer': 'https://www.bilibili.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/114.0.0.0 Safari/537.36'
}

http_session: Optional[aiohttp.ClientSession] = None


def load_bilibili_cookies():
    
    cookies = http.cookies.SimpleCookie()
    #if cfg.bilibili_cookies_file:
    #cookies_fn = os.path.join(config.BASE_PATH, cfg.bilibili_cookies_file)
    cookies_fn = '/data/cookies.txt'
    try:
        with open(cookies_fn, 'rt') as f:
            cookies.load(f.read())
        for cookie in cookies.values():
            cookie['domain'] = cookie['domain'] or '.bilibili.com'
    except FileNotFoundError:
        logger.warning("Cookies file not found, check if config is correct")
    for key in ['SESSDATA', 'bili_jct']:
        if key not in cookies:
            logger.warning("Missing necessary cookie entries, please check cookie file content and format")
            break
    return cookies

def init():
    global http_session
    
    cookie_jar = aiohttp.CookieJar()
    cookie_jar.update_cookies(load_bilibili_cookies())
    #http_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), cookie_jar=cookie_jar)
    
    http_session = aiohttp.ClientSession(
        response_class=CustomClientResponse,
        timeout=aiohttp.ClientTimeout(total=10),
        cookie_jar=cookie_jar
    )


async def shut_down():
    if http_session is not None:
        await http_session.close()


class CustomClientResponse(aiohttp.ClientResponse):
    # 因为aiohttp的BUG，当底层连接断开时，_wait_released可能会抛出CancelledError，导致上层协程结束。这里改个错误类型
    async def _wait_released(self):
        try:
            return await super()._wait_released()
        except asyncio.CancelledError as e:
            raise aiohttp.ClientConnectionError('Connection released') from e
