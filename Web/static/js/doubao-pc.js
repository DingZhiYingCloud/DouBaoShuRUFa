/**
 * 豆包输入法官网 PC 首页 - 交互层（本地克隆实现）
 *
 * 功能与源站保持一致：
 *   1. Swiper 特性轮播（自动播放 3s、分页可点击、横向滚轮翻页）
 *   2. macOS / Windows 安装包直链下载
 *   3. iOS / Android / HarmonyOS 扫码下载弹层（点击遮罩或 Esc 关闭）
 *
 * 依赖：swiper-bundle.min.js（全局 Swiper）、qrcode.min.js（全局 QRCode）
 * 弹层数据由服务端通过 #modal-config（json_script）注入。
 */
(function () {
    'use strict';

    /* ============ 0. rem 根字号校正 ============
     * 首屏内联脚本执行时纵向滚动条尚未生成，clientWidth 偏大，会算出过大的根字号
     * 导致内容宽度超出视口、出现横向滚动条。此处按最终视口宽度复核，并在窗口尺寸
     * 与资源加载变化时再次校正。
     */
    function initRemAdaptation() {
        var apply = window.__applyRootFontSize;
        if (typeof apply !== 'function') return;
        apply();
        window.addEventListener('load', apply);
        window.addEventListener('resize', apply);
    }

    /* ============ 1. 特性轮播 ============ */
    function initSwiper() {
        if (typeof Swiper === 'undefined') return;
        var el = document.querySelector('.swiper');
        if (!el) return;
        new Swiper(el, {
            slidesPerView: 1,
            autoplay: { delay: 3000 },
            pagination: { el: '.swiper-pagination', clickable: true },
            mousewheel: { forceToAxis: true }
        });
    }

    /* ============ 2. 直链下载（与源站一致：_self 锚点触发） ============ */
    function directDownload(url) {
        if (!url) return;
        var anchor = document.createElement('a');
        anchor.href = url;
        anchor.target = '_self';
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
    }

    function initDownloadButtons() {
        document.querySelectorAll('[data-download]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                directDownload(btn.getAttribute('data-url'));
            });
        });
    }

    /* ============ 3. 扫码下载弹层 ============ */
    function readModalConfig() {
        var el = document.getElementById('modal-config');
        if (!el) return {};
        try {
            return JSON.parse(el.textContent);
        } catch (e) {
            return {};
        }
    }

    function initModal() {
        var modal = document.querySelector('[data-download-modal]');
        if (!modal) return;
        var overlay = modal.querySelector('[data-modal-overlay]');
        var titleEl = modal.querySelector('[data-modal-title]');
        var qrEl = modal.querySelector('[data-modal-qr]');
        var versionEl = modal.querySelector('[data-modal-version]');
        var config = readModalConfig();

        function open(type) {
            var item = config[type];
            if (!item) return;
            titleEl.textContent = item.title;
            versionEl.textContent = item.version || '扫码下载';
            // 重新渲染二维码（按容器原生尺寸 198x199 绘制，保证清晰）
            qrEl.innerHTML = '';
            new QRCode(qrEl, {
                text: item.qr,
                width: 198,
                height: 199,
                colorDark: '#000000',
                colorLight: '#ffffff',
                correctLevel: QRCode.CorrectLevel.H
            });
            modal.hidden = false;
        }

        function close() {
            modal.hidden = true;
        }

        document.querySelectorAll('[data-modal-open]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                open(btn.getAttribute('data-modal-open'));
            });
        });
        overlay.addEventListener('click', function (event) {
            if (event.target === overlay) close();
        });
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && !modal.hidden) close();
        });
    }

    /* ============ 启动 ============ */
    function init() {
        initRemAdaptation();
        initSwiper();
        initDownloadButtons();
        initModal();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
