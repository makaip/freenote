let noteTree = null;
let selectedNote = null;
let selectedNoteContentLastSave = null;
let selectedNoteTitleLastSave = null;
let openNotebooks = new Set();


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
    console.log(noteId, noteId === null, noteId === undefined);

    if (noteId === null || noteId === undefined) {
        selectedNote = null;
        selectedNoteContentLastSave = null;
        selectedNoteTitleLastSave = null;
        document.getElementById("content").innerHTML = "";
        document.getElementById("title").innerHTML = "";
        return;
    }

    if (noteId === selectedNote) {
        return;
    }

    if (selectedNote !== null) {
        save();
    }

    fetch(`/api/notes/${noteId}`).then(r => r.json()).then(data => {
        if (data === null) {
            // note doesn't exist
            selectNote(null);
            return;
        }

        selectedNote = data;

        selectedNoteContentLastSave = data.content;
        selectedNoteTitleLastSave = data.title;

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


/**
 * Makes the notebook with the given id open, and all parent notebooks open. Used to open a notebook when adding a new
 * note or notebook to it.
 *
 * @param id {number} The id of the notebook to open
 */
function openNotebook(id) {
    let notebook = document.getElementById(`noteobject-${id}`);
    if (notebook === null) {
        return;
    }

    notebook.open = true;
    openNotebooks.add(id);

    let parent = notebook.parentNode;
    while (parent !== null && parent.tagName === "DETAILS") {
        parent.open = true;
        parent = parent.parentNode;
        openNotebooks.add(parseInt(parent.id.split("-")[1]));
    }
}


function newNoteObject(id, type) {
    // Make the notebook open
    openNotebook(id);

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
        openNotebook(id);  // sometimes the openNotebook function in the beginning is too early, so call it again
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

            if (selectedNote !== null && traverseNoteTree(selectedNote.id) === null) {
                selectNote(null);
            }
        }
    });
}


function toggleExpandedNotebook(id) {
    if (openNotebooks.has(id)) {
        openNotebooks.delete(id);
    } else {
        openNotebooks.add(id);
    }
}


function notesToHtmlTree(notes) {
    let html = "<ul>";

    notes["notes"].forEach(note => {
        if (note.type === "notebook") {
            html += `<details ${openNotebooks.has(note.id) ? "open" : ""} id="noteobject-${note.id}"><summary onclick="toggleExpandedNotebook(${note.id})">${note.title} <span onclick="newNoteObject(${note.id}, 'note')">New Note</span> <span onclick="newNoteObject(${note.id}, 'notebook')">New Notebook</span>`;

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

    if (selectedNoteContentLastSave === document.getElementById("content").innerHTML && selectedNoteTitleLastSave === document.getElementById("title").innerHTML) {
        return;
    }

    let autosaveText = document.getElementById("autosave-notif");
    autosaveText.innerHTML = "Saving...";

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
            selectedNoteContentLastSave = document.getElementById("content").innerHTML;
            selectedNoteTitleLastSave = document.getElementById("title").innerHTML;
            autosaveText.innerHTML = "Saved!";
        } else {
            console.log("Failed to save note. Response: ", response);
            autosaveText.innerHTML = "Failed to save note";
        }

        setTimeout(() => {
            autosaveText.innerHTML = "";
        }, 2000);
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

    // autosave
    setInterval(save, 5000);

    updateTree();
});


