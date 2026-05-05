// static/js/reader.js

class BookReader {
    constructor(htmlContent, config) {
        this.pages = [];
        this.chapters = [];          // { title, startPage }
        this.currentPage = 1;
        this.totalPages = 1;
        this.textId = config.textId;
        this.serverPage = config.serverPage;
        this.saveUrl = config.saveUrl;
        this.saveTimeout = null;

        this.viewport = document.getElementById('viewport');
        this.pageContent = document.getElementById('page-content');
        this.prevBtn = document.getElementById('prev-page');
        this.nextBtn = document.getElementById('next-page');
        this.currentPageSpan = document.getElementById('current-page');
        this.totalPagesSpan = document.getElementById('total-pages');
        this.fontSizeDisplay = document.getElementById('font-size-display');

        // Навигация по главам
        this.chaptersBtn = document.getElementById('chapters-btn');
        this.chaptersModal = document.getElementById('chapters-modal');
        this.chaptersList = document.getElementById('chapters-list');
        this.closeChaptersBtn = document.getElementById('close-chapters');

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
        // Удаляем все HTML-теги, кроме заголовочных (h1-h3), чтобы потом найти главы
        // Но сохраняем структуру для пагинации.
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
        this.currentPage = this.determineStartPage();
        this.buildChapters();       // строим список глав после пагинации
        this.updatePage();
    }

    determineStartPage() {
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

    // --- Работа с главами ---
    buildChapters() {
        this.chapters = [];
        // Регулярное выражение для поиска заголовков h1, h2, h3 (открывающий тег)
        const headingRegex = /<h[123][^>]*>(.*?)<\/h[123]>/i;

        this.pages.forEach((pageContent, index) => {
            const match = pageContent.match(headingRegex);
            if (match) {
                // Извлекаем текст заголовка, убирая возможные HTML-теги внутри
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = match[1];
                const title = tempDiv.textContent.trim();
                if (title) {
                    this.chapters.push({
                        title: title,
                        startPage: index + 1   // страницы нумеруются с 1
                    });
                }
            }
        });

        // Обновляем модальное окно с главами, если оно открыто
        this.renderChaptersList();
        // Если мы на какой-то странице, можно подсветить текущую главу (опционально)
    }

    renderChaptersList() {
        if (!this.chaptersList) return;
        this.chaptersList.innerHTML = '';
        if (this.chapters.length === 0) {
            this.chaptersList.innerHTML = '<li class="list-group-item text-muted">Главы не найдены</li>';
            return;
        }
        this.chapters.forEach((chapter, idx) => {
            const li = document.createElement('li');
            li.className = 'list-group-item list-group-item-action';
            li.textContent = chapter.title;
            li.addEventListener('click', () => {
                this.goToPage(chapter.startPage);
                this.closeChaptersModal();
            });
            // Подсветка текущей главы
            if (this.currentPage >= chapter.startPage) {
                // если текущая страница >= начала этой главы, считаем её текущей (найдём последнюю такую)
                li.classList.add('active');
                // снимем active с предыдущих
                const allItems = this.chaptersList.querySelectorAll('.list-group-item');
                allItems.forEach(item => item.classList.remove('active'));
                li.classList.add('active');
            }
            this.chaptersList.appendChild(li);
        });
    }

    openChaptersModal() {
        if (this.chaptersModal) {
            this.renderChaptersList();
            this.chaptersModal.style.display = 'block';
        }
    }

    closeChaptersModal() {
        if (this.chaptersModal) {
            this.chaptersModal.style.display = 'none';
        }
    }
    // -----------------------

    updatePage() {
        this.pageContent.innerHTML = this.pages[this.currentPage - 1] || '';
        this.currentPageSpan.textContent = this.currentPage;
        this.totalPagesSpan.textContent = this.totalPages;
        this.prevBtn.disabled = this.currentPage <= 1;
        this.nextBtn.disabled = this.currentPage >= this.totalPages;
        this.saveProgress();
        // Обновим подсветку главы в модальном окне, если оно открыто
        if (this.chaptersModal && this.chaptersModal.style.display === 'block') {
            this.renderChaptersList();
        }
    }

    saveProgress() {
        localStorage.setItem(`reader_progress_${this.textId}`, this.currentPage);

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
                }).catch(() => { });
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

        // Кнопка "Содержание"
        if (this.chaptersBtn) {
            this.chaptersBtn.addEventListener('click', () => this.openChaptersModal());
        }
        if (this.closeChaptersBtn) {
            this.closeChaptersBtn.addEventListener('click', () => this.closeChaptersModal());
        }
        // Закрытие по клику вне модального окна
        window.addEventListener('click', (e) => {
            if (e.target === this.chaptersModal) {
                this.closeChaptersModal();
            }
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

document.addEventListener('DOMContentLoaded', () => {
    if (window.READER_CONTENT) {
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