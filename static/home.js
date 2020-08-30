var nameList = [];
const options = {
    includeScore: true,
    threshold: 0.3
  }
  
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
        error: function(){
            loadNames();
        }
    });
}

function displayNames(namesToDisplay) {
    console.log("displaying names")
    var htmlResults = "";
    for (var i = 0; i < namesToDisplay.length; i++) {
        htmlResults += "<div id='person-"+namesToDisplay[i]["item"]+"' class='person' tabindex='"+(i+2)+"'>" + namesToDisplay[i]["item"] + "</div>";
    }
    htmlResults += "<div id='guest' class='person guest' tabindex='"+(i+2)+"'>Sign in as a guest</div>";
    $('#search-results-container').html(htmlResults);
}

function signInPerson(nameOfPerson,signedUp){
    console.log("Signing in " + nameOfPerson);
    console.log("Posting: "+JSON.stringify({"Name":nameOfPerson,"SignedUp":signedUp}));
    $.ajax({
        url: '/signin',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({"Name":nameOfPerson,"SignedUp":signedUp}),
        success: function (response) {
            $("#search-input").val("");
            $('#search-results-container').html("");
            $('#search-input').focus();
        },
        error: function(response){
            alert("Failed to send to server, response: "+response.status);
        }
    })
}
function guestSignIn(){
    signInPerson($('#guest-name-input').val(), false);
    $("#guestSignInModal").modal('hide');
}
function triggerGuestSignIn(){
    console.log("Triggering Guest Sign In");
    $("#guestSignInModal").modal('show');
    $("#guest-name-input").val($('#search-input').val());
    $("#guest-name-input").focus();
}

$(document).ready(function () {
    $("#search-input").val("");
    $('#search-input').focus();
    loadNames();
    $('#search-input').keyup(function(e){
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
                signInPerson(search[0]["item"], true)
            } else if ($('#search-input').val() != "") {
                triggerGuestSignIn();
            }
        }
    });
    $('#guest-name-input').keyup(function(e) {
        if (e.code == 'Enter') {
            guestSignIn();
        }
    })
    $(document).on('click','.person',function(event){
        if (this.id != "guest") {
            signInPerson(this.id.substring(7),true);
        } else {
            triggerGuestSignIn();
        }
        
    });

})