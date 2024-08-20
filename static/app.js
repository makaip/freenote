let noteTree = null;
let selectedNote = null;
let selectedNoteContentLastSave = null;


function traverseNoteTree(noteId) {
    let stack = [noteTree];

    while (stack.length > 0) {
        let current = stack.pop();

        if (current.id === noteId) {
            return current;
        }

        if (current.type === "notebook") {
            current.notes.forEach(note => {
                stack.push(note);
            });
        }
    }

    return null;
}


function selectNote(noteId) {
    if (noteId === selectedNote) {
        return;
    }

    if (selectedNote !== null) {
        save();
    }

    fetch(`/api/notes/${noteId}`).then(r => r.json()).then(data => {
        selectedNote = data;

        selectedNoteContentLastSave = data.content;
        document.getElementById("content").innerHTML = data.content;
        document.getElementById("title").innerHTML = data.title;
    });
}


function onTitleUpdate() {
    if (selectedNote === null) {
        return;
    }

    // change the title of the note in noteTree, then update the tree html
    let note = traverseNoteTree(selectedNote.id);
    note.title = document.getElementById("title").innerHTML;
    document.getElementById("notes").innerHTML = notesToHtmlTree({notes: [noteTree]});
}


function newNoteObject(id, type) {
    fetch("api/new-noteobject", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            parent: id,
            type: type
        })
    }).then(response => {
        if (!response.ok) {
            console.log("Failed to create new note");
        } else {
            updateTree();
        }
    });
}


function deleteNoteobject(id) {
    fetch("api/delete-noteobject", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            id: id
        })
    }).then(response => {
        if (!response.ok) {
            console.log("Failed to delete note");
        } else {
            updateTree();
        }
    });
}


function notesToHtmlTree(notes) {
    let html = "<ul>";

    notes["notes"].forEach(note => {
        if (note.type === "notebook") {
            html += `<details><summary>${note.title} <span onclick="newNoteObject(${note.id}, 'note')">New Note</span> <span onclick="newNoteObject(${note.id}, 'notebook')">New Notebook</span>`;

            if (note.id !== 0) {  // root notebook, do not delete
                html += ` <span onclick="deleteNoteobject(${note.id})">Delete</span>`;
            }

            html += `</summary>`;

            html += notesToHtmlTree(note);
        } else {
            html += `<li onclick="selectNote(${note.id})">${note.title} <span onclick="deleteNoteobject(${note.id})">Delete</span></li>`;
        }
    });

    html += "</ul>";

    return html;
}


function save() {
    if (selectedNote === null) {
        return;
    }

    if (selectedNoteContentLastSave === document.getElementById("content").innerHTML) {
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


function updateTree() {
    fetch("/api/notes").then(r => r.json()).then(data => {
        noteTree = data;
        document.getElementById("notes").innerHTML = notesToHtmlTree({notes: [data]});
    });
}


document.addEventListener('DOMContentLoaded', () => {
    document.getElementById("title").addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
        }
    });

    document.getElementById("title").addEventListener("input", onTitleUpdate);

    updateTree();
});