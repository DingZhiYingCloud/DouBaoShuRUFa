"""友情链接数据服务（小影 API）。

通过后端实时调用「小影 API - 查询友情链接列表」接口，在服务端完成数据获取与渲染（SSR），
确保搜索引擎爬虫直接可见友情链接，无需前端再发起 API 请求。

策略（与 doubao.py 一致）：带缓存（1 小时）；接口未配置 / 调用失败 / 签名异常 / 返回错误码时，
自动降级为本地快照（可能为空列表），保证页面始终可渲染、不报错。
"""
import hashlib
import hmac
import logging
import time
import uuid

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ============ 小影 API 配置（来自 .env） ============
API_BASE = getattr(settings, 'XIAOYING_API_BASE', '')
APP_ID = getattr(settings, 'XIAOYING_API_APPID', '')
APP_SECRET = getattr(settings, 'XIAOYING_API_APPSECRET', '')

ENDPOINT = '/api/seo/friend_links'

CACHE_KEY = 'friend_links:list'
CACHE_TTL = 60 * 60  # 1 小时
REQUEST_TIMEOUT = 5

# ============ 本地快照（接口未配置/失败/签名异常时降级） ============
SNAPSHOT_FRIEND_LINKS = []


def _generate_sign(app_id, timestamp, nonce, app_secret):
    """生成签名 sign（HMAC-SHA256）。

    规范：将公共参数按 key 升序拼接为 ``app_id=..&nonce=..&timestamp=..``，
    以 ``app_secret`` 为密钥做 HMAC-SHA256，结果取小写 hex。
    注意：若小影 API 实际签名串规范不同（如含请求路径、body 或不同排序），
    请按其文档调整此处拼接方式。
    """
    params = {'app_id': app_id, 'nonce': nonce, 'timestamp': timestamp}
    canonical = '&'.join(f'{k}={params[k]}' for k in sorted(params))
    return hmac.new(
        app_secret.encode('utf-8'),
        canonical.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


def get_friend_links():
    """拉取友情链接列表（带缓存与降级）。

    返回 ``list[dict]``，字段含 ``name`` / ``url`` / ``description`` / ``logo`` /
    ``category`` 等；接口不可用时返回快照（可能为空列表）。
    仅保留 ``status`` 为启用且地址安全的链接，按 ``sort`` 降序、``create_time`` 降序排列。
    """
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached

    if not (API_BASE and APP_ID and APP_SECRET):
        logger.warning('友情链接接口未配置（缺少 XIAOYING_API_* 环境变量），使用快照')
        return SNAPSHOT_FRIEND_LINKS

    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex
    sign = _generate_sign(APP_ID, timestamp, nonce, APP_SECRET)
    params = {
        'app_id': APP_ID,
        'timestamp': timestamp,
        'nonce': nonce,
        'sign': sign,
    }
    try:
        resp = requests.get(
            f'{API_BASE.rstrip("/")}{ENDPOINT}',
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        logger.warning('友情链接接口请求失败，降级为本地快照', exc_info=True)
        return SNAPSHOT_FRIEND_LINKS

    if payload.get('code') != 10000:
        logger.warning(
            '友情链接接口返回错误：code=%s, msg=%s',
            payload.get('code'), payload.get('msg'),
        )
        return SNAPSHOT_FRIEND_LINKS

    items = (payload.get('data') or {}).get('items') or []
    # 仅保留启用状态且地址安全的链接（防止注入）
    safe_items = []
    for item in items:
        if item.get('status') is False:
            continue
        url = str(item.get('url') or '')
        if not url.startswith(('http://', 'https://')):
            continue
        safe_items.append(item)
    safe_items.sort(
        key=lambda x: (x.get('sort') or 0, x.get('create_time') or ''),
        reverse=True,
    )
    cache.set(CACHE_KEY, safe_items, CACHE_TTL)
    return safe_items
