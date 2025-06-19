let currentTaskId = null;
let fullChatHistory = [];

document.getElementById('pdfUploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const fileInput = document.getElementById('pdfFile');
    const file = fileInput.files[0];

    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please upload a valid PDF file.');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/home/uploadfiles', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });

        const result = await response.json();
        const statusDiv = document.getElementById('uploadStatus');

        if (response.ok) {
            currentTaskId = result.task_id;
            statusDiv.innerHTML = `<strong>${result.message}</strong>`;
            document.getElementById('checkStatusBtn').style.display = 'inline-block';
        } else {
            statusDiv.innerHTML = `<span class="text-danger">Error: ${result.detail || result.error}</span>`;
        }
    } catch (error) {
        document.getElementById('uploadStatus').innerHTML =
            `<span class="text-danger">Upload failed: ${error.message}</span>`;
    }
});

// Handle Check Status Button
document.getElementById('checkStatusBtn').addEventListener('click', function () {
    checkTaskStatus(currentTaskId);
});

async function checkTaskStatus(taskId) {
    const statusDiv = document.getElementById('statusResult');

    try {
        const response = await fetch(`/home/status/${taskId}`, {
            method: 'GET',
            credentials: 'include'
        });

        const result = await response.json();

        if (response.ok) {
            let statusText = result.state || 'Unknown';
            let colorClass = 'text-secondary';
            let extraMessage = '';

            if (statusText.toLowerCase() === 'success') {
                colorClass = 'text-success';
            } else if (statusText.toLowerCase() === 'pending') {
                colorClass = 'text-warning';
                extraMessage = '<br><small>Please wait while processing…</small>';

                // Auto-refresh after 5 seconds
                setTimeout(() => checkTaskStatus(taskId), 10000);
            }

            statusDiv.innerHTML = `<strong>Status:</strong> <span class="${colorClass}">${statusText}</span>${extraMessage}`;
        } else {
            statusDiv.innerHTML = `<span class="text-danger">Error: ${result.detail || result.error}</span>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<span class="text-danger">Failed to fetch status: ${error.message}</span>`;
    }
}


document.getElementById('queryForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const queryInput = document.getElementById('queryInput');
    const userQuery = queryInput.value.trim();

    if (!userQuery) return;

    fullChatHistory.push({ user: userQuery, bot: '<span class="thinking-indicator"></span>' });
    renderChat(); 
    queryInput.value = ''; 

    try {
        const response = await fetch('/query/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ query: userQuery })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Server returned an error');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let botResponseText = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            botResponseText += decoder.decode(value, { stream: true });
            
            const thinkingIndicator = document.querySelector('.thinking-indicator');
            if (thinkingIndicator) {
                thinkingIndicator.parentElement.innerHTML = botResponseText.replace(/\n/g, '<br>');
            }
        }

        fullChatHistory[fullChatHistory.length - 1].bot = botResponseText;
        renderChat();

    } catch (error) {
        console.error('Query failed:', error);
        fullChatHistory[fullChatHistory.length - 1].bot = `Error: ${error.message}`;
        renderChat();
    }
});

// Clear Chat History
document.getElementById('clearChatBtn').addEventListener('click', async function () {
    const response = await fetch('/query/history', {
        method: 'DELETE',
        credentials: 'include'
    });

    if (response.ok) {
        fullChatHistory = [];
        renderChat();
    } else {
        const result = await response.json();
        alert(result.error || result.detail || 'Error clearing chat.');
    }
});

function renderChat() {
    const chatHistoryDiv = document.getElementById('chatHistory');
    chatHistoryDiv.innerHTML = ''; 

    for (const item of fullChatHistory) {
        if (item.bot) {
            const botDiv = document.createElement('div');
            botDiv.className = 'chat-entry bot';
            botDiv.innerHTML = `<div class="message">${item.bot.replace(/\n/g, '<br>')}</div>`;
            chatHistoryDiv.prepend(botDiv);
        }
        const userDiv = document.createElement('div');
        userDiv.className = 'chat-entry user';
        userDiv.innerHTML = `<div class="message">${item.user}</div>`;
        chatHistoryDiv.prepend(userDiv);
    }
}

const getAllVectorsBtn = document.getElementById('getAllVectors');
if (getAllVectorsBtn) { 
    getAllVectorsBtn.addEventListener('click', async () => {
        const response = await fetch('/admin/get_vector/', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
        });
        const data = await response.json();
        const vectorCountDiv = document.getElementById("vectorCount");

        const vectorList = document.getElementById("vectorList");
        vectorCountDiv.textContent = `Total Vectors: ${data.count}`;
        vectorList.innerHTML = "";
        data.ids.forEach(id => {
            const div = document.createElement("div");
            div.textContent = id;
            vectorList.appendChild(div);
        });
    });
}

const fetchVectorBtn = document.getElementById("fetchVector");
if (fetchVectorBtn) {
    fetchVectorBtn.addEventListener('click', async () => {
        const id = document.querySelector("input[name='vector_id']").value;
        const response = await fetch(`/admin/get_vector_by_id/${id}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
        });
        const data = await response.text();
        document.getElementById("vectorResult").textContent = data;
    });

}

const deleteVectorBtn = document.getElementById("deleteVector");
if(deleteVectorBtn){
    deleteVectorBtn.addEventListener('click', async () => {
        const id = document.querySelector("input[name='vector_id']").value;
        const confirmed = confirm("Are you sure you want to delete this vector?");
        if (!confirmed) return;

        const response = await fetch(`/admin/delete_vector/${id}`, {
            method: "DELETE",
            credentials: 'include'
        });

        if (response.status === 204) {
            alert("Vector deleted successfully.");
            document.getElementById("vectorResult").textContent = "";
        } else {
            const msg = await response.text();
            alert("Error: " + msg);
        }

    });
}
