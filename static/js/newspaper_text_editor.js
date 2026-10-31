// Простой визуальный редактор текста статьи для конструктора газеты.
// Работает поверх textarea с газетной разметкой (##, ###, >, ---, <b>, <i>)
// и полностью управляется кнопками — размечать текст вручную не нужно.
(function () {
    'use strict';

    function escapeHtml(s) {
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    // Разметка -> HTML предпросмотра (совпадает с NewspaperBlock.get_content_html)
    function renderPreview(text) {
        if (!text || !text.trim()) {
            return '<p class="text-muted mb-0">Текст статьи появится здесь, когда вы начнёте печатать.</p>';
        }
        var html = '';
        text.split('\n').forEach(function (rawLine) {
            var line = rawLine.trim();
            if (!line) return;
            if (/^[-—*]{3,}$/.test(line)) { html += '<hr class="news-rule">'; return; }
            if (line.indexOf('### ') === 0) { html += '<h4 class="news-section-sub">' + inline(line.slice(4)) + '</h4>'; return; }
            if (line.indexOf('## ') === 0 || line.indexOf('# ') === 0) {
                var t = line.replace(/^#+\s*/, '');
                html += '<h3 class="news-section-title">' + inline(t) + '</h3>';
                return;
            }
            if (line.indexOf('> ') === 0) { html += '<blockquote class="news-quote">' + inline(line.slice(2)) + '</blockquote>'; return; }
            if (line === '>') return; // пустая строка-маркер, игнорируем
            html += '<p>' + inline(line) + '</p>';
        });
        return html;
    }

    // Разрешённые inline-теги остаются как есть, остальные экранируются
    function inline(s) {
        return s
            .replace(/<(\/?)(b|i|strong|em|u)>/gi, '<$1$2>')
            .replace(/<a\s+href="([^"]*)"[^>]*>/gi, function (m, href) {
                return /^https?:\/\//i.test(href) ? '<a href="' + href + '">' : '';
            })
            .replace(/<\/a>/gi, '</a>')
            .replace(/<(?!\/?(?:b|i|strong|em|u|a)\b)[^>]*>/gi, '');
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('.np-text-editor').forEach(function (wrap) {
            var ta = wrap.querySelector('textarea');
            if (!ta) return;
            var preview = wrap.querySelector('.np-preview-body');

            // ---------- низкоуровневые операции с выделением ----------
            function replaceRange(start, end, newText, selStart, selEnd) {
                ta.focus();
                ta.setSelectionRange(start, end);
                try {
                    if (!document.execCommand('insertText', false, newText)) throw new Error('no exec');
                } catch (e) {
                    var v = ta.value;
                    ta.value = v.slice(0, start) + newText + v.slice(end);
                }
                if (selStart != null) ta.setSelectionRange(selStart, selEnd == null ? selStart : selEnd);
                sync();
            }

            function surround(open, close, placeholder) {
                var s = ta.selectionStart, e = ta.selectionEnd;
                var sel = ta.value.slice(s, e);
                // повторное нажатие снимает форматирование
                if (sel && ta.value.slice(s - open.length, s) === open &&
                    ta.value.slice(e, e + close.length) === close) {
                    replaceRange(s - open.length, e + close.length, sel,
                        s - open.length, s - open.length + sel.length);
                    return;
                }
                if (!sel) sel = placeholder || 'текст';
                replaceRange(s, e, open + sel + close, s + open.length, s + open.length + sel.length);
            }

            function insertAtLineStart(prefix) {
                var v = ta.value, s = ta.selectionStart;
                var lineStart = v.lastIndexOf('\n', s - 1) + 1;
                var lineEnd = v.indexOf('\n', s);
                if (lineEnd === -1) lineEnd = v.length;
                var line = v.slice(lineStart, lineEnd).replace(/^(#{1,3}\s|>\s|---+\s*)/, '');
                var newLine = prefix + line;
                replaceRange(lineStart, lineEnd, newLine, lineStart + newLine.length);
            }

            function addLink() {
                var s = ta.selectionStart, e = ta.selectionEnd;
                var sel = ta.value.slice(s, e) || 'ссылка';
                var url = window.prompt('Вставьте адрес ссылки, например https://пример.рф', 'https://');
                if (!url || !/^https?:\/\//i.test(url)) return;
                var tag = '<a href="' + url + '">' + sel + '</a>';
                replaceRange(s, e, tag, s + tag.length);
            }

            // ---------- привязка кнопок ----------
            function bind(name, handler) {
                wrap.querySelectorAll('[data-action="' + name + '"]').forEach(function (btn) {
                    btn.addEventListener('click', function (ev) {
                        ev.preventDefault();
                        handler();
                    });
                });
            }

            bind('bold', function () { surround('<b>', '</b>', 'выделенный текст'); });
            bind('italic', function () { surround('<i>', '</i>', 'курсив'); });
            bind('link', addLink);
            bind('h2', function () { insertAtLineStart('## '); });
            bind('h3', function () { insertAtLineStart('### '); });
            bind('quote', function () { insertAtLineStart('> '); });
            bind('rule', function () {
                var s = ta.selectionStart, v = ta.value;
                var before = (s > 0 && v[s - 1] !== '\n') ? '\n' : '';
                var block = before + '---\n';
                replaceRange(s, ta.selectionEnd, block, s + block.length);
            });
            bind('clear', function () {
                var s = ta.selectionStart, e = ta.selectionEnd;
                var sel = ta.value.slice(s, e);
                if (!sel) return;
                var clean = sel
                    .replace(/<\/?(?:b|i|strong|em|u)>/gi, '')
                    .replace(/<a\s+href="[^"]*">/gi, '').replace(/<\/a>/gi, '')
                    .replace(/^#{1,3}\s/gm, '').replace(/^>\s/gm, '');
                replaceRange(s, e, clean, s, s + clean.length);
            });

            // горячие клавиши
            ta.addEventListener('keydown', function (ev) {
                if (!(ev.ctrlKey || ev.metaKey)) return;
                var k = ev.key.toLowerCase();
                if (k === 'b') { ev.preventDefault(); surround('<b>', '</b>'); }
                else if (k === 'i') { ev.preventDefault(); surround('<i>', '</i>'); }
                else if (k === 'k') { ev.preventDefault(); addLink(); }
            });

            // ---------- предпросмотр ----------
            var timer = null;
            function sync() {
                if (!preview) return;
                clearTimeout(timer);
                timer = setTimeout(function () {
                    preview.innerHTML = renderPreview(ta.value);
                }, 250);
            }
            ta.addEventListener('input', sync);
            if (preview) preview.innerHTML = renderPreview(ta.value);
        });
    });
})();
