var url_root = window.location.href.substring(0, window.location.href.indexOf('/', 8));

function addathlete()
{
    var athlete_id = document.getElementById('athlete').value;
    var division = document.getElementById('division').value;
    var status = document.getElementById('add_athlete_status');
    status.innerHTML = "";

    if (athlete_id.length >= 3 && athlete_id.length <= 9 && !isNaN(athlete_id) && division.length >= 3 && division.length <= 6)
    {
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open( "GET", url_root + '/addathlete/' + athlete_id + '/' + division, false ); // false for synchronous request
        xmlHttp.send( null );

        if (xmlHttp.status == 200)
        {
            if (IsJsonString(xmlHttp.responseText))
            {
                athlete = JSON.parse(xmlHttp.responseText);

                status.innerHTML = athlete['firstname'] + ' ' + athlete['lastname'] + ' added to ' + division;

                var oldRow = document.getElementById(athlete_id + '_row');

                if (oldRow != null)
                {
                    oldRow.remove();
                }

                var table = document.getElementById(division);
                var row = table.insertRow(-1);
                row.id = athlete_id + '_row';
                var nameCell = row.insertCell(0)
                var idCell = row.insertCell(1);

                nameCell.innerHTML = athlete['firstname'] + ' ' + athlete['lastname'];
                idCell.innerHTML = athlete['id'];
            }
            else
            {
                status.innerHTML = xmlHttp.responseText;
            }
        }
        else
        {
            status.innerHTML = xmlHttp.status + ': Failed to add athlete';
        }
    }
    else
    {
        alert('You must submit a valid Strava athlete number');
    }


}

function removeathlete(athlete_id)
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", url_root + '/removeathlete/' + athlete_id, false ); // false for synchronous request
    xmlHttp.send( null );

    if (xmlHttp.status == 200)
    {
        var oldRow = document.getElementById(athlete_id + '_row');

        if (oldRow != null)
        {
            oldRow.remove();
        }
    }
    else
    {
        status.innerHTML = xmlHttp.status + ': Failed to remove athlete';
    }
}

function setsotw()
{
    var newSoTW = document.getElementById('segment').value;

    if (newSoTW.length >= 3 && !isNaN(newSoTW))
    {
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open( "GET", url_root + '/setsotw/' + newSoTW, false ); // false for synchronous request
        xmlHttp.send( null );
        alert(xmlHttp.responseText);
    }
    else
    {
        alert('You must submit a valid Strava segment number');
    }
}

function IsJsonString(str) {
    try {
        JSON.parse(str);
    } catch (e) {
        return false;
    }
    return true;
}