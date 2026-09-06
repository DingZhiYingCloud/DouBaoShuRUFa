"""模板上下文处理器：为所有页面注入服务端渲染用的友情链接数据。"""
from SpiderServices.friend_links import get_friend_links


def friend_links(request):
    """将后端拉取的友情链接列表注入每一个页面的渲染上下文。

    由于所有页面（首页 / 404 / 500）均通过 Django ``render`` 渲染，
    该处理器会自动生效，无需在各视图中手动传递。
    """
    return {'friend_links': get_friend_links()}
