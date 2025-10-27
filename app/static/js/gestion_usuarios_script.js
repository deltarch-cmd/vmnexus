document.addEventListener('DOMContentLoaded', () => {
    const userDataRow = document.querySelectorAll('tbody tr'); // table rows of users
    const searchInput = document.getElementById('search-input'); // search input

    // Filter by role and create a new list for the filtered users
    document.getElementById('role-filter').addEventListener('change', () => {
        const selectedRole = document.getElementById('role-filter').value;
        userDataRow.forEach((row) => {
            const role = row.querySelector('.user-role').textContent.trim().toLowerCase();
            if (selectedRole === 'all' || role === selectedRole) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });

    // Listen for input changes
    searchInput.addEventListener('input', () => {
        const searchValue = searchInput.value.trim().toLowerCase();
        userDataRow.forEach((row) => {
            const name = row.querySelector('.user-name').textContent.toLowerCase();
            if (name.includes(searchValue)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
});
