// app/static/js/scripts.js

// Пример: Подтверждение удаления текста
document.addEventListener('DOMContentLoaded', function () {
    const deleteForms = document.querySelectorAll('form[action^="/delete-text"]');
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            const confirmDelete = confirm('Вы уверены, что хотите удалить этот текст?');
            if (!confirmDelete) {
                event.preventDefault();
            }
        });
    });
});
