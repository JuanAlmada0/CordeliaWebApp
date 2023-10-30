
/* Alert messages */

document.addEventListener('DOMContentLoaded', function() {
    var alert = document.querySelector('.alert');
    if (alert) {
        alert.classList.add('fade-out');
        setTimeout(function() {
            alert.classList.add('fade-out-active');
        }, 1250);
    }
});

function confirmAction(message) {
    var result = confirm(message);

    if (result) {
        var form = event.target;
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'confirm';
        input.value = 'true';
        form.appendChild(input);
        form.submit();
    } else {
        alert('Action canceled.');
        return false;
    }
}

/* Maintenance modal */

var dressCount = parseInt(document.getElementById('dressCountInput').value);

function addDressId() {
    var newField = document.createElement("div");
    newField.innerHTML = '<div class="form-group"> <label for="dress_ids-' + dressCount + '-dress_id">Dress ID</label> <input class="form-control" id="dress_ids-' + dressCount + '-dress_id" name="dress_ids-' + dressCount + '-dress_id" type="number"> <button type="button" class="btn btn-danger btn-sm" onclick="removeDressId(this)">Remove</button> </div>';
    document.getElementById("dress_ids").appendChild(newField);
    dressCount++;
}

function removeDressId(button) {
    var parentDiv = button.parentElement;
    parentDiv.remove();
}