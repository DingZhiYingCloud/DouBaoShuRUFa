# 项目URL配置
from django.shortcuts import render
from django.http import HttpResponse
from django.core.cache import cache

from SpiderServices import doubao





# 服务类名


def index(request):
    """首页：实时拉取官网下载数据渲染；抓取失败时服务层自动降级为快照，保证页面可访问。"""
    try:
        data = doubao.get_index_context()
    except Exception:
        data = {}  # 兜底：模板按空数据降级渲染
    return render(request, 'index.html', data)


def error_404(request, exception=None):
    """404 错误页：访问不存在的路径或文件时返回（DEBUG=False 时生效）"""
    return render(request, '404.html', status=404)


def error_500(request, exception=None):
    """500 错误页：服务器内部错误时返回（DEBUG=False 时生效）"""
    return render(request, '500.html', status=500)


# ============ Sitemap（站点地图） ============
# 站点内容由爬虫实时获取，因此 sitemap 分为两部分：
#   1. 静态固定 URL：单（与 index.html 硬编码xxxx保持一致，改动需同步）
#   2. 动态 URL：调用爬虫抓取首页，提取xxxx生成详情页链接（爬虫失败时自动降级为仅静态 URL）
# 生成结果缓存 6 小时，避免每次请求 sitemap 都触发源站爬虫。
SITEMAP_STATIC_URLS = [
]
SITEMAP_CACHE_KEY = 'sitemap_urls'
SITEMAP_CACHE_TTL = 60 * 60 * 6  # 6 小时


def sitemap(request):
    """sitemap.xml：静态 URL + 爬虫实时xxxx详情 URL，缓存 6 小时"""

    return HttpResponse('\n', content_type='application/xml')
