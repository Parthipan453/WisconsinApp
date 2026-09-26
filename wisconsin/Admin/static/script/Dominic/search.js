(function () {

    function initSearch(wrapper, input, dropdown) {
        if (!wrapper || !input || !dropdown) return;

        const SEARCH_ENDPOINT = wrapper.dataset.searchUrl;

        let items = [];
        let activeIndex = -1;
        let debounceTimer = null;
        let requestToken = 0;
        let controller = null;

        function searchApi(query) {
            if (controller) controller.abort();
            controller = new AbortController();

            return fetch(SEARCH_ENDPOINT + '?q=' + encodeURIComponent(query), {
                signal: controller.signal,
                headers: { Accept: 'application/json' },
            })
            .then((res) => {
                if (!res.ok) throw new Error('Search request failed: ' + res.status);
                return res.json();
            })
            .then((data) => data.results || [])
            .catch((err) => {
                if (err.name === 'AbortError') return null;
                console.error(err);
                return [];
            });
        }

        function escapeHtml(str) {
            return str.replace(/[&<>"']/g, (c) => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
            }[c]));
        }

        function highlight(text, query) {
            if (!query) return escapeHtml(text);
            const idx = text.toLowerCase().indexOf(query.toLowerCase());
            if (idx === -1) return escapeHtml(text);
            return (
                escapeHtml(text.slice(0, idx)) +
                '<mark>' + escapeHtml(text.slice(idx, idx + query.length)) + '</mark>' +
                escapeHtml(text.slice(idx + query.length))
            );
        }

        function openDropdown() { dropdown.classList.add('is-open'); }

        function closeDropdown() {
            dropdown.classList.remove('is-open');
            activeIndex = -1;
        }

        function navigateTo(path) {
            window.location.href = path;
        }

        function renderLoading() {
            dropdown.innerHTML = '<div class="navbar__search-loading">Searching…</div>';
            openDropdown();
        }

        function renderEmpty(query) {
            dropdown.innerHTML =
                '<div class="navbar__search-empty">No results for "' + escapeHtml(query) + '"</div>';
            openDropdown();
        }

        function renderResults(results, query) {
            items = results;
            activeIndex = -1;

            if (!results.length) return renderEmpty(query);

            const groups = [];
            const groupMap = {};
            results.forEach((r) => {
                if (!groupMap[r.group]) {
                    groupMap[r.group] = [];
                    groups.push(r.group);
                }
                groupMap[r.group].push(r);
            });

            let html = '';
            let flatIndex = 0;
            groups.forEach((groupName) => {
                html += '<div class="navbar__search-group-label">' + escapeHtml(groupName) + '</div>';
                groupMap[groupName].forEach((item) => {
                    html +=
                        '<div class="navbar__search-item" data-index="' + flatIndex + '" data-path="' + escapeHtml(item.path) + '">' +
                        '<svg class="navbar__search-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/></svg>' +
                        '<div class="navbar__search-item-text">' +
                            '<span class="navbar__search-item-title">' + highlight(item.title, query) + '</span>' +
                            '<span class="navbar__search-item-path">' + escapeHtml(item.path) + '</span>' +
                        '</div>' +
                        '</div>';
                    flatIndex++;
                });
            });

            html +=
                '<div class="navbar__search-footer">' +
                '<span><kbd>↑</kbd><kbd>↓</kbd> to navigate</span>' +
                '<span><kbd>Enter</kbd> to select</span>' +
                '</div>';

            dropdown.innerHTML = html;
            openDropdown();

            dropdown.querySelectorAll('.navbar__search-item').forEach((el) => {
                el.addEventListener('mouseenter', () => setActive(Number(el.dataset.index)));
                el.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    navigateTo(el.dataset.path);
                });
            });
        }

        function setActive(index) {
            activeIndex = index;
            dropdown.querySelectorAll('.navbar__search-item').forEach((el) => {
                el.classList.toggle('is-active', Number(el.dataset.index) === index);
            });
            const activeEl = dropdown.querySelector('.navbar__search-item.is-active');
            if (activeEl) activeEl.scrollIntoView({ block: 'nearest' });
        }

        input.addEventListener('input', () => {
            const query = input.value.trim();
            clearTimeout(debounceTimer);

            if (!query) {
                closeDropdown();
                return;
            }

            renderLoading();
            const thisRequest = ++requestToken;

            debounceTimer = setTimeout(() => {
                searchApi(query).then((results) => {
                    if (results === null) return;
                    if (thisRequest !== requestToken) return;
                    renderResults(results, query);
                });
            }, 250);
        });

        input.addEventListener('keydown', (e) => {
            if (!dropdown.classList.contains('is-open') || !items.length) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setActive(Math.min(activeIndex + 1, items.length - 1));
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setActive(Math.max(activeIndex - 1, 0));
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (activeIndex >= 0) navigateTo(items[activeIndex].path);
            } else if (e.key === 'Escape') {
                closeDropdown();
            }
        });

        document.addEventListener('click', (e) => {
            if (!wrapper.contains(e.target)) closeDropdown();
        });
    }

    initSearch(
        document.getElementById('navbarSearch'),
        document.getElementById('navbarSearchInput'),
        document.getElementById('navbarSearchDropdown')
    );

    initSearch(
        document.getElementById('navbarSearch1'),
        document.getElementById('navbarSearchInput1'),
        document.getElementById('navbarSearchDropdown1')
    );

})();