var url_root = window.location.href.substring(0, window.location.href.indexOf('/', 8));

function addathlete()
{
    var athlete_input = document.getElementById('athlete');
    var lastSlash = athlete_input.value.lastIndexOf('/');
    var athlete_id = athlete_input.value.substring(lastSlash + 1);

    var paramsStart = athlete_id.indexOf('?');

    if  (paramsStart > 0)
    {
        athlete_id = athlete_id.substring(0, paramsStart);
    }

    athlete_input.value = athlete_id;

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
    var neutralSegment = [];

    var mainSegment = getCleanInputFromControl(document.getElementById('segment'));
    neutralSegment[0] = getCleanInputFromControl(document.getElementById('neutral_segment_1'));
    neutralSegment[1] = getCleanInputFromControl(document.getElementById('neutral_segment_2'));
    neutralSegment[2] = getCleanInputFromControl(document.getElementById('neutral_segment_3'));

    var status = document.getElementById('set_sotw_status');
    var paramString = "";

    for (var i = 0; i < 3; i++)
    {
        if (neutralSegment[i].length > 0)
        {
            if (!isNaN(neutralSegment[i]))
            {
                paramString = paramString + '/' + neutralSegment[i];
            }
            else
            {
                status.innerHTML = "All segments must be a numerical value";
            }
        }
    }

    if (mainSegment.length >= 3 && !isNaN(mainSegment))
    {
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open( "GET", url_root + '/setsotw/' + mainSegment + paramString, false ); // false for synchronous request
        xmlHttp.send( null );
        status.innerHTML = xmlHttp.responseText;
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

function getCleanInputFromControl(control)
{
    var oldValue = control.value;
    var lastSlash = oldValue.lastIndexOf('/');
    var cleanValue = oldValue.substring(lastSlash + 1);

    var paramsStart = cleanValue.indexOf('?');

    if  (paramsStart > 0)
    {
        cleanValue = cleanValue.substring(0, paramsStart);
    }

    return cleanValue;
}

function getSegmentDetails(control)
{
    setTimeout(function(){

        var control_id = control.id;
        control.value = getCleanInputFromControl(control);
        var segment_details_id = control_id + '_details';
        var segment_details = document.getElementById(segment_details_id);
        var segment_id = control.value

        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open( "GET", url_root + '/getsegment/' + segment_id, false ); // false for synchronous request
        xmlHttp.send( null );
        if (xmlHttp.status == 200 && IsJsonString(xmlHttp.responseText))
        {
            segment = JSON.parse(xmlHttp.responseText);
            segment_details.innerHTML = segment['name'] + ', ' + segment['distance'] + ' metres';
        }
        else
        {
            segment_details.innerHTML = 'Error retrieving segment: ' + xmlHttp.status.toString();
        }
    }, 4); //or 4
}