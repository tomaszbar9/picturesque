function verify(formType) {
    var tags = document.getElementsByClassName("verify");
    let validation = true;
    var entryType;
    var val;
    var len;
    var alertField;

    // Clear alert fileds
    for (var tag of tags) {

        entryType = tag.id;
        alertField = document.getElementById(entryType + "Alert");

        alertField.innerHTML = ""
        alertField.style.border = "0";
        alertField.style.backgroundColor = "transparent";
        alertField.style.width = "100%";
        alertField.style.paddingLeft = "0";
    };

    // Check fields and show alert
    for (var tag of tags) {
        entryType = tag.id;
        val = document.forms[formType][entryType].value;
        len = val.length;
        alertField = document.getElementById(entryType + "Alert");

        switch (entryType) {
            case "username":
                if (len < 3) {
                    validation = showAlert(alertField, "Username must be at least 3 characters");
                };
                break;
            case "password":
                if (len < 8) {
                    validation = showAlert(alertField, "Password must be at leat 8 characters");
                } else if (!(/\d/.test(val) && /[a-zA-Z]/.test(val))) {
                    validation = showAlert(alertField, "Password must contain letters and digits");
                };
                break;
            case "confirmation":
                password = document.getElementById("password").value;
                if (val != password) {
                    validation = showAlert(alertField, "Confirmation does not match the password");
                };
                break;
            case "author":
            case "title":
            case "quote":
                if (!val) {
                    validation = showAlert(alertField, "This field cannot be empty");
                };
                break;
            case "picture-button":
                if (!val) {
                    validation = showAlert(alertField, "Please upload a picture");
                };
                break;
            case "search":
                if (len < 3) {
                    document.getElementById("search").value = "";
                    document.getElementById("search").placeholder = "Please enter at least 3 characters";
                    validation = false;
                };
                break;
        };
    };
    return validation;
};


function showAlert(field, msg) {
    field.innerHTML = msg;
    field.style.color = "red";
    field.style.fontSize = "small";
    return false;
};



function invalidInput(text, where) {
    var redFrame = document.getElementById(where);
    redFrame.innerHTML = text;
    redFrame.style.color = "white";
    redFrame.style.fontSize = "small";
    redFrame.style.border = "red";
    redFrame.style.backgroundColor = "rgb(255, 0, 0, 0.5)";
    redFrame.style.paddingLeft = "5px";
    redFrame.style.marginTop = "2px";
    redFrame.style.width = "240px";
};
