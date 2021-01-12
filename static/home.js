var nameList = [];
var rollbackList = [];
var currentlyProcessingName = ""

const options = {
    includeScore: true,
    threshold: 0.3
}
var repeatAttendPersonDetails;

var timeoutDelay = 60000;

var timeoutID = window.setTimeout(clearScreen, timeoutDelay);

var fuse;

function restartTimer() {
    window.clearTimeout(timeoutID);
    timeoutID = window.setTimeout(clearScreen, timeoutDelay);
}
function loadNames() {
    $.ajax({
        url: '/getnames',
        type: 'GET',
        success: function (response) {
            console.log(response);
            nameList = response;
            fuse = new Fuse(response, options);
            $('#loading_icon').hide();
        },
        error: function (response) {
            $.notify({
                // options
                message: "Failed to get list of names from server, response: " + response.status + "<br>Trying again in 2s."
            }, {
                // settings
                type: 'danger',
                delay: 2000
            });

            setTimeout("loadNames()", 2000);
        }
    });
}

function displayNames(namesToDisplay) {
    console.log("displaying names")
    var htmlResults = "";
    for (var i = 0; i < namesToDisplay.length; i++) {
        htmlResults += "<div id='person-" + namesToDisplay[i]["item"] + "' class='person' tabindex='" + (i + 2) + "'>" + namesToDisplay[i]["item"] + "</div>";
    }
    htmlResults += "<div id='guest' class='person guest' tabindex='" + (i + 2) + "'>Sign in as a guest</div>";
    $('#search-results-container').html(htmlResults);
}

function signInPerson(nameOfPerson, signedUp, force) {
    currentlyProcessingName = nameOfPerson
    console.log("Signing in " + nameOfPerson);
    data = { "Name": nameOfPerson, "SignedUp": signedUp, "Force": force };
    console.log("Posting: ", data);
    $.ajax({
        url: '/signin',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (response) {
            console.log("Response: ", response);
            if (response["attendance_warning"]) {
                repeatAttendPersonDetails = response
                repeatAttendPersonDetails["signedUp"] = signedUp;
                $("#repeatAttendPersonDetails-time").html("<strong>" + repeatAttendPersonDetails["previous_time"] + "</strong>");
                $("#repeatAttendPersonDetails").modal('show');
            } else {
                rollbackList.push([response["id"], nameOfPerson]);
                // Special Argolia Stuff
                $("#askArgolia").modal('show');
                $("#askArgolia").focus();
                console.log($("#askArgolia"));


            }

        },
        error: function (response) {
            $.notify({
                // options
                message: "Failed to send sign in to server, response: " + response.status
            }, {
                // settings
                type: 'danger',
                delay: 2000
            });
        }
    })
}

function guestSignIn() {
    signInPerson($('#guest-name-input').val(), false, false);
    $("#guestSignInModal").modal('hide');
}

function repeatAttendSignIn() {
    $('#repeatAttendPersonSend').html('Sending...');
    signInPerson(repeatAttendPersonDetails['full_name'], repeatAttendPersonDetails['signedUp'], true);
    console.log('Signing in with force from modal');
    $('#repeatAttendPersonDetails').modal('hide');
    $('#repeatAttendPersonSend').html('Continue anyway');

}

function triggerGuestSignIn() {
    console.log("Triggering Guest Sign In");
    $("#guestSignInModal").modal('show');
    $("#guest-name-input").val($('#search-input').val());
    $("#guest-name-input").focus();
}

function clearScreen() {
    console.log("Timer ran out")
    if ($("#search-input").val() != "") {
        $("#search-input").val("");
        $('#search-results-container').html("");
    }
    $('#search-input').focus();
    $("#askArgolia").modal('hide')
    $("#askArgoliaUsername").modal('hide');
    $("#minecraftUsernameInput").removeClass("is-valid")
    $("#minecraftUsernameInput").removeClass("is-invalid")
    $("#minecraftUsernameInput").val("")
    restartTimer();
}

function checkArgolia() {
    console.log($("#attendingArgoliaCheckBox")[0])
    if ($("#attendingArgoliaCheckBox")[0].checked) {
        $("#askArgolia").modal('hide')
        $("#askArgoliaUsername").modal({
            backdrop: 'static'
        });
    } else {
        promptSuccessfulSignIn()
        $("#askArgolia").modal('hide')
    }
}

function checkUsernameAvailability(username) {
    $.ajax({
        url: "/argolia/check-username",
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            "username": username
        }),
        success: function (response) {
            result = JSON.parse(response)
            console.log(result["available"], result)
            if (result["available"]) {
                $("#minecraftUsernameInput").addClass("is-valid")
                $("#minecraftUsernameInput").removeClass("is-invalid")
                $("#minecraftUsernameInput").val("")
                createArgoliaAccount(username)
            } else {
                $("#minecraftUsernameInvalidHelp").html("Sorry, but that username has been taken!")
                $("#minecraftUsernameInput").removeClass("is-valid")
                $("#minecraftUsernameInput").addClass("is-invalid")
            }

        }
    })
}

function createArgoliaAccount(username) {
    $("#askArgoliaUsername").modal('hide');
    console.log({
        "username": username,
        "full_name": currentlyProcessingName
    });
    $.ajax({
        url: "/argolia/create-account",
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            "username": username,
            "full_name": currentlyProcessingName
        }),
        success: function (response) {
            console.log("Response: ",response)
            pin = JSON.parse(response)["pin"]
            promptSuccessfulSignIn("<br>Please pickup the printing receipt!")
            var printWindow = window.open('', '', 'height=200,width=400'); 
            printWindow.document.write(`
            <!DOCTYPE html>
            <html lang="en" >
            <head>
                <meta charset="utf-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    .content {
                        text-align: center;
                        font-size: 5mm;
                        filter: none;
                        padding: 2mm 4mm;
                    }
                    .title {
                        font-size: 9mm
                    }
                    .subtitle {
                        font-size: 7mm;
                    }
                    @page {
                        margin: 0;
                    }
                    @media print {
                        .content {
                            width: 55mm !important;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="content">
                    <div class="title">ARGOLIA</div>
                    <div class="description">
                    Welcome<br>
                    ${currentlyProcessingName}<br>
                    This is some key information about the event, <b>don't lose it!</b><br>
                    </div>
                    <div class="subtitle">Timetable</div>
                    <p>
                    Opening: 8:30 AM<br>
                    The Beginning: 9:00 AM<br>
                    Morning Tea: 10:30 AM<br>
                    Lunch: 12:45 PM<br>
                    Event Finish: 4:30 PM<br>
                    Closing: 5:30 PM<br>
                    </p>
                    <div class="subtitle">Wifi</div>
                    <p>
                    SSID: Questionable_5G<br>
                    Password: noquestions<br>
                    </p>
                    <div class="subtitle">Minecraft Account</div>
                    <p>
                    This will be your credentials for when you sign into Argolia:<br><br>
                    Username: ${username}<br>
                    Pin: ${pin}<br>
                    </p>
                </div>
            </body>
            </html>
            `);
            printWindow.addEventListener('afterprint', (event) => {
                console.log("Printing completed...");
                
                printWindow.close();
                window.focus()
              });
              setTimeout(function () {
                  console.log("Timeout yes")
                printWindow.close(); // Replace this line with your own 'afterprint' logic.
            }, 3000);
            printWindow.print();
            
        },
        error: function (response) {
            if (response.status == 500) {
                $.notify({
                    // options
                    message: "Failed to create account, please find a staff member, response: " + response
                }, {
                    // settings
                    type: 'danger',
                    delay: 5000
                });
            } else {
                $.notify({
                    // options
                    message: "Failed to create account, please contact a staff member, response: " + response.status
                }, {
                    // settings
                    type: 'danger',
                    delay: 5000
                });
            }
        }
    })
}

function submitArgoliaUsername() {
    username = $("#minecraftUsernameInput").val();
    if (!(username.length >= 3 && username.length <= 16)) {
        console.log("Username not valid")
        $("#minecraftUsernameInvalidHelp").html("Username is not valid. It has to be between 3-16 chars long.")
        $("#minecraftUsernameInput").removeClass("is-valid")
        $("#minecraftUsernameInput").addClass("is-invalid")
    }
    else if (!(/^[\d|\w]{3,16}$/.test(username))) {
        console.log("Username not valid")
        $("#minecraftUsernameInvalidHelp").html("Username is not valid. It has to only include a-Z,0-9 and '_'.")
        $("#minecraftUsernameInput").removeClass("is-valid")
        $("#minecraftUsernameInput").addClass("is-invalid")
    } else {
        checkUsernameAvailability(username)
    }
}

function undoSignIn() {
    if (rollbackList.length > 0) {
        userToUndo = rollbackList[rollbackList.length - 1];
        console.log("Canceling sign in of: ", userToUndo);
        $.ajax({
            url: '/deleteattendance',
            type: 'DELETE',
            contentType: 'application/json',
            data: JSON.stringify({ "id": userToUndo[0] }),
            success: function (response) {
                $.notify({
                    // options
                    message: 'Canceled attendance of <strong>' + userToUndo[1] + '</strong>'
                }, {
                    // settings
                    type: 'success',
                    delay: 1000
                });
                rollbackList.pop();
            },
            error: function (response) {
                $.notify({
                    // options
                    message: "Failed to cancel attendance" + userToUndo[1] + ", response: " + response.status
                }, {
                    // settings
                    type: 'danger',
                    delay: 2000
                });
            }
        });
    } else {
        $.notify({
            // options
            message: 'Nothing left to undo.'
        }, {
            // settings
            type: 'warning',
            delay: 2500
        });
    }

}

$(document).ready(function () {
    $("#search-input").val("");
    $('#search-input').focus();
    loadNames();
    $('#search-input').keyup(function (e) {
        console.log(e);
        if (e.code != "Enter") {
            console.log($('#search-input').val());
            if ($('#search-input').val()) {
                displayNames(fuse.search($('#search-input').val()));
            } else {
                $('#search-results-container').html('');
            }

        } else {
            var search = fuse.search($('#search-input').val())
            if (search.length > 0) {
                signInPerson(search[0]["item"], true, false)
            } else if ($('#search-input').val() != "") {
                triggerGuestSignIn();
            }
        }
    });
    $("#attendingArgoliaCheckBox").change(function () {
        if (this.checked) {
            $("#argoliaNextButton").html("Next")
        } else {
            $("#argoliaNextButton").html("Finish")
        }
    });

    $('#guest-name-input').keyup(function (e) {
        if (e.code == 'Enter') {
            guestSignIn();
        }
    })
    $('#guest-name-input').keyup(function (e) {
        if (e.code == 'Enter') {
            guestSignIn();
        }
    })
    $('#guest-name-input').keyup(function (e) {
        if (e.code == 'Enter') {
            guestSignIn();
        }
    })
    $(document).on('click', '.person', function (event) {
        if (this.id != "guest") {
            signInPerson(this.id.substring(7), true, false);
        } else {
            triggerGuestSignIn();
        }
    });
    $(document).on('keypress', '.person', function (e) {
        if (e.code == "Enter") {
            if (this.id != "guest") {
                signInPerson(this.id.substring(7), true, false);
            } else {
                triggerGuestSignIn();
            }
        }

    });
    $(document).on("keydown", "#argoliaUsernameForm", function (event) {
        if (event.key == "Enter") {
            submitArgoliaUsername()
            return false;
        }
        return true;
    });
    $(document).on("keydown", "#askArgolia", function (event) {
        if (event.key == "Enter") {
            checkArgolia()
        }
    });

    $(document).on('click keypress', restartTimer);

})

function promptSuccessfulSignIn(customText = "") {
    console.log("Successful signin")
    $.notify({
        // options
        message: `Signed in as <strong>${currentlyProcessingName}</strong>${customText}`
    }, {
        // settings
        type: 'success',
        delay: 1000
    });
    clearScreen()
}