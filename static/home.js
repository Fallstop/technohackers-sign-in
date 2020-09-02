var nameList = [];
const options = {
    includeScore: true,
    threshold: 0.3
}
var repeatAttendPersonDetails;

var fuse;
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
var rollbackList = [];

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
                $("#repeatAttendPersonDetails-time").html("<strong>"+repeatAttendPersonDetails["previous_time"]+"</strong>");
                $("#repeatAttendPersonDetails").modal('show');
            } else {
                $("#search-input").val("");
                $('#search-results-container').html("");
                $('#search-input').focus();
                rollbackList.push([response["id"], nameOfPerson]);
                console.log(rollbackList)
                $.notify({
                    // options
                    message: 'Signed in as <strong>' + nameOfPerson + '</strong>'
                }, {
                    // settings
                    type: 'success',
                    delay: 1000

                });
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
                    message: "Failed to undo sign in to server, response: " + response.status
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

})