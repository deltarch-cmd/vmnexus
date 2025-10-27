function sortDropdown() {
    const options = $('#alumno option');
    options.sort((a, b) => a.text.localeCompare(b.text));
    $('#alumno').html(options);
}

function removeMatricula(id) {
    // Add the item back to the dropdown
    const selectedText = $(`#matriculas-container .table tbody tr[data-id="${id}"] input[type="text"]`).val();
    $('#alumno').append(new Option(selectedText, id));

    // Remove the row from the table
    $(`#matriculas-container .table tbody tr[data-id="${id}"]`).remove();

    // Sort the dropdown
    sortDropdown();

    // Clear the search input
    $('.select2-search__field').val('');
    $('#alumno').trigger('change'); // Update Select2
}

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Select2
    $('#alumno').select2({
        placeholder: 'Seleccione un alumno',
        theme: 'bootstrap4',
        width: '100%',
        allowClear: true
    });

    // Sort the dropdown
    sortDropdown();

    // Add remove functionality for existing rows
    const removeMatriculaButtons = document.querySelectorAll('.btn-remove-matricula');
    removeMatriculaButtons.forEach((button) => {
        button.addEventListener('click', (event) => {
            const id = event.target.closest('tr').dataset.id;
            removeMatricula(id);
        });
    });

    // Handle item selection
    $('#alumno').on('select2:select', function (e) {
        const selectedId = e.params.data.id;
        const selectedText = e.params.data.text;

        // Add the selected item to the table
        $('#matriculas-container .table tbody').append(`
            <tr data-id="${selectedId}">
                <input type="hidden" name="alumnos-ids[]" value="${selectedId}">
                <td>
                    <input type="text" class="form-control" name="matricula_nombre[]" value="${selectedText}" readonly>
                </td>
                <td>
                    <button type="button" class="btn btn-outline-danger btn-sm btn-remove-matricula">Eliminar</button>
                </td>
            </tr>
        `);

        // Remove the selected item from the dropdown
        const option = $(this).find(`option[value="${selectedId}"]`);
        option.remove();
        $(this).trigger('change'); // Update Select2

        // Add remove functionality to the new "Eliminar" button
        const removeButton = $('#matriculas-container .table tbody tr:last-child .btn-remove-matricula');
        removeButton.on('click', () => {
            removeMatricula(selectedId);
        });
    });
});