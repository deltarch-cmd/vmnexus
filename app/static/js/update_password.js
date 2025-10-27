// Script para comprobar que las dos contraseñas coinciden

function updatePassword() {
    var password = document.getElementById("new_password").value;
    var password2 = document.getElementById("confirm_password").value;
    if (password != password2) {
        alert("Las contraseñas no coinciden");
        return false;
    }
    return true;
}
document.getElementById("update-password-button").addEventListener("submit", updatePassword);
