let noteTree = null;
let selectedNote = null;


function selectNote(noteId) {
    if (noteId === selectedNote) {
        return;
    }

    if (selectedNote !== null) {
        save();
    }

    fetch(`/api/notes/${noteId}`).then(r => r.json()).then(data => {
        selectedNote = data;

        document.getElementById("content").innerHTML = data.content;
        document.getElementById("title").innerHTML = data.title;
    });
}

function notesToHtmlTree(notes) {
    let html = "<ul>";

    notes["notes"].forEach(note => {
        if (note.type === "notebook") {
            html += "<details><summary>" + note.title + "</summary>";
            html += notesToHtmlTree(note);
        } else {
            html += `<li onclick="selectNote(${note.id})">${note.title}</li>`;
        }
    });

    html += "</ul>";

    return html;
}


function save() {
    if (selectedNote === null) {
        return;
    }

    fetch(`/api/modify-note`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            title: document.getElementById("title").innerHTML,
            content: document.getElementById("content").innerHTML,
            id: selectedNote.id
        })
    }).then(response => {
        if (response.ok) {
            console.log("Note saved");
        } else {
            console.error("Failed to save note");
        }
    });
}


document.addEventListener('DOMContentLoaded', () => {
    document.getElementById("title").addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
        }
    });

    // request the data from the server
    fetch("/api/notes").then(r => r.json()).then(data => {
        noteTree = data;
        document.getElementById("notes").innerHTML = notesToHtmlTree({notes: [data]});
    });
});