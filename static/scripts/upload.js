
// Checks if at least one of the multiple select colors or fabrics are selected
document.querySelector('.upload-form').addEventListener('submit', function(e) {
    const colorChecked = document.querySelectorAll('input[name="color_id"]:checked').length;
    const fabricChecked = document.querySelectorAll('input[name="fabric_id"]:checked').length;
    let isValid = true;

    // Validate colors
    const colorError = document.getElementById('color-error');
    if (colorChecked === 0) {
        colorError.style.display = 'block';
        isValid = false;
    } else {
        colorError.style.display = 'none';
    }

    // Validate fabrics
    const fabricError = document.getElementById('fabric-error');
    if (fabricChecked === 0) {
        fabricError.style.display = 'block';
        isValid = false;
    } else {
        fabricError.style.display = 'none';
    }

    if (!isValid) {
        e.preventDefault(); // Prevent form submission
    }
});
