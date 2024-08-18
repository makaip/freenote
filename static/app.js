
function notesToHtmlTree(notes) {
    let html = "<ul>";

    notes["notes"].forEach(note => {
        if (note.type === "notebook") {
            html += "<details><summary>" + note.title + "</summary>";
            html += notesToHtmlTree(note);
        } else {
            html += `<li>${note.title}</li>`;
        }
    });

    html += "</ul>";

    return html;
}


document.addEventListener('DOMContentLoaded', () => {
    console.log("App loaded");

    // request the data from the server
    fetch("/api/notes").then(r => r.json()).then(data => {
        document.getElementById("notes").innerHTML = notesToHtmlTree({notes: [data]});
    });
});