// Add the update file name function to the new rows
function updateFileName(fileInput) {
    fileInput.addEventListener('change', (event) => {
        const fileName = event.target.files[0] ? event.target.files[0].name : 'Ningún archivo seleccionado';
        const textInput = fileInput.closest('td').querySelector('input[type="text"]');
        textInput.value = fileName;
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const labsContainer = document.querySelector('#labs-container tbody'); // Target the table body
    const addLabButton = document.getElementById('btn-add-lab'); // Add button
    // We must keep count of the number of labs to avoid duplicate names
    let labCount = labsContainer.querySelectorAll('input[name="labs[]"]').length || 0;

    // Function to add a new lab row
    addLabButton.addEventListener('click', () => {
        // Create a new table row
        const newRow = document.createElement('tr');
        labCount += 1;
        newRow.innerHTML = `
            <td>
                <input type="text" class="form-control" name="labs[]" value="" placeholder="Nombre del laboratorio" required>
            </td>
            <td class="input-group">
                <input type="text" class="form-control" style="width: 65%;" name="lab-file-names[]" readonly value="Ningún archivo seleccionado">
                <input type="file" name="lab-files[]" id="file-${labCount}" class="inputfile" />
                <label class="d-flex align-items-center justify-content-center" for="file-${labCount}" style="width: 35%;">Seleccione un archivo</label>
            </td>
            <td>
                <button type="button" class="btn btn-outline-danger btn-sm btn-remove-lab">Eliminar</button>
            </td>
        `;

        // Add the row to the table body
        labsContainer.appendChild(newRow);

        // Add remove functionality to the new "Eliminar" button
        const removeButton = newRow.querySelector('.btn-remove-lab');
        removeButton.addEventListener('click', () => {
            labsContainer.removeChild(newRow);
            labCount -= 1; // Decrement the lab count
        });

        // Update the file name when a file is selected
        const fileInput = newRow.querySelector('input[type="file"]');
        updateFileName(fileInput);
    });

    // Add remove functionality for existing rows
    const removeLabButtons = document.querySelectorAll('.btn-remove-lab');
    removeLabButtons.forEach((button) => {
        button.addEventListener('click', (event) => {
            const row = event.target.closest('tr'); // Find the closest row
            labsContainer.removeChild(row);
            labCount -= 1; // Decrement the lab count
        });
    });

    // Validation before form submission
    const form = document.querySelector('form'); // Adjust the selector to your form ID/class if needed
    form.addEventListener('submit', (event) => {
        const labNames = document.querySelectorAll('input[name="labs[]"]');
        const labNamesSet = new Set();
        let isValid = true;

        labNames.forEach((input) => {
            const value = input.value.trim();
            if (!value) {
                alert('Todos los nombres de los laboratorios deben estar llenos.');
                isValid = false;
                return;
            }
            if (labNamesSet.has(value)) {
                alert('No se pueden repetir nombres de laboratorios.');
                isValid = false;
                return;
            }
            labNamesSet.add(value);
        });

        if (!isValid) {
            event.preventDefault(); // Prevent form submission if validation fails
        }
    });

    // Updating the file name when a file is selected
    document.querySelectorAll('input[type="file"]').forEach(updateFileName);
});
