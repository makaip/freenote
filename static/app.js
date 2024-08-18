let noteTree = null;


function getNoteContent(noteId) {
    fetch(`/api/notes/${noteId}`).then(r => r.json()).then(data => {
        document.getElementById("note").innerHTML = data.content;
    });
}

function notesToHtmlTree(notes) {
    let html = "<ul>";

    notes["notes"].forEach(note => {
        if (note.type === "notebook") {
            html += "<details><summary>" + note.title + "</summary>";
            html += notesToHtmlTree(note);
        } else {
            html += `<li onclick="getNoteContent(${note.id})">${note.title}</li>`;
        }
    });

    html += "</ul>";

    return html;
}


document.addEventListener('DOMContentLoaded', () => {
    // request the data from the server
    fetch("/api/notes").then(r => r.json()).then(data => {
        noteTree = data;
        document.getElementById("notes").innerHTML = notesToHtmlTree({notes: [data]});
    });
});