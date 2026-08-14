const togglePassword = document.getElementById("togglePassword");
const password = document.getElementById("password");
const togglePasswordIcon = document.getElementById("togglePasswordIcon");

if (togglePassword && password && togglePasswordIcon) {

    togglePassword.addEventListener("click", function () {

        if (password.type === "password") {

            password.type = "text";

            togglePasswordIcon.classList.remove("bi-eye");
            togglePasswordIcon.classList.add("bi-eye-slash");

        } else {

            password.type = "password";

            togglePasswordIcon.classList.remove("bi-eye-slash");
            togglePasswordIcon.classList.add("bi-eye");

        }

    });

}