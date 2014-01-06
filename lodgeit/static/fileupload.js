var filefieldcount = 1;
var filefieldinc = 1;

function addField(e){
    if (e.target.value && filefieldcount < 5) {
            var field = $('form input:file').last().after($( "<input />", {
                        "type": "file",
                        "name": "file_" + filefieldinc++
            }));
            filefieldcount++;
            $('input:file').last().change(addField);
    }
    if (e.target.value == "" && filefieldcount > 1) {
            e.target.remove();
            filefieldcount--;
    }
}

function fileinputmonitor(){
    $('input:file').change(addField);
}

$(fileinputmonitor);
