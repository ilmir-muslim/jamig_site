// static/js/studio_text_form.js

(function() {
    window.addEventListener('DOMContentLoaded', function() {
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
                    [{'header': [1, 2, 3, false]}],
                    [{'align': []}],
                    ['blockquote', 'code-block'],
                    [{'list': 'ordered'}, {'list': 'bullet'}],
                    ['link', 'image'],
                    ['clean']
                ]
            },
            placeholder: 'Начните писать статью...'
        });

        if (contentHidden.value) {
            quill.root.innerHTML = contentHidden.value;
        }

        function syncContent() {
            contentHidden.value = quill.root.innerHTML;
        }

        form.addEventListener('submit', function() {
            syncContent();
        });

        if (publishBtn && statusSelect) {
            publishBtn.addEventListener('click', function(e) {
                e.preventDefault();
                statusSelect.value = 'published';
                syncContent();
                form.submit();
            });
        }

        if (statusSelect && !statusSelect.value) {
            statusSelect.value = 'draft';
        }

        // ========= ЗАГРУЗКА ФАЙЛА =========
        const fileInput = document.getElementById('file-upload-input');
        if (fileInput) {
            fileInput.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (!file) return;

                const ext = file.name.split('.').pop().toLowerCase();
                if (ext === 'txt') {
                    const reader = new FileReader();
                    reader.onload = function(ev) {
                        const text = ev.target.result;
                        // Экранируем угловые скобки и заменяем переводы строк на <br>
                        const html = text
                            .replace(/&/g, '&amp;')   // сначала амперсанд
                            .replace(/</g, '&lt;')
                            .replace(/>/g, '&gt;')
                            .replace(/\n/g, '<br>');
                        quill.root.innerHTML = html;
                        syncContent();
                    };
                    reader.readAsText(file, 'UTF-8');
                } else if (ext === 'docx') {
                    const reader = new FileReader();
                    reader.onload = function(ev) {
                        const arrayBuffer = ev.target.result;
                        mammoth.convertToHtml({arrayBuffer: arrayBuffer})
                            .then(function(result) {
                                quill.root.innerHTML = result.value;
                                syncContent();
                            })
                            .catch(function(err) {
                                console.error('Ошибка конвертации docx:', err);
                                alert('Не удалось прочитать файл. Возможно, он повреждён.');
                            });
                    };
                    reader.readAsArrayBuffer(file);
                } else {
                    alert('Неподдерживаемый формат. Пожалуйста, выберите .txt или .docx');
                }
                // Сброс выбора, чтобы можно было загрузить тот же файл повторно
                fileInput.value = '';
            });
        }
        // =================================
    });
})();