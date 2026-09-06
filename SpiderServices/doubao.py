"""豆包输入法官网数据服务。

策略：优先实时调用官网公开接口获取各平台下载信息（带缓存），
接口不可用时自动降级为本地快照，保证页面永远可渲染。
"""
import logging

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ============ 官网接口 ============
ORIGIN = 'https://shurufa.doubao.com'
DOWNLOAD_URL_API = f'{ORIGIN}/api/v1/app/download_url'
PLATFORMS = ('macos', 'windows', 'ios', 'android', 'harmony')

CACHE_KEY = 'doubao:download_links'
CACHE_TTL = 60 * 60  # 1 小时
REQUEST_TIMEOUT = 5

# ============ 本地快照（2026-09-06 采集自官网接口，接口失败时降级） ============
SNAPSHOT_DOWNLOADS = {
    'macos': {
        'version': 'V0.9.7',
        'url': 'https://lf-wave.doubaocdn.com/obj/doubao-ime/app/macos/DoubaoImeInstaller_v90703_release.zip',
    },
    'windows': {'version': '', 'url': ''},  # 官网暂未开放 Windows 版
    'ios': {'version': 'V1.5.3', 'url': ''},  # iOS 走 App Store，无直链
    'android': {
        'version': 'V1.4.3',
        'url': 'https://lf-wave.doubaocdn.com/obj/doubao-ime/app/android/doubaoime_v1.4.3_100403010_official_arm64_release.apk',
    },
    'harmony': {
        'version': 'V0.9.2',
        'url': 'https://appgallery.huawei.com/app/detail?id=com.bytedance.hm.doubaoime',
    },
}

# 移动端扫码落地页（iOS / Android 二维码内容）
QR_MIDDLE_PAGE = f'{ORIGIN}/h5'

# ============ 首页轮播（源站为前端硬编码内容，此处做等价快照） ============
SLIDES = [
    {
        'title': 'macOS版语音输入',
        'desc': '按住fn开始说话，重新定义效率',
        'image': 'images/doubao/pc0.png',
        'banner_width': '27rem',
        'ios_only': False,
    },
    {
        'title': '语音输入 又快又准',
        'desc': '标点无须改，轻声照样说',
        'image': 'images/doubao/pc1.png',
        'banner_width': '23.875rem',
        'ios_only': False,
    },
    {
        'title': '语音免跳转全新体验',
        'desc': '语音待机+悬浮窗，双模式随心选',
        'image': 'images/doubao/pc2.png',
        'banner_width': '23.7rem',
        'ios_only': True,
    },
    {
        'title': '更高效的键盘输入',
        'desc': '又快又准，省时省心',
        'image': 'images/doubao/pc3.png',
        'banner_width': '24.5rem',
        'ios_only': False,
    },
    {
        'title': '更强大的智能联想',
        'desc': '吃透上下文，秒懂你所想',
        'image': 'images/doubao/pc4.png',
        'banner_width': '23.9rem',
        'ios_only': False,
    },
]

# ============ 页脚合规信息（源站来自 zlink 合规接口，此处快照） ============
FOOTER = {
    'developer': '北京春田知韵科技有限公司',
    'icp': '京ICP备2023020373号-36A',
    'police': '京公网安备11010202010719',
    'license_url': f'{ORIGIN}/license',
    'thanks_url': f'{ORIGIN}/thanks',
}


def fetch_download_links():
    """实时获取各平台下载链接，缓存 1 小时；失败时返回本地快照。"""
    cached = cache.get(CACHE_KEY)
    if cached:
        return cached

    try:
        result = {}
        for platform in PLATFORMS:
            resp = requests.get(
                DOWNLOAD_URL_API,
                params={'platform': platform},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = (resp.json() or {}).get('data') or {}
            result[platform] = {
                'version': data.get('version_name') or '',
                'url': data.get('url') or '',
            }
        cache.set(CACHE_KEY, result, CACHE_TTL)
        return result
    except Exception:
        logger.warning('豆包下载链接接口拉取失败，降级为本地快照', exc_info=True)
        return SNAPSHOT_DOWNLOADS


def get_index_context():
    """组装首页渲染所需的全部上下文数据。"""
    downloads = fetch_download_links()
    return {
        'downloads': downloads,
        'slides': SLIDES,
        'footer': FOOTER,
        # 前端弹层配置（JSON 注入）：各端二维码内容 / 标题 / 版本
        'modal_config': {
            'ios': {
                'title': '豆包输入法 iOS 版',
                'qr': QR_MIDDLE_PAGE,
                'version': downloads['ios']['version'] or '扫码下载',
            },
            'android': {
                'title': '豆包输入法 Android 版',
                'qr': QR_MIDDLE_PAGE,
                'version': downloads['android']['version'] or '扫码下载',
            },
            'harmony': {
                'title': '豆包输入法HarmonyOS NEXT版',
                'qr': downloads['harmony']['url'] or QR_MIDDLE_PAGE,
                'version': downloads['harmony']['version'] or '扫码下载',
            },
        },
    }
