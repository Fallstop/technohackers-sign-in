var nameList = [];
const options = {
    includeScore: true,
    threshold: 0.2
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
        htmlResults += "<div class='person'>" + namesToDisplay[i]["item"] + "</div>";
    }
    $('#search-results-container').html(htmlResults);
}

$(document).ready(function () {
    loadNames();
    $('#search-input').keyup(function(){
        console.log($('#search-input').val())
        displayNames(fuse.search($('#search-input').val()));
    })
})