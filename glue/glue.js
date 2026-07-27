glue = {
    _host: window.location.origin,

    set_host: function (hostname) {
        glue._host = hostname
    },

    expose: function(f, name) {
        if(name === undefined){
            name = f.toString();
            let i = 'function '.length, j = name.indexOf('(');
            name = name.substring(i, j).trim();
        }

        glue._exposed_functions[name] = f;
    },

    guid: function() {
        return glue._guid;
    },

    // These get dynamically added by library when file is served
    /** _py_functions **/
    /** _start_geometry **/
    /** _webview **/
    /** _window_title **/

    _guid: ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
            (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
        ),

    _exposed_functions: {},

    _mock_queue: [],

    _mock_py_functions: function() {
        for(let i = 0; i < glue._py_functions.length; i++) {
            let name = glue._py_functions[i];
            glue[name] = function() {
                let call_object = glue._call_object(name, arguments);
                glue._mock_queue.push(call_object);
                return glue._call_return(call_object);
            }
        }
    },

    _import_py_function: function(name) {
        let func_name = name;
        glue[name] = function() {
            let call_object = glue._call_object(func_name, arguments);
            glue._websocket.send(glue._toJSON(call_object));
            return glue._call_return(call_object);
        }
    },

    _call_number: 0,

    _call_return_callbacks: {},

    _call_object: function(name, args) {
        let arg_array = [];
        for(let i = 0; i < args.length; i++){
            arg_array.push(args[i]);
        }

        let call_id = (glue._call_number += 1) + Math.random();
        return {'call': call_id, 'name': name, 'args': arg_array};
    },

    _sleep: function(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    _toJSON: function(obj) {
        return JSON.stringify(obj, (k, v) => v === undefined ? null : v);
    },

    _error_payload: function(err) {
        if (err && typeof err === 'object' && (err.errorText !== undefined || err.message !== undefined)) {
            return {
                errorText: err.errorText !== undefined ? err.errorText : String(err.message),
                errorTraceback: err.errorTraceback !== undefined ? err.errorTraceback : (err.stack || '')
            };
        }
        return {
            errorText: String(err),
            errorTraceback: (err && err.stack) ? err.stack : ''
        };
    },

    _send_return: function(call_id, status, value, error) {
        glue._websocket.send(glue._toJSON({
            'return': call_id,
            'status': status,
            'value': value,
            'error': error || {}
        }));
    },

    _call_return: function(call) {
        return function(callback = null) {
            if(callback != null) {
                glue._call_return_callbacks[call.call] = {resolve: callback};
            } else {
                return new Promise(function(resolve, reject) {
                    glue._call_return_callbacks[call.call] = {resolve: resolve, reject: reject};
                });
            }
        }
    },

    _position_window: function(page) {
        let size = glue._start_geometry['default'].size;
        let position = glue._start_geometry['default'].position;

        if(page in glue._start_geometry.pages) {
            size = glue._start_geometry.pages[page].size;
            position = glue._start_geometry.pages[page].position;
        }

        if(size != null){
            let w = size[0];
            let h = size[1];
            // Keep size= as content pixels: add Glue title bar when it is inset chrome.
            if(glue._webview && glue._webview.enabled && glue._webview.titlebar_height){
                h = h + glue._webview.titlebar_height;
            }
            window.resizeTo(w, h);
        }

        if(position != null){
            window.moveTo(position[0], position[1]);
        }
    },

    _webview_os: function() {
        let platform = (glue._webview && glue._webview.platform) || '';
        if(platform){
            return platform;
        }
        let ua = navigator.userAgentData && navigator.userAgentData.platform
            ? navigator.userAgentData.platform
            : (navigator.platform || '');
        if(/Win/i.test(ua)) return 'windows';
        if(/Mac/i.test(ua)) return 'macos';
        return 'linux';
    },

    _titlebar_icon_url: function() {
        if(glue._webview && glue._webview.icon){
            return glue._webview.icon;
        }
        let link = document.querySelector('link[rel="icon"], link[rel="shortcut icon"]');
        if(link && link.getAttribute('href')){
            return link.href;
        }
        return '/favicon.ico';
    },

    _install_webview_chrome: function() {
        if(!glue._webview || !glue._webview.enabled){
            return;
        }
        if(document.getElementById('glue-titlebar')){
            return;
        }

        let os = glue._webview_os();
        let title = (glue._webview && glue._webview.title) || document.title || 'Glue';
        // Heights come from Python (TITLEBAR_HEIGHTS via _webview) — single source of truth.
        let barH = Number(glue._webview && glue._webview.titlebar_height) || 0;
        if(!barH){
            return;
        }
        document.documentElement.classList.add('glue-webview-chrome', 'glue-webview-chrome--' + os);
        document.documentElement.style.setProperty('--glue-titlebar-height', barH + 'px');

        let style = document.createElement('style');
        style.id = 'glue-titlebar-style';
        style.textContent = `
/* Title bar is non-client chrome: window is grown by --glue-titlebar-height and
   content is laid out in the remaining client area (same idea as a native
   title bar outside the client rect). Padding is on html — not body — so
   position:absolute; inset:0 children stay below the bar. */
html.glue-webview-chrome {
  box-sizing: border-box;
  height: 100%;
  padding-top: var(--glue-titlebar-height);
}
html.glue-webview-chrome body {
  box-sizing: border-box;
  height: 100%;
  margin: 0;
  position: relative;
}
#glue-titlebar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 2147483000;
  display: flex; align-items: center;
  height: var(--glue-titlebar-height);
  font-family: "Segoe UI", system-ui, -apple-system, "Ubuntu", sans-serif;
  font-size: 12px; user-select: none; -webkit-user-select: none;
  color: #1a1a1a; background: rgba(246,246,246,0.92);
  border-bottom: 1px solid rgba(0,0,0,0.08);
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
}
#glue-titlebar .glue-titlebar__drag {
  flex: 1; height: 100%; display: flex; align-items: center; gap: 8px;
  min-width: 0; padding: 0 12px;
}
#glue-titlebar .glue-titlebar__favicon {
  width: 16px; height: 16px; flex: 0 0 auto; border-radius: 2px;
  object-fit: contain; pointer-events: none;
}
#glue-titlebar .glue-titlebar__title {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  opacity: 0.72; font-weight: 500; pointer-events: none;
}
#glue-titlebar .glue-titlebar__controls {
  display: flex; align-items: stretch; height: 100%; flex: 0 0 auto;
}
#glue-titlebar button {
  appearance: none; border: 0; background: transparent; margin: 0;
  padding: 0; width: 46px; height: 100%; cursor: default;
  display: inline-flex; align-items: center; justify-content: center;
  color: inherit;
}
#glue-titlebar button:hover { background: rgba(0,0,0,0.06); }
#glue-titlebar button.glue-titlebar__close:hover { background: #e81123; color: #fff; }
#glue-titlebar .glue-titlebar__icon { width: 10px; height: 10px; display: block; position: relative; }
#glue-titlebar .glue-titlebar__icon--min::before {
  content: ""; position: absolute; left: 0; right: 0; top: 50%;
  border-top: 1px solid currentColor;
}
#glue-titlebar .glue-titlebar__icon--max {
  border: 1px solid currentColor; width: 10px; height: 10px; box-sizing: border-box;
}
#glue-titlebar .glue-titlebar__icon--close::before,
#glue-titlebar .glue-titlebar__icon--close::after {
  content: ""; position: absolute; left: 50%; top: 0; width: 1px; height: 12px;
  background: currentColor; transform-origin: center;
}
#glue-titlebar .glue-titlebar__icon--close::before { transform: translateX(-50%) rotate(45deg); }
#glue-titlebar .glue-titlebar__icon--close::after { transform: translateX(-50%) rotate(-45deg); }

html.glue-webview-chrome--macos #glue-titlebar {
  justify-content: center;
  background: rgba(246,246,246,0.88); color: #1d1d1f;
}
html.glue-webview-chrome--macos #glue-titlebar .glue-titlebar__controls {
  position: absolute; left: 10px; top: 0; height: 100%;
  display: flex; align-items: center; gap: 8px; padding: 0 4px;
}
html.glue-webview-chrome--macos #glue-titlebar button {
  width: 12px; height: 12px; border-radius: 50%; padding: 0;
}
html.glue-webview-chrome--macos #glue-titlebar button:hover { filter: brightness(0.95); }
html.glue-webview-chrome--macos #glue-titlebar .glue-titlebar__close { background: #ff5f57; }
html.glue-webview-chrome--macos #glue-titlebar .glue-titlebar__min { background: #febc2e; }
html.glue-webview-chrome--macos #glue-titlebar .glue-titlebar__max { background: #28c840; }
html.glue-webview-chrome--macos #glue-titlebar .glue-titlebar__icon { display: none; }
html.glue-webview-chrome--macos #glue-titlebar .glue-titlebar__drag {
  justify-content: center; padding: 0 72px; gap: 8px;
}
html.glue-webview-chrome--macos #glue-titlebar .glue-titlebar__favicon {
  width: 14px; height: 14px;
}
html.glue-webview-chrome--macos #glue-titlebar .glue-titlebar__title {
  opacity: 0.85; font-weight: 600; font-size: 13px;
}

html.glue-webview-chrome--linux #glue-titlebar {
  background: #2c2c2c; color: #f2f2f2;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
html.glue-webview-chrome--linux #glue-titlebar button:hover { background: rgba(255,255,255,0.08); }
html.glue-webview-chrome--linux #glue-titlebar button.glue-titlebar__close:hover { background: #e81123; color: #fff; }
html.glue-webview-chrome--linux #glue-titlebar .glue-titlebar__title { opacity: 0.9; }
`;
        document.head.appendChild(style);

        let bar = document.createElement('div');
        bar.id = 'glue-titlebar';
        bar.setAttribute('role', 'banner');

        let controls = document.createElement('div');
        controls.className = 'glue-titlebar__controls';
        controls.setAttribute('role', 'group');
        controls.setAttribute('aria-label', 'Window controls');

        function mkBtn(action, label, iconClass, extraClass) {
            let btn = document.createElement('button');
            btn.type = 'button';
            btn.className = extraClass || '';
            btn.setAttribute('aria-label', label);
            btn.setAttribute('title', label);
            btn.dataset.glueWin = action;
            let icon = document.createElement('span');
            icon.className = 'glue-titlebar__icon ' + iconClass;
            icon.setAttribute('aria-hidden', 'true');
            btn.appendChild(icon);
            return btn;
        }

        let minBtn = mkBtn('minimize', 'Minimize', 'glue-titlebar__icon--min', 'glue-titlebar__min');
        let maxBtn = mkBtn('maximize', 'Maximize', 'glue-titlebar__icon--max', 'glue-titlebar__max');
        let closeBtn = mkBtn('close', 'Close', 'glue-titlebar__icon--close', 'glue-titlebar__close');

        let drag = document.createElement('div');
        drag.className = 'glue-titlebar__drag pywebview-drag-region';
        let favicon = document.createElement('img');
        favicon.className = 'glue-titlebar__favicon';
        favicon.alt = '';
        favicon.decoding = 'async';
        favicon.src = glue._titlebar_icon_url();
        favicon.addEventListener('error', function() {
            favicon.remove();
        });
        drag.appendChild(favicon);
        let titleEl = document.createElement('div');
        titleEl.className = 'glue-titlebar__title';
        titleEl.textContent = title;
        drag.appendChild(titleEl);

        if(os === 'macos'){
            controls.appendChild(closeBtn);
            controls.appendChild(minBtn);
            controls.appendChild(maxBtn);
            bar.appendChild(controls);
            bar.appendChild(drag);
        } else {
            bar.appendChild(drag);
            controls.appendChild(minBtn);
            controls.appendChild(maxBtn);
            controls.appendChild(closeBtn);
            bar.appendChild(controls);
        }

        bar.addEventListener('click', function(ev) {
            let btn = ev.target.closest('[data-glue-win]');
            if(!btn){
                return;
            }
            let action = btn.getAttribute('data-glue-win');
            if(action === 'minimize' && typeof glue.webview_minimize === 'function'){
                glue.webview_minimize()();
            } else if(action === 'maximize' && typeof glue.webview_toggle_maximize === 'function'){
                glue.webview_toggle_maximize()();
            } else if(action === 'close' && typeof glue.webview_close === 'function'){
                glue.webview_close()();
            }
        });

        document.body.appendChild(bar);
        glue._install_webview_resize_grips();
    },

    _install_webview_resize_grips: function() {
        // PyWebView frameless on Windows removes the OS resize border; add hit zones
        // that call into Win32 HT* resize via glue.webview_start_resize.
        if(!glue._webview || !glue._webview.resize_grips){
            return;
        }
        if(document.getElementById('glue-resize-layer')){
            return;
        }

        let style = document.createElement('style');
        style.id = 'glue-resize-style';
        style.textContent = `
#glue-resize-layer { position: fixed; inset: 0; z-index: 2147483645; pointer-events: none; }
#glue-resize-layer .glue-resize {
  position: absolute; pointer-events: auto; background: transparent;
}
#glue-resize-layer .glue-resize--top { top: 0; left: 8px; right: 8px; height: 6px; cursor: ns-resize; }
#glue-resize-layer .glue-resize--bottom { bottom: 0; left: 8px; right: 8px; height: 6px; cursor: ns-resize; }
#glue-resize-layer .glue-resize--left { top: 8px; left: 0; bottom: 8px; width: 6px; cursor: ew-resize; }
#glue-resize-layer .glue-resize--right { top: 8px; right: 0; bottom: 8px; width: 6px; cursor: ew-resize; }
#glue-resize-layer .glue-resize--top-left { top: 0; left: 0; width: 10px; height: 10px; cursor: nwse-resize; }
#glue-resize-layer .glue-resize--top-right { top: 0; right: 0; width: 10px; height: 10px; cursor: nesw-resize; }
#glue-resize-layer .glue-resize--bottom-left { bottom: 0; left: 0; width: 10px; height: 10px; cursor: nesw-resize; }
#glue-resize-layer .glue-resize--bottom-right { bottom: 0; right: 0; width: 10px; height: 10px; cursor: nwse-resize; }
`;
        document.head.appendChild(style);

        let layer = document.createElement('div');
        layer.id = 'glue-resize-layer';
        layer.setAttribute('aria-hidden', 'true');

        let edges = [
            'top', 'bottom', 'left', 'right',
            'top-left', 'top-right', 'bottom-left', 'bottom-right'
        ];
        edges.forEach(function(edge) {
            let el = document.createElement('div');
            el.className = 'glue-resize glue-resize--' + edge;
            el.dataset.glueResize = edge;
            el.addEventListener('mousedown', function(ev) {
                if(ev.button !== 0){
                    return;
                }
                ev.preventDefault();
                ev.stopPropagation();
                // Prefer pywebview.api — must run during mousedown (Win32 resize).
                let api = window.pywebview && window.pywebview.api;
                if(api && typeof api.webview_start_resize === 'function'){
                    api.webview_start_resize(edge);
                    return;
                }
                if(typeof glue.webview_start_resize === 'function'){
                    glue.webview_start_resize(edge)();
                }
            });
            layer.appendChild(el);
        });

        document.body.appendChild(layer);
    },

    _apply_window_chrome: function() {
        // glue.start(title=…) should win over page <title> for OS caption
        // (Chrome/Edge app mode) and keep document.title in sync with PyWebView.
        if(typeof glue._window_title === 'string' && glue._window_title.length){
            document.title = glue._window_title;
        }
        // Chrome/Edge caption icon comes from <link rel="icon"> / /favicon.ico.
        if(!document.querySelector('link[rel="icon"], link[rel="shortcut icon"]')){
            let link = document.createElement('link');
            link.rel = 'icon';
            link.href = '/favicon.ico';
            document.head.appendChild(link);
        }
    },

    _init: function() {
        glue._mock_py_functions();

        document.addEventListener("DOMContentLoaded", function(event) {
            let page = window.location.pathname.substring(1);
            glue._apply_window_chrome();
            glue._position_window(page);
            glue._install_webview_chrome();

            let websocket_addr = (glue._host + '/glue').replace('http', 'ws');
            websocket_addr += ('?page=' + page);
            glue._websocket = new WebSocket(websocket_addr);

            glue._websocket.onopen = function() {
                for(let i = 0; i < glue._py_functions.length; i++){
                    let py_function = glue._py_functions[i];
                    glue._import_py_function(py_function);
                }

                while(glue._mock_queue.length > 0) {
                    let call = glue._mock_queue.shift();
                    glue._websocket.send(glue._toJSON(call));
                }
            };
            glue._websocket.onmessage = function (e) {
                let message = JSON.parse(e.data);
                if(message.hasOwnProperty('call') ) {
                    // Python making a function call into us
                    if(!(message.name in glue._exposed_functions)) {
                        glue._send_return(
                            message.call,
                            'error',
                            null,
                            {
                                errorText: 'Function "' + message.name + '" is not exposed',
                                errorTraceback: ''
                            }
                        );
                        return;
                    }
                    try {
                        let return_val = glue._exposed_functions[message.name](...message.args);
                        Promise.resolve(return_val).then(function(value) {
                            glue._send_return(message.call, 'ok', value, {});
                        }).catch(function(err) {
                            glue._send_return(message.call, 'error', null, glue._error_payload(err));
                        });
                    } catch(err) {
                        glue._send_return(message.call, 'error', null, glue._error_payload(err));
                    }
                } else if(message.hasOwnProperty('return')) {
                    // Python returning a value to us
                    if(message['return'] in glue._call_return_callbacks) {
                        if(message['status']==='ok'){
                            glue._call_return_callbacks[message['return']].resolve(message.value);
                        }
                        else if(message['status']==='error' &&  glue._call_return_callbacks[message['return']].reject) {
                                glue._call_return_callbacks[message['return']].reject(message['error']);
                        }
                    }
                } else {
                    throw 'Invalid message ' + message;
                }

            };
        });
    }
};

glue._init();
