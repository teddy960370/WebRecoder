/**
 * 阻止頁面開啟新分頁的腳本
 * 強制所有新分頁在當前頁面打開
 */
(function() {
    // 保存原始的 window.open 方法
    var originalWindowOpen = window.open;
    
    // 覆蓋 window.open 方法
    window.open = function(url, name, specs, replace) {
        console.log("攔截到 window.open 調用:", url);
        // 在當前窗口打開，而不是新窗口
        if (url) {
            window.location.href = url;
        }
        // 返回當前窗口引用，讓原始腳本可以繼續運行
        return window;
    };
    
    // 攔截所有鏈接的點擊事件
    document.addEventListener('click', function(e) {
        var target = e.target;
        
        // 循環向上查找 A 標籤（處理點擊在 A 標籤內部的元素的情況）
        while (target && target.tagName !== 'A' && target.parentElement) {
            target = target.parentElement;
        }
        
        if (target && target.tagName === 'A') {
            // 檢查是否會開啟新分頁
            if (target.target === '_blank' || target.getAttribute('rel') === 'noopener' || 
                e.ctrlKey || e.metaKey || e.shiftKey) {
                e.preventDefault();
                e.stopPropagation();
                
                var href = target.href;
                if (href && !href.startsWith('javascript:') && href !== '#') {
                    console.log("攔截到新分頁連結點擊:", href);
                    window.location.href = href;
                }
                return false;
            }
        }
    }, true); // true 表示在捕獲階段處理，先於其他事件監聽器
    
    // 強制修改所有連結，取消 target="_blank"
    function processLinks() {
        var allLinks = document.getElementsByTagName('a');
        for (var i = 0; i < allLinks.length; i++) {
            if (allLinks[i].target === '_blank') {
                allLinks[i].target = '_self';
                // 添加攔截器
                allLinks[i].addEventListener('click', function(e) {
                    e.preventDefault();
                    window.location.href = this.href;
                });
            }
            
            // 移除可能導致新分頁的屬性
            allLinks[i].removeAttribute('rel');
        }
    }
    
    // 初始處理
    processLinks();
    
    // 覆蓋 window.open 和 showModalDialog 方法在所有框架中
    function applyToFrames(win) {
        try {
            win.open = window.open;
            
            // 遍歷子框架
            if (win.frames && win.frames.length) {
                for (var i = 0; i < win.frames.length; i++) {
                    try {
                        applyToFrames(win.frames[i]);
                    } catch (e) {
                        console.log("無法訪問框架:", e);
                    }
                }
            }
        } catch (e) {
            console.log("無法修改框架:", e);
        }
    }
    
    // 應用到所有框架
    try {
        applyToFrames(window);
    } catch (e) {
        console.log("框架處理錯誤:", e);
    }
    
    // 監視 DOM 變化，處理動態添加的連結
    var observer = new MutationObserver(function(mutations) {
        processLinks();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['target', 'href', 'rel']
    });
    
    // 覆蓋各種可能導致新分頁的事件
    ['mousedown', 'mouseup', 'click', 'dblclick', 'auxclick'].forEach(function(eventType) {
        document.addEventListener(eventType, function(e) {
            if (e.button === 1) { // 中鍵點擊
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        }, true);
    });
    
    // 覆蓋 HTMLAnchorElement.prototype.click 方法
    var originalAnchorClick = HTMLAnchorElement.prototype.click;
    HTMLAnchorElement.prototype.click = function() {
        if (this.target === '_blank') {
            this.target = '_self';
        }
        return originalAnchorClick.apply(this, arguments);
    };
    
    console.log("已注入新分頁攔截器");
})();
