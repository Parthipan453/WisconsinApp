/* ====== ERIC CODE START ====== */

/* Live page updates for application pages.
 *
 * Reads <script id="live-config" type="application/json"> for {"appId": ...}.
 *   - appId = application pk  -> subscribe to that application's events
 *   - appId = "me"            -> subscribe to the connected user's events
 *
 * Containers opt in with:
 *   data-live-event="event_a event_b"        (space separated event names)
 *   data-live-url="/path?partial=block"       (returns only that block's HTML)
 *
 * When a matching event arrives the block is re-fetched and swapped in.
 * Events are hints only - the server is always the source of truth.
 */
(function () {
  'use strict';

  var cfg = null;
  var cfgEl = document.getElementById('live-config');
  if (cfgEl) {
    try { cfg = JSON.parse(cfgEl.textContent || '{}'); } catch (e) { cfg = null; }
  }
  var firstRegion = document.querySelector('[data-live-event]');
  var appId = (cfg && cfg.appId) ||
              (firstRegion && firstRegion.getAttribute('data-live-app')) ||
              '';
  if (!appId || appId === 'none') return;

  var wsProto = location.protocol === 'https:' ? 'wss://' : 'ws://';
  var wsUrl = wsProto + location.host + '/ws/app-events/' + encodeURIComponent(appId) + '/';

  var socket = null;
  var reconnectDelay = 1000;
  var suspended = false;
  var closedByUs = false;
  var lastEvent = {};
  var queues = {};

  function reify(el) {
    var snap = {};
    var fields = el.querySelectorAll('textarea, input, select');
    for (var i = 0; i < fields.length; i++) {
      var f = fields[i];
      snap[(f.name || '') + ':' + i] = (f.value === undefined) ? '' : f.value;
    }
    el._liveState = snap;
  }

  function dirtyRegion(el) {
    var snap = el._liveState;
    if (!snap) return false;
    var fields = el.querySelectorAll('textarea, input, select');
    for (var i = 0; i < fields.length; i++) {
      var f = fields[i];
      if (document.activeElement === f) return true;
      var key = (f.name || '') + ':' + i;
      if (!(key in snap)) continue;
      var cur = (f.value === undefined) ? '' : f.value;
      if (snap[key] != null && cur !== snap[key]) return true;
    }
    return false;
  }

  function refreshBlock(el) {
    if (el.hasAttribute('data-live-disabled')) return;
    var url = el.getAttribute('data-live-url');
    if (!url) return;

    if (dirtyRegion(el)) {
      /* Someone is typing in this block - do not clobber their work. */
      el.setAttribute('data-live-paused', '1');
      return;
    }
    el.removeAttribute('data-live-paused');

    var run = queues[url] || (queues[url] = Promise.resolve());
    queues[url] = run.then(function () {
      return fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        cache: 'no-store',
      })
        .then(function (r) { if (!r.ok) throw new Error('refresh ' + r.status); return r.text(); })
        .then(function (html) {
          if (!document.body.contains(el)) return;
          el.innerHTML = html;
          reify(el);
          window.dispatchEvent(new Event('live:swapped'));
        })
        .catch(function () { /* keep last good content while offline */ });
    });
  }

  function handleEvent(name, data) {
    var key = name + ':' + (data && data.app || '') + ':' + (data && data.ts || 0);
    var now = Date.now();
    if (lastEvent[key] && now - lastEvent[key] < 2000) return; /* dedupe */
    lastEvent[key] = now;

    var nodes = document.querySelectorAll('[data-live-event]');
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var events = (el.getAttribute('data-live-event') || '').split(/\s+/);
      if (events.indexOf(name) !== -1) refreshBlock(el);
    }
  }

  function hydrateAll() {
    var nodes = document.querySelectorAll('[data-live-event]');
    for (var i = 0; i < nodes.length; i++) refreshBlock(nodes[i]);
    /* Snapshot fields so later typing is not clobbered by refresh blocks. */
    for (var j = 0; j < nodes.length; j++) reify(nodes[j]);
  }

  function scheduleReconnect() {
    if (suspended) return;
    var delay = reconnectDelay + Math.floor(Math.random() * 1000);
    reconnectDelay = Math.min(reconnectDelay * 1.6, 30000);
    setTimeout(function () {
      if (!suspended && (!socket || socket.readyState > 1)) connect();
    }, delay);
  }

  function connect() {
    closedByUs = false;
    try {
      socket = new WebSocket(wsUrl);
    } catch (e) {
      scheduleReconnect();
      return;
    }
    socket.onopen = function () { reconnectDelay = 1000; hydrateAll(); };
    socket.onmessage = function (ev) {
      var msg;
      try { msg = JSON.parse(ev.data); } catch (e) { return; }
      if (msg && msg.type === 'live') handleEvent(msg.event, msg);
    };
    socket.onerror = function () { try { socket.close(); } catch (e) {} };
    socket.onclose = function () { if (!closedByUs) scheduleReconnect(); };
  }

  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      suspended = true;
      closedByUs = true;
      if (socket) { try { socket.close(); } catch (e) {} }
    } else {
      var was = suspended;
      suspended = false;
      closedByUs = false;
      if (was && (!socket || socket.readyState > 1)) connect();
    }
  });

  connect();
})();

/* ====== ERIC CODE END ====== */