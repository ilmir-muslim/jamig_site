// static/js/reader.js

class BookReader {
    constructor(htmlContent, config) {
        this.pages = [];
        this.currentPage = 1;
        this.totalPages = 1;
        this.textId = config.textId;
        this.serverPage = config.serverPage;
        this.saveUrl = config.saveUrl;
        this.saveTimeout = null; // для debounce

        this.viewport = document.getElementById('viewport');
        this.pageContent = document.getElementById('page-content');
        this.prevBtn = document.getElementById('prev-page');
        this.nextBtn = document.getElementById('next-page');
        this.currentPageSpan = document.getElementById('current-page');
        this.totalPagesSpan = document.getElementById('total-pages');
        this.fontSizeDisplay = document.getElementById('font-size-display');

        // Восстанавливаем настройки из localStorage
        this.fontSize = this._loadSetting('reader_fontSize', 18);
        this.lineHeight = this._loadSetting('reader_lineHeight', 1.8);

        this.applySettings();
        this.loadContent(htmlContent);
        this.bindEvents();
    }

    _loadSetting(key, defaultValue) {
        const saved = localStorage.getItem(key);
        if (saved !== null) {
            const val = parseFloat(saved);
            return isNaN(val) ? defaultValue : val;
        }
        return defaultValue;
    }

    _saveSetting(key, value) {
        localStorage.setItem(key, value);
    }

    applySettings() {
        document.documentElement.style.setProperty('--reader-font-size', this.fontSize + 'px');
        document.documentElement.style.setProperty('--reader-line-height', this.lineHeight);
        this.fontSizeDisplay.textContent = Math.round(100 * this.fontSize / 18) + '%';
    }

    loadContent(html) {
        const testDiv = document.createElement('div');
        testDiv.style.cssText = `
            position: absolute; visibility: hidden;
            width: ${this.pageContent.clientWidth}px;
            font-size: var(--reader-font-size);
            line-height: var(--reader-line-height);
            white-space: pre-wrap; word-wrap: break-word;
        `;
        document.body.appendChild(testDiv);

        const pageHeight = this.pageContent.clientHeight;
        let remaining = html;
        this.pages = [];

        while (remaining.length > 0) {
            const midDiv = document.createElement('div');
            midDiv.style.cssText = testDiv.style.cssText;
            document.body.appendChild(midDiv);

            let low = 0, high = remaining.length, best = 0;
            while (low <= high) {
                const mid = Math.floor((low + high) / 2);
                midDiv.innerHTML = remaining.substring(0, mid);
                if (midDiv.scrollHeight <= pageHeight) {
                    best = mid;
                    low = mid + 1;
                } else {
                    high = mid - 1;
                }
            }
            this.pages.push(remaining.substring(0, best));
            remaining = remaining.substring(best).trimStart();
            document.body.removeChild(midDiv);
        }

        document.body.removeChild(testDiv);
        if (this.pages.length === 0) this.pages = [''];

        this.totalPages = this.pages.length;
        // Определяем стартовую страницу: сначала сервер, потом localStorage
        this.currentPage = this.determineStartPage();
        this.updatePage();
    }

    determineStartPage() {
        // Приоритет: серверный прогресс > localStorage > 1
        if (this.serverPage && this.serverPage >= 1 && this.serverPage <= this.totalPages) {
            return this.serverPage;
        }
        const local = localStorage.getItem(`reader_progress_${this.textId}`);
        if (local) {
            const page = parseInt(local, 10);
            if (page >= 1 && page <= this.totalPages) return page;
        }
        return 1;
    }

    updatePage() {
        this.pageContent.innerHTML = this.pages[this.currentPage - 1] || '';
        this.currentPageSpan.textContent = this.currentPage;
        this.totalPagesSpan.textContent = this.totalPages;
        this.prevBtn.disabled = this.currentPage <= 1;
        this.nextBtn.disabled = this.currentPage >= this.totalPages;
        this.saveProgress();
    }

    saveProgress() {
        // Локально сохраняем всегда мгновенно
        localStorage.setItem(`reader_progress_${this.textId}`, this.currentPage);

        // Отправляем на сервер с задержкой 800 мс после последнего вызова
        if (this.saveTimeout) clearTimeout(this.saveTimeout);
        this.saveTimeout = setTimeout(() => {
            if (this.saveUrl && navigator.onLine) {
                fetch(this.saveUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({
                        text_id: this.textId,
                        page_number: this.currentPage,
                    }),
                }).catch(() => { /* тихо */ });
            }
        }, 800);
    }

    goToPage(page) {
        if (page < 1 || page > this.totalPages) return;
        this.currentPage = page;
        this.updatePage();
    }

    nextPage() { if (this.currentPage < this.totalPages) this.goToPage(this.currentPage + 1); }
    prevPage() { if (this.currentPage > 1) this.goToPage(this.currentPage - 1); }

    changeFontSize(delta) {
        const fraction = (this.currentPage - 1) / (this.totalPages || 1);
        this.fontSize = Math.max(12, Math.min(32, this.fontSize + delta));
        this._saveSetting('reader_fontSize', this.fontSize);
        this.applySettings();
        const allHtml = this.pages.join(' ');
        this.loadContent(allHtml);
        this.goToPage(Math.max(1, Math.round(fraction * this.totalPages)));
    }

    bindEvents() {
        this.prevBtn.addEventListener('click', () => this.prevPage());
        this.nextBtn.addEventListener('click', () => this.nextPage());

        document.getElementById('font-plus').addEventListener('click', () => this.changeFontSize(2));
        document.getElementById('font-minus').addEventListener('click', () => this.changeFontSize(-2));

        // Тема
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.body.classList.remove('sepia-theme', 'dark-theme');
                const theme = e.target.dataset.theme;
                if (theme === 'sepia') document.body.classList.add('sepia-theme');
                if (theme === 'dark') document.body.classList.add('dark-theme');
                document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                localStorage.setItem('reader_theme', theme);
            });
        });

        // Горячие клавиши
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight') { e.preventDefault(); this.nextPage(); }
            if (e.key === 'ArrowLeft') { e.preventDefault(); this.prevPage(); }
        });

        // Ресайз
        window.addEventListener('resize', () => {
            const fraction = (this.currentPage - 1) / (this.totalPages || 1);
            const allHtml = this.pages.join(' ');
            this.loadContent(allHtml);
            this.goToPage(Math.max(1, Math.round(fraction * this.totalPages)));
        });
    }
}

// Вспомогательная функция получения CSRF‑токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    if (window.READER_CONTENT) {
        // Восстановить тему
        const savedTheme = localStorage.getItem('reader_theme') || 'light';
        if (savedTheme !== 'light') {
            document.body.classList.add(savedTheme + '-theme');
            const activeBtn = document.querySelector(`.theme-btn[data-theme="${savedTheme}"]`);
            if (activeBtn) activeBtn.classList.add('active');
            document.querySelector('.theme-btn[data-theme="light"]')?.classList.remove('active');
        }
        window.reader = new BookReader(window.READER_CONTENT, window.READER_CONFIG);
    }
});