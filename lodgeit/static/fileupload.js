var filefieldcount = 1;

function addField(){
    $('form input:file').last().after($( "<input />", {
                "type": "file",
                "name": "file_" + filefieldcount++
    }));
}

function fileinputmonitor(){
    $('input[type="file"]').change(addField);
}

$(fileinputmonitor);
