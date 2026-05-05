// static/js/studio_text_form.js

(function () {
    window.addEventListener('DOMContentLoaded', function () {
        // Получаем настройки из глобального объекта, переданного шаблоном
        const config = window.STUDIO_TEXT_CONFIG || {};
        const contentFieldId = config.contentFieldId || 'id_content';
        const editorContainerId = config.editorContainerId || 'quill-editor';
        const formId = config.formId || 'content-form';
        const statusFieldId = config.statusFieldId || 'id_status';
        const publishBtnId = config.publishBtnId || 'publish-btn';

        const contentHidden = document.getElementById(contentFieldId);
        const editorContainer = document.getElementById(editorContainerId);
        const form = document.getElementById(formId);
        const statusSelect = document.getElementById(statusFieldId);
        const publishBtn = document.getElementById(publishBtnId);

        if (!editorContainer || !contentHidden || !form) {
            console.error('Не найдены основные элементы редактора');
            return;
        }

        const quill = new Quill(editorContainer, {
            theme: 'snow',
            modules: {
                toolbar: [
                    ['bold', 'italic', 'underline', 'strike'],
                    [{ 'header': [1, 2, 3, false] }],
                    [{ 'align': [] }],
                    ['blockquote', 'code-block'],
                    [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                    ['link', 'image'],
                    ['clean']
                ]
            },
            placeholder: 'Начните писать статью...'
        });

        // Заполняем редактор существующим контентом
        if (contentHidden.value) {
            quill.root.innerHTML = contentHidden.value;
        }

        // Синхронизация содержимого редактора со скрытым полем
        function syncContent() {
            contentHidden.value = quill.root.innerHTML;
        }

        // Обработка отправки формы
        form.addEventListener('submit', function () {
            syncContent();
        });

        // Кнопка «Опубликовать»
        if (publishBtn && statusSelect) {
            publishBtn.addEventListener('click', function (e) {
                e.preventDefault();
                statusSelect.value = 'published';
                syncContent();
                form.submit();
            });
        }

        // Статус по умолчанию, если не задан
        if (statusSelect && !statusSelect.value) {
            statusSelect.value = 'draft';
        }
    });
})();