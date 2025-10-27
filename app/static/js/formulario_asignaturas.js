function updateFileName(fileInput) {
    fileInput.addEventListener('change', (event) => {
        const fileName = event.target.files[0] ? event.target.files[0].name : 'Ningún archivo seleccionado';
        const textInput = fileInput.closest('td').querySelector('input[type="text"]');
        textInput.value = fileName;
    });
}

function labButtonEvent(labsContainer, idCounter) {
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
        <input type="hidden" name="lab-ids[]" value="">
        <td>
            <input type="text" class="form-control" name="labs[]" value="" placeholder="Nombre del laboratorio" required>
        </td>
        <td class="input-group">
            <input type="text" class="form-control" style="width: 60%;" name="lab-file-names[]" readonly value="Ningún archivo seleccionado">
            <input type="file" name="lab-files[]" id="file-${idCounter}" class="inputfile" accept=".pdf" />
            <label class="d-flex align-items-center justify-content-center text-center" for="file-${idCounter}" style="width: 30%;">Choose a file</label>
        </td>
        <td>
            <button type="button" class="btn btn-outline-danger btn-sm btn-remove-lab">Eliminar</button>
        </td>
    `;

    labsContainer.appendChild(newRow);

    // Add remove functionality to the new "Eliminar" button
    const removeButton = newRow.querySelector('.btn-remove-lab');
    removeButton.addEventListener('click', () => {
        labsContainer.removeChild(newRow);
    });

    return newRow;
}

function horarioButtonEvent(horariosContainer) {
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
        <input type="hidden" name="horario-ids[]" value="">
        <td>
            <select name="dias[]" class="form-control" required>
                <option value="">Seleccione un día</option>
                <option value="mon">Lunes</option>
                <option value="tue">Martes</option>
                <option value="wed">Miércoles</option>
                <option value="thu">Jueves</option>
                <option value="fri">Viernes</option>
                <option value="sat">Sábado</option>
                <option value="sun">Domingo</option>
            </select>
        </td>
        <td>
            <input type="time" class="form-control" name="horas-inicio[]" required>
        </td>
        <td>
            <input type="time" class="form-control" name="horas-fin[]" required>
        </td>
        <td>
            <button type="button" class="btn btn-outline-danger btn-sm btn-remove-horario">Eliminar</button>
        </td>
    `;

    horariosContainer.appendChild(newRow);

    // Add remove functionality to the new "Eliminar" button
    const removeButton = newRow.querySelector('.btn-remove-horario');
    removeButton.addEventListener('click', () => {
        horariosContainer.removeChild(newRow);
    });

    return newRow;
}

// Validate all the data before submitting the form
function validateLabData() {
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
    return isValid;
}

function validateHorarioData() {
    const dias = document.querySelectorAll('select[name="dias[]"]');
    const horasInicio = document.querySelectorAll('input[name="hora-inicio[]"]');
    const horasFin = document.querySelectorAll('input[name="hora-fin[]"]');
    const horariosSet = new Set();

    for (let i = 0; i < dias.length; i++) {
        const dia = dias[i].value;
        const horaInicio = horasInicio[i].value;
        const horaFin = horasFin[i].value;

        if (!dia || !horaInicio || !horaFin) {
            alert('Todos los campos de los horarios deben estar llenos.');
            isValid = false;
            break;
        }
        // Se comprueba que la hora de inicio sea menor a la hora de fin
        const inicio = new Date(`01/01/2000 ${horaInicio}`);
        const fin = new Date(`01/01/2000 ${horaFin}`);
        if (inicio >= fin) {
            alert('La hora de inicio debe ser menor a la hora de fin.');
            isValid = false;
            break;
        }

        if (horariosSet.has(`${dia}-${horaInicio}-${horaFin}`)) {
            alert('No se pueden repetir horarios.');
            isValid = false;
            break;
        }
        // TODO: Comprobar que no haya horarios que se traslapen

        horariosSet.add(`${dia}-${horaInicio}-${horaFin}`);
    }
    return isValid;
}

document.addEventListener('DOMContentLoaded', () => {
    const labsContainer = document.querySelector('#labs-container tbody'); // Target the table body
    const horariosContainer = document.querySelector('#horarios-container tbody'); // Target the table body

    const addLabButton = document.getElementById('btn-add-lab'); // Add button
    const addHorarioButton = document.getElementById('btn-add-horario'); // Add button

    let uniqueLabId = Date.now();
    //let uniqueHorarioId = Date.now(); // TODO: Check if this is useful

    // Add remove functionality for existing rows
    const removeLabButtons = document.querySelectorAll('.btn-remove-lab');
    removeLabButtons.forEach((button) => {
        button.addEventListener('click', (event) => {
            const row = event.target.closest('tr'); // Find the closest row
            labsContainer.removeChild(row);
        });
    });

    const removeHorarioButtons = document.querySelectorAll('.btn-remove-horario');
    removeHorarioButtons.forEach((button) => {
        button.addEventListener('click', (event) => {
            const row = event.target.closest('tr'); // Find the closest row
            horariosContainer.removeChild(row);
        });
    });

    // Function to add a new lab row
    addLabButton.addEventListener('click', () => {
        // Add a new row to the labs table with its functionality
        newRow = labButtonEvent(labsContainer, uniqueLabId);
        uniqueLabId += 1; // Increment the lab count

        // Update the file name when a file is selected
        const fileInput = newRow.querySelector('input[type="file"]');
        updateFileName(fileInput);
    });

    // Function to add a new horario row
    addHorarioButton.addEventListener('click', () => {
        // Add a new row to the horarios table with its functionality
        newRow = horarioButtonEvent(horariosContainer);
        //uniqueHorarioId += 1; // Increment the horario count
    });

    // Validation before form submission
    const form = document.querySelector('form'); // Adjust the selector to your form ID/class if needed
    form.addEventListener('submit', (event) => {
        if (!validateLabData() || !validateHorarioData()) {
            event.preventDefault();
        }
    });

    // Update the file name when a file is selected
    document.querySelectorAll('input[type="file"]').forEach(updateFileName);
});
