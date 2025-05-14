/**
 * @author Taha Al-Jody <taha@ta3.dev>
 * https://github.com/TA3/web-user-behaviour
 */
var userBehaviour = (function () {
    var defaults = {
        userInfo: true,
        clicks: true,
        mouseMovement: true,
        mouseMovementInterval: 1,
        mouseScroll: true,
        timeCount: true,
        clearAfterProcess: true,
        processTime: 15,
        windowResize: true,
        visibilitychange: true,
        keyboardActivity: true,
        pageNavigation: true,
        formInteractions: true,
        touchEvents: true,
        audioVideoInteraction: true,
        customEventRegistration: true,
        processData: function (results) {
            console.log(results);
        },
    };
    var user_config = {};
    var mem = {
        processInterval: null,
        mouseInterval: null,
        mousePosition: [], //x,y,timestamp
        eventListeners: {
            scroll: null,
            click: null,
            mouseMovement: null,
            windowResize: null,
            visibilitychange: null,
            keyboardActivity: null,
            touchStart: null
        },
        eventsFunctions: {
            scroll: () => {

                // scroll details
                var scrollDetails = {
                    url : location.href,
                    title : document.title,
                    x: window.scrollX,
                    y: window.scrollY,
                    timestamp: getTimeStamp(),
                }

                results.mouseScroll.push(scrollDetails);
                saveToLocalStorage();
            },
            click: (e) => {
                results.clicks.clickCount++;
                var path = [];
                var node = "";
                e.composedPath().forEach((el, i) => {
                    if ((i !== e.composedPath().length - 1) && (i !== e.composedPath().length - 2)) {
                        node = el.localName;
                        (el.className !== "") ? el.classList.forEach((clE) => {
                            node += "." + clE
                        }): 0;
                        (el.id !== "") ? node += "#" + el.id: 0;
                        path.push(node);
                    }
                })
                path = path.reverse().join(">");

                // click details
                var clickDetails = {
                    url : location.href,
                    title : document.title,
                    x: e.clientX,
                    y: e.clientY,
                    name : e.target.localName,
                    className : e.target.className,
                    id : e.target.id,
                    path : path,
                    aria_label : e.target.getAttribute("aria-label"),
                    type : e.target.type,
                    value : e.target.value,
                    tagName : e.target.tagName,
                    text : e.target.innerText,
                    timestamp: getTimeStamp(),
                }
                
                // 檢查是否為導航連結 (a標籤)
                const isNavigation = e.target.tagName === 'A' || 
                    (e.target.closest && e.target.closest('a')) || 
                    e.target.getAttribute('role') === 'link';
                
                // 增加標記，表示這是導航點擊
                if (isNavigation) {
                    clickDetails.isNavigation = true;
                    const link = e.target.tagName === 'A' ? e.target : e.target.closest('a');
                    clickDetails.href = link ? link.href : "";
                    
                    // 捕獲點擊的href，供後續導航使用
                    try {
                        window._lastClickedUrl = clickDetails.href;
                        window._lastClickNavTimestamp = getTimeStamp();
                        window._lastClickEvent = {
                            type: 'navigation_click',
                            url: clickDetails.href,
                            details: clickDetails,
                            timestamp: getTimeStamp()
                        };
                    } catch(err) {
                        console.error("保存導航點擊數據失敗:", err);
                    }
                }
                
                results.clicks.clickDetails.push(clickDetails);
                saveToLocalStorage();
                
                // 如果是導航連結，確保數據同步保存後再導航
                if (isNavigation && e.target.tagName === 'A' && e.target.href) {
                    try {
                        // 立即處理數據
                        processResults();
                        
                        // 如果是非同源網站，這個保存數據非常重要
                        if (e.target.href && !e.target.href.startsWith(window.location.origin)) {
                            // 添加導航歷史記錄
                            var pageDetails = {
                                url: location.href,
                                title: document.title,
                                nextUrl: e.target.href,
                                isDirectNavigation: true,
                                timestamp: getTimeStamp(),
                            }
                            results.navigationHistory.push(pageDetails);
                            saveToLocalStorage();
                            processResults();
                        }
                    } catch(err) {
                        console.error("處理導航點擊失敗:", err);
                    }
                }
            },
            mouseMovement: (e) => {
                pos = {
                    x: e.clientX,
                    y: e.clientY
                }
                mem.mousePosition = [pos , getTimeStamp()];
            },
            windowResize: (e) => {
                results.windowSizes.push([window.innerWidth, window.innerHeight, getTimeStamp()]);
                saveToLocalStorage();
            },
            visibilitychange: (e) => {
                results.visibilitychanges.push([document.visibilityState, getTimeStamp()]);
                processResults();
                saveToLocalStorage();
            },
            keyboardActivity: (e) => {
                var path = [];
                var node = "";
                e.composedPath().forEach((el, i) => {
                    if ((i !== e.composedPath().length - 1) && (i !== e.composedPath().length - 2)) {
                        node = el.localName;
                        (el.className !== "") ? el.classList.forEach((clE) => {
                            node += "." + clE
                        }): 0;
                        (el.id !== "") ? node += "#" + el.id: 0;
                        path.push(node);
                    }
                })
                path = path.reverse().join(">");

                // input details
                var inputDetails = {
                    url : location.href,
                    title : document.title,
                    x: e.clientX,
                    y: e.clientY,
                    name : e.target.localName,
                    className : e.target.className,
                    id : e.target.id,
                    path : path,
                    aria_label : e.target.getAttribute("aria-label"),
                    type : e.target.type,
                    value : e.target.value,
                    text : e.target.innerText,
                    tagName : e.target.tagName,
                    timestamp: getTimeStamp(),
                }

                results.keyboardActivities.push(inputDetails);
                saveToLocalStorage();
            },
            pageNavigation: () => {
                // 獲取上次點擊的URL和時間戳，用於確認這是點擊導致的導航
                let lastClickedUrl = "";
                let isClickNavigation = false;
                let navigationSource = "direct";
                
                try {
                    lastClickedUrl = window._lastClickedUrl || "";
                    const lastClickTime = window._lastClickNavTimestamp || 0;
                    
                    // 如果在過去3秒內有點擊導航，可以推斷為點擊導航
                    if (lastClickedUrl && (getTimeStamp() - lastClickTime < 3000)) {
                        isClickNavigation = true;
                        navigationSource = "click";
                    }
                } catch(e) {
                    console.error("獲取導航信息失敗:", e);
                }

                // page navigation details
                var pageDetails = {
                    url : location.href,
                    title : document.title,
                    timestamp: getTimeStamp(),
                    navigationSource: navigationSource,
                    previousUrl: document.referrer || "",
                    isClickNavigation: isClickNavigation,
                    fromClick: lastClickedUrl
                }

                results.navigationHistory.push(pageDetails);
                saveToLocalStorage();
                
                // 清理上次點擊記錄，避免影響下次判斷
                try {
                    window._lastClickedUrl = "";
                    window._lastClickNavTimestamp = 0;
                } catch(e) {
                    console.error("清理導航點擊數據失敗:", e);
                }
            },
            formInteraction: (e) => {
                e.preventDefault(); // Prevent the form from submitting normally
                results.formInteractions.push([e.target.name, getTimeStamp()]);
                saveToLocalStorage();
                // Optionally, submit the form programmatically after tracking
            },
            touchStart: (e) => {
                results.touchEvents.push(['touchstart', "(" + e.touches[0].clientX + "," + e.touches[0].clientY + ")" , getTimeStamp()]);
                saveToLocalStorage();
            },
            mediaInteraction: (e) => {
                results.mediaInteractions.push(['play', e.target.currentSrc, getTimeStamp()]);
                saveToLocalStorage();
            }
        }
    };
    var results = {};

    // Load results from localStorage if available
    function loadFromLocalStorage() {
        try {
            const savedData = localStorage.getItem('userBehaviourData');
            if (savedData) {
                const parsedData = JSON.parse(savedData);
                // Only use saved data if it has the expected structure
                if (parsedData && typeof parsedData === 'object' && 'clicks' in parsedData) {
                    return parsedData;
                }
            }
        } catch (e) {
            console.error("Error loading from localStorage:", e);
        }
        return null;
    }

    // Save current results to localStorage
    function saveToLocalStorage() {
        try {
            localStorage.setItem('userBehaviourData', JSON.stringify(results));
        } catch (e) {
            console.error("Error saving to localStorage:", e);
        }
    }

    function resetResults() {
        // Try to load existing data first
        const savedResults = loadFromLocalStorage();
        
        if (savedResults) {
            console.log("Loaded previous tracking data from localStorage");
            results = savedResults;
            
            // Update time info
            if (!results.time) {
                results.time = {
                    startTime: getTimeStamp(),
                    currentTime: getTimeStamp(),
                    stopTime: 0,
                };
            }
            
            // Make sure all necessary arrays exist
            if (!results.mouseMovements) results.mouseMovements = [];
            if (!results.mouseScroll) results.mouseScroll = [];
            if (!results.keyboardActivities) results.keyboardActivities = [];
            if (!results.navigationHistory) results.navigationHistory = [];
            if (!results.formInteractions) results.formInteractions = [];
            if (!results.touchEvents) results.touchEvents = [];
            if (!results.mediaInteractions) results.mediaInteractions = [];
            if (!results.windowSizes) results.windowSizes = [];
            if (!results.visibilitychanges) results.visibilitychanges = [];
        } else {
            // Initialize with new data
            results = {
                userInfo: {
                    windowSize: [window.innerWidth, window.innerHeight],
                    appCodeName: navigator.appCodeName || '',
                    appName: navigator.appName || '',
                    vendor: navigator.vendor || '',
                    platform: navigator.platform || '',
                    userAgent: navigator.userAgent || ''
                },
                time: {
                    startTime: 0,
                    currentTime: 0,
                    stopTime: 0,
                },
                clicks: {
                    clickCount: 0,
                    clickDetails: []
                },
                mouseMovements: [],
                mouseScroll: [],
                keyboardActivities: [],
                navigationHistory: [],
                formInteractions: [],
                touchEvents: [],
                mediaInteractions: [],
                windowSizes: [],
                visibilitychanges: [],
            };
            
            // Add current page to navigation history
            var pageDetails = {
                url : location.href,
                title : document.title,
                timestamp: getTimeStamp(),
                isInitialPage: true
            }
            results.navigationHistory.push(pageDetails);
        }
        
        // Save the initialized/loaded results
        saveToLocalStorage();
        
        // 設置在beforeunload時儲存資料
        window.addEventListener('beforeunload', function saveBeforeUnload(e) {
            try {
                results.time.currentTime = getTimeStamp();
                // 添加頁面離開記錄
                results.visibilitychanges.push(["beforeunload", getTimeStamp()]);
                
                // 如果有點擊導致的導航，記錄導航信息
                if (window._lastClickEvent) {
                    results.navigationHistory.push({
                        url: window._lastClickEvent.url || "",
                        fromUrl: location.href,
                        timestamp: getTimeStamp(),
                        navigationSource: "click_beforeunload",
                        clickDetails: window._lastClickEvent.details
                    });
                }
                saveToLocalStorage();
                
                // 確保同步保存
                var forceSyncSave = function() {
                    localStorage.setItem('userBehaviourData_unload', JSON.stringify({
                        time: new Date().toISOString(),
                        lastNav: window._lastClickEvent,
                        currentUrl: location.href
                    }));
                };
                forceSyncSave();
                
                // 允許正常導航
                delete e['returnValue'];
            } catch(err) {
                console.error("beforeunload儲存失敗:", err);
            }
        });
        
        // 增強導航監測
        enhanceNavigationTracking();
    };
    
    function enhanceNavigationTracking() {
        // 攔截所有A標籤的點擊
        document.addEventListener('click', function captureAnchorClicks(e) {
            const link = e.target.closest('a');
            if (!link || !link.href) return;
            
            // 創建導航信息
            window._navigationInfo = {
                fromUrl: location.href,
                toUrl: link.href,
                clickedAt: getTimeStamp(),
                targetText: link.innerText || link.textContent,
                targetHref: link.href
            };
            
            // 對於外部連結，強制進行記錄
            if (link.target === '_blank' || !link.href.startsWith(window.location.origin)) {
                try {
                    results.navigationHistory.push({
                        url: location.href,
                        title: document.title,
                        nextUrl: link.href,
                        isExternalNavigation: true,
                        timestamp: getTimeStamp()
                    });
                    saveToLocalStorage();
                    processResults();
                } catch(err) {
                    console.error("保存外部導航信息失敗:", err);
                }
            }
        }, true);
        
        // 攔截表單提交
        document.addEventListener('submit', function captureFormSubmit(e) {
            try {
                const form = e.target;
                if (!form || form.tagName !== 'FORM') return;
                
                // 記錄表單提交
                results.formInteractions.push({
                    url: location.href,
                    title: document.title,
                    formId: form.id || "",
                    formAction: form.action || "",
                    formMethod: form.method || "GET",
                    isFormNavigation: true,
                    timestamp: getTimeStamp()
                });
                saveToLocalStorage();
                processResults();
            } catch(err) {
                console.error("保存表單提交信息失敗:", err);
            }
        }, true);
        
        // 創建全局變數來保存原始 URL
        try {
            window._originalUserBehaviourUrl = location.href;
            
            // 使用 MutationObserver 監控頁面DOM變化
            const observer = new MutationObserver(function(mutations) {
                if (window._originalUserBehaviourUrl !== location.href) {
                    console.log("偵測到URL變化:", window._originalUserBehaviourUrl, "->", location.href);
                    
                    // 新增一條導航記錄
                    results.navigationHistory.push({
                        url: location.href,
                        title: document.title,
                        previousUrl: window._originalUserBehaviourUrl,
                        isMutationNavigation: true,
                        timestamp: getTimeStamp()
                    });
                    
                    window._originalUserBehaviourUrl = location.href;
                    saveToLocalStorage();
                }
            });
            
            observer.observe(document, {
                childList: true,
                subtree: true
            });
        } catch(err) {
            console.error("設置 URL 監測失敗:", err);
        }
    }

    function getTimeStamp() {
        return Date.now();
    };

    function config(ob) {
        user_config = {};
        Object.keys(defaults).forEach((i) => {
            i in ob ? user_config[i] = ob[i] : user_config[i] = defaults[i];
        })
    };

    function start() {
        if (Object.keys(user_config).length !== Object.keys(defaults).length) {
            console.log("no config provided. using default..");
            user_config = defaults;
        }
        // TIME SET
        if (user_config.timeCount !== undefined && user_config.timeCount) {
            if (results.time && results.time.startTime === 0) {
                results.time.startTime = getTimeStamp();
                saveToLocalStorage();
            }
        }
        
        // Set up page unload handler
        window.addEventListener('beforeunload', function() {
            processResults();
        });

        // MOUSE MOVEMENTS
        if (user_config.mouseMovement) {
            /*
            mem.eventListeners.mouseMovement = window.addEventListener("mousemove", mem.eventsFunctions.mouseMovement);
            mem.mouseInterval = setInterval(() => {
                if (mem.mousePosition && mem.mousePosition.length) {
                    if (!results.mouseMovements.length || ((mem.mousePosition[0] !== results.mouseMovements[results.mouseMovements.length - 1][0]) && (mem.mousePosition[1] !== results.mouseMovements[results.mouseMovements.length - 1][1]))) {
                        results.mouseMovements.push(mem.mousePosition)
                    }
                }
            }, defaults.mouseMovementInterval * 1000);*/
        }
        //CLICKS
        if (user_config.clicks) {
            mem.eventListeners.click = window.addEventListener("click", mem.eventsFunctions.click, {capture: true});
        }
        //SCROLL
        if (user_config.mouseScroll) {
            mem.eventListeners.scroll = window.addEventListener("scroll", mem.eventsFunctions.scroll);
        }
        //Window sizes
        if (user_config.windowResize !== false) {
            mem.eventListeners.windowResize = window.addEventListener("resize", mem.eventsFunctions.windowResize);
        }
        //Before unload / visibilitychange
        if (user_config.visibilitychange !== false) {
            mem.eventListeners.visibilitychange = window.addEventListener("visibilitychange", mem.eventsFunctions.visibilitychange);
        }
        //Keyboard Activity
        if (user_config.keyboardActivity) {
            mem.eventListeners.keyboardActivity = window.addEventListener("input", mem.eventsFunctions.keyboardActivity);
        }
        //Page Navigation
        if (user_config.pageNavigation) {
            window.history.pushState = (f => function pushState() {
                var ret = f.apply(this, arguments);
                window.dispatchEvent(new Event('pushstate'));
                window.dispatchEvent(new Event('locationchange'));
                return ret;
            })(window.history.pushState);
            
            window.history.replaceState = (f => function replaceState() {
                var ret = f.apply(this, arguments);
                window.dispatchEvent(new Event('replacestate'));
                window.dispatchEvent(new Event('locationchange'));
                return ret;
            })(window.history.replaceState);
            
            window.addEventListener('popstate', mem.eventsFunctions.pageNavigation);
            window.addEventListener('pushstate', mem.eventsFunctions.pageNavigation);
            window.addEventListener('replacestate', mem.eventsFunctions.pageNavigation);
            window.addEventListener('locationchange', mem.eventsFunctions.pageNavigation);
            
            // 新增 hashchange 偵測
            window.addEventListener('hashchange', function(e) {
                console.log("偵測到 hashchange:", e.oldURL, "->", e.newURL);
                results.navigationHistory.push({
                    url: location.href,
                    title: document.title,
                    previousUrl: e.oldURL || document.referrer,
                    isHashChange: true,
                    timestamp: getTimeStamp()
                });
                saveToLocalStorage();
                mem.eventsFunctions.pageNavigation();
            });
        }
        //Form Interactions
        if (user_config.formInteractions) {
            document.querySelectorAll('form').forEach(form => form.addEventListener('submit', function(e) {
                // 記錄表單提交信息
                mem.eventsFunctions.formInteraction(e);
                
                // 對於會導致頁面導航的表單，強制儲存資料
                const isNonAjaxForm = !e.defaultPrevented && 
                                     (!form.getAttribute('onsubmit')) && 
                                     (form.method.toLowerCase() === 'get' || form.method.toLowerCase() === 'post');
                
                if (isNonAjaxForm) {
                    results.formInteractions.push({
                        url: location.href,
                        title: document.title,
                        formId: form.id || "",
                        formName: form.name || "",
                        formMethod: form.method || "",
                        isNavigationForm: true,
                        timestamp: getTimeStamp()
                    });
                    saveToLocalStorage();
                    processResults(); // 立即處理結果
                }
            }, {capture: true}));
        }
        //Touch Events
        if (user_config.touchEvents) {
            mem.eventListeners.touchStart = window.addEventListener("touchstart", mem.eventsFunctions.touchStart);
        }
        //Audio & Video Interaction
        if (user_config.audioVideoInteraction) {
            document.querySelectorAll('video').forEach(video => {
                video.addEventListener('play', mem.eventsFunctions.mediaInteraction);
                // Add other media events as needed
            });
        }

        //PROCESS INTERVAL
        if (user_config.processTime !== false) {
            mem.processInterval = setInterval(() => {
                processResults();
            }, user_config.processTime * 1000)
        }
    };

    function processResults() {
        results.time.currentTime = getTimeStamp();
        
        // 先保存到 localStorage
        saveToLocalStorage();
        
        // 同步保存一次，確保完整
        try {
            localStorage.setItem('userBehaviourData', JSON.stringify(results));
        } catch (e) {
            console.error("同步保存失敗:", e);
        }
        
        // 回調處理函數
        try {
            user_config.processData(result());
        } catch (e) {
            console.error("處理數據回調失敗:", e);
        }
        
        if (user_config.clearAfterProcess) {
            // Don't fully reset, just clear the arrays if needed
            if (typeof results === 'object') {
                // Instead of full reset, clear arrays but keep the structure
            }
        }
    }

    function stop() {
        if (user_config.processTime !== false) {
            clearInterval(mem.processInterval);
        }
        clearInterval(mem.mouseInterval);
        window.removeEventListener("scroll", mem.eventsFunctions.scroll);
        window.removeEventListener("click", mem.eventsFunctions.click);
        window.removeEventListener("mousemove", mem.eventsFunctions.mouseMovement);
        window.removeEventListener("resize", mem.eventsFunctions.windowResize);
        window.removeEventListener("visibilitychange", mem.eventsFunctions.visibilitychange);
        window.removeEventListener("keydown", mem.eventsFunctions.keyboardActivity);
        window.removeEventListener("touchstart", mem.eventsFunctions.touchStart);
        results.time.stopTime = getTimeStamp();
        saveToLocalStorage();
        processResults();
    }

    function result() {
        if (user_config.userInfo === false && userBehaviour.showResult().userInfo !== undefined) {
            delete userBehaviour.showResult().userInfo;
        }
        if (user_config.timeCount !== undefined && user_config.timeCount) {
            results.time.currentTime = getTimeStamp();
            saveToLocalStorage();
        }
        return results
    };

    function showConfig() {
        if (Object.keys(user_config).length !== Object.keys(defaults).length) {
            return defaults;
        } else {
            return user_config;
        }
    };
    
    // Initialize results
    resetResults();
    
    return {
        showConfig: showConfig,
        config: config,
        start: start,
        stop: stop,
        showResult: result,
        processResults: processResults,
        registerCustomEvent: (eventName, callback) => {
            window.addEventListener(eventName, callback);
        },
        // Added methods to directly interact with local storage
        loadFromStorage: loadFromLocalStorage,
        saveToStorage: saveToLocalStorage,
    };

})();