// Simple JavaScript for Kiro playground
document.addEventListener('DOMContentLoaded', () => {
    console.log('JavaScript is working!');
    
    // DOM Elements
    const editModeBtn = document.getElementById('editModeBtn');
    const viewModeBtn = document.getElementById('viewModeBtn');
    const editModeView = document.getElementById('editModeView');
    const viewModeView = document.getElementById('viewModeView');
    const editor = document.getElementById('editor');
    const preview = document.getElementById('preview');
    const viewPreview = document.getElementById('viewPreview');
    const saveBtn = document.getElementById('saveBtn');
    const printBtn = document.getElementById('printBtn');
    const newFolderBtn = document.getElementById('newFolderBtn');
    const newFileBtn = document.getElementById('newFileBtn');
    const fileModal = document.getElementById('fileModal');
    const modalTitle = document.getElementById('modalTitle');
    const nameInput = document.getElementById('nameInput');
    const cancelBtn = document.getElementById('cancelBtn');
    const confirmBtn = document.getElementById('confirmBtn');
    
    // State
    let lastRenderedHTML = '';
    let currentFile = null;
    let lastSavedContent = '';
    let autoSaveTimer = null;
    let currentMode = 'edit'; // 'edit' or 'view'
    let modalAction = null; // 'file' or 'folder'
    let modalParentPath = '';
    let draggedItem = null; // For drag and drop
    
    // Event listeners for mode buttons
    if (editModeBtn) {
        editModeBtn.addEventListener('click', () => {
            console.log('Edit mode clicked');
            // Switch to edit mode
            currentMode = 'edit';
            editModeView.classList.remove('hidden');
            viewModeView.classList.add('hidden');
            editModeBtn.classList.add('bg-blue-500', 'text-white');
            editModeBtn.classList.remove('bg-gray-200', 'text-gray-700');
            viewModeBtn.classList.add('bg-gray-200', 'text-gray-700');
            viewModeBtn.classList.remove('bg-blue-500', 'text-white');
        });
    }
    
    if (viewModeBtn) {
        viewModeBtn.addEventListener('click', () => {
            console.log('View mode clicked');
            // Switch to view mode
            currentMode = 'view';
            editModeView.classList.add('hidden');
            viewModeView.classList.remove('hidden');
            viewModeBtn.classList.add('bg-blue-500', 'text-white');
            viewModeBtn.classList.remove('bg-gray-200', 'text-gray-700');
            editModeBtn.classList.add('bg-gray-200', 'text-gray-700');
            editModeBtn.classList.remove('bg-blue-500', 'text-white');
            
            // Save changes before switching to view mode
            if (currentFile && editor.value !== lastSavedContent) {
                saveFile();
            }
            
            // Render to view mode
            if (editor && editor.value) {
                renderKiro(true);
            }
        });
    }
    
    // Save button - changed to download .kiro file
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            downloadKiroFile();
        });
    }
    
    // Print button
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            downloadHtml();
        });
    }
    
    // New folder/file buttons
    if (newFolderBtn) {
        newFolderBtn.addEventListener('click', () => {
            showModal('folder', '');
        });
    }
    
    if (newFileBtn) {
        newFileBtn.addEventListener('click', () => {
            showModal('file', '');
        });
    }
    
    // Modal buttons
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            hideModal();
        });
    }
    
    if (confirmBtn) {
        confirmBtn.addEventListener('click', () => {
            handleModalConfirm();
        });
    }
    
    // Show file/folder creation modal
    function showModal(action, parentPath) {
        modalAction = action;
        modalParentPath = parentPath;
        
        modalTitle.textContent = action === 'file' ? '새 파일 생성' : '새 폴더 생성';
        nameInput.placeholder = action === 'file' ? '파일명.kiro' : '폴더명';
        nameInput.value = action === 'file' ? 'untitled.kiro' : '';
        
        fileModal.classList.remove('hidden');
        nameInput.focus();
    }
    
    // Hide modal
    function hideModal() {
        fileModal.classList.add('hidden');
    }
    
    // Handle modal confirm button click
    async function handleModalConfirm() {
        const name = nameInput.value.trim();
        if (!name) {
            alert('이름을 입력해주세요.');
            return;
        }
        
        // Validate file extension for files
        if (modalAction === 'file' && !name.endsWith('.kiro')) {
            alert('파일명은 .kiro로 끝나야 합니다.');
            return;
        }
        
        try {
            // First check if a file/folder with the same name already exists
            const fileStructure = await loadFileStructure();
            const itemPath = modalParentPath ? `${modalParentPath}/${name}` : name;
            
            // Function to check duplicates in the file structure
            const checkDuplicate = (items, path) => {
                if (!items) return false;
                
                // Direct check for root level items
                if (items.some(item => item.id === path)) {
                    return true;
                }
                
                // Check in folders for nested paths
                if (path.includes('/')) {
                    const pathParts = path.split('/');
                    const parentFolderName = pathParts[0];
                    const parentFolder = items.find(item => 
                        item.type === 'folder' && item.name === parentFolderName
                    );
                    
                    if (parentFolder && parentFolder.children) {
                        const remainingPath = pathParts.slice(1).join('/');
                        return checkDuplicate(parentFolder.children, remainingPath);
                    }
                }
                
                return false;
            };
            
            if (checkDuplicate(fileStructure, itemPath)) {
                showToast(`이미 같은 이름의 ${modalAction === 'file' ? '파일' : '폴더'}이 존재합니다`, true);
                return;
            }
            
            if (modalAction === 'folder') {
                // Create folder
                const folderPath = modalParentPath ? `${modalParentPath}/${name}` : name;
                
                const response = await fetch('/api/folder', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        path: folderPath
                    })
                });
                
                if (!response.ok) throw new Error('Failed to create folder');
                
                // Always refresh the file structure after creating a folder
                hideModal();
                await loadFileStructure();
                showToast('폴더가 생성되었습니다');
            } else {
                // Create file
                const filePath = modalParentPath ? `${modalParentPath}/${name}` : name;
                
                const response = await fetch('/api/file', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        path: filePath,
                        content: ''
                    })
                });
                
                if (!response.ok) throw new Error('Failed to create file');
                
                // Always refresh the file structure after creating a file
                hideModal();
                await loadFileStructure();
                // Then load the newly created file
                loadFile(filePath);
                showToast('파일이 생성되었습니다');
            }
        } catch (error) {
            console.error('Error creating item:', error);
            showToast(`생성 실패: ${error.message}`, true);
        }
    }
    
    // Move file to another folder
    async function moveFile(sourcePath, targetFolder) {
        try {
            // First, load the file content
            const response = await fetch(`/api/file?path=${encodeURIComponent(sourcePath)}`);
            if (!response.ok) throw new Error('Failed to load file');
            
            const data = await response.json();
            const content = data.content;
            
            // Create the new file path
            const fileName = sourcePath.split('/').pop();
            const newPath = targetFolder === '' ? fileName : `${targetFolder}/${fileName}`;
            
            // Create the file in the new location
            const createResponse = await fetch('/api/file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    path: newPath,
                    content: content
                })
            });
            
            if (!createResponse.ok) throw new Error('Failed to move file');
            
            // Delete the old file
            const deleteResponse = await fetch(`/api/file?path=${encodeURIComponent(sourcePath)}`, {
                method: 'DELETE'
            });
            
            if (!deleteResponse.ok) throw new Error('Failed to delete original file');
            
            // Update UI if the current file was moved
            if (currentFile === sourcePath) {
                currentFile = newPath;
                document.title = `☘️Kiro - ${fileName}`;
            }
            
            // Refresh the file structure
            await loadFileStructure();
            showToast('파일이 이동되었습니다');
        } catch (error) {
            console.error('Error moving file:', error);
            showToast(`이동 실패: ${error.message}`, true);
        }
    }
    
    // Download the current .kiro file
    function downloadKiroFile() {
        if (!editor || !editor.value) {
            alert('편집 중인 내용이 없습니다.');
            return;
        }
        
        // Create filename
        const filename = currentFile ? 
            currentFile.split('/').pop() : 
            'document.kiro';
        
        // Create a blob with the content
        const blob = new Blob([editor.value], { type: 'text/plain' });
        
        // Create a temporary download link
        const downloadLink = document.createElement('a');
        downloadLink.href = URL.createObjectURL(blob);
        downloadLink.download = filename;
        
        // Append to body, click, and remove
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
        
        // Clean up the URL object
        URL.revokeObjectURL(downloadLink.href);
        
        showToast('파일이 다운로드되었습니다');
    }
    
    // Print document function
    function printDocument() {
        if (!editor || !editor.value) {
            alert('인쇄할 내용이 없습니다.');
            return;
        }
        
        // Make sure preview is updated
        renderKiro(false).then(() => {
            const printWindow = window.open('', '_blank');
            const title = currentFile ? currentFile.split('/').pop().replace('.kiro', '') : 'Kiro 문서';
            
            // Create print content
            printWindow.document.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>${title}</title>
                    <script src="https://cdn.tailwindcss.com"></script>
                    <style>
                        @font-face {
                            font-family: 'MonoplexKR-Regular';
                            src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_Monoplex-kr@1.0/MonoplexKR-Regular.woff2') format('woff2');
                            font-display: swap;
                        }
                        body {
                            font-family: 'MonoplexKR-Regular', 'Noto Sans KR', sans-serif;
                            padding: 20px;
                        }
                        @media print {
                            body {
                                padding: 20mm;
                            }
                            .prose img {
                                max-width: 100%;
                                height: auto;
                            }
                        }
                    </style>
                </head>
                <body class="bg-white">
                    <div class="max-w-none prose prose-lg">
                        ${lastRenderedHTML || '<p>인쇄할 내용이 없습니다.</p>'}
                    </div>
                </body>
                </html>
            `);
            
            // Print after content is loaded
            printWindow.document.close();
            printWindow.addEventListener('load', () => {
                setTimeout(() => {
                    printWindow.print();
                    printWindow.close();
                }, 250);
            });
        });
        
        showToast('인쇄 창이 열렸습니다');
    }
    
    // Basic editor functionality
    if (editor) {
        editor.addEventListener('input', () => {
            // Render preview more frequently (500ms instead of 2000ms)
            clearTimeout(window.renderTimer);
            window.renderTimer = setTimeout(() => {
                renderKiro(false);
                // Schedule auto-save after rendering
                scheduleAutoSave();
            }, 500);
        });
        
        editor.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === 'Tab') {
                clearTimeout(window.renderTimer);
                window.renderTimer = setTimeout(() => {
                    renderKiro(false);
                    // Schedule auto-save after rendering
                    scheduleAutoSave();
                }, 200);  // Even faster for Enter/Tab
            }
        });
    }
    
    // Schedule auto-save function
    function scheduleAutoSave() {
        if (!currentFile) return;
        
        // Clear any existing auto-save timer
        clearTimeout(autoSaveTimer);
        
        // Set a new auto-save timer (1 second after rendering)
        autoSaveTimer = setTimeout(() => {
            if (editor.value !== lastSavedContent) {
                saveFile();
            }
        }, 1000);
    }
    
    // Simple render function
    function renderKiro(forViewMode = false) {
        if (!editor || !editor.value) {
            console.log('No content to render');
            return Promise.resolve();  // Return a resolved promise for chaining
        }
    
        console.log('Rendering Kiro content:', editor.value.length, 'characters');
    
        return fetch('/api/render', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: editor.value
            })
        })
        .then(response => {
            console.log('Render API response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Render data received:', data);
    
            if (data.error) {
                console.error('Render error:', data.error);
                return;
            }

            lastRenderedHTML = data.html;
    
            // 편집모드일 때 스타일 감싼 HTML로 미리보기
            if (!forViewMode) {
                const iframe = document.getElementById('editPreviewIframe');
                if (iframe) {
                    iframe.srcdoc = data.html;
                    console.log('Updated edit preview iframe with full rendered HTML');
                }
            }            
    
            // 보기모드일 때 iframe에 전체 HTML 삽입
            if (forViewMode) {
                const iframe = document.getElementById('viewIframe');
                if (iframe) {
                    iframe.srcdoc = data.html;
                    console.log('Updated iframe with full rendered HTML');
                }
            }
        })
        .catch(error => {
            console.error('Error rendering Kiro:', error);
        });
    }

    function downloadHtml() {
        if (!lastRenderedHTML) {
            alert("먼저 렌더링을 수행하세요.");
            return;
        }
    
        const blob = new Blob([lastRenderedHTML], { type: "text/html" });
        const url = URL.createObjectURL(blob);
    
        const a = document.createElement("a");
        a.href = url;
        a.download = (currentFile ? currentFile.replace('.kiro', '') : "document") + ".html";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    
        showToast("HTML 파일 다운로드 완료!");
    }    
    
    // Save file function
    function saveFile() {
        if (!currentFile) {
            console.log('No file is currently open');
            return Promise.resolve();
        }
        
        console.log('Saving file:', currentFile);
        
        return fetch('/api/file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: currentFile,
                content: editor.value
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to save file');
            }
            lastSavedContent = editor.value;
            console.log('File saved successfully');
            // Show a brief save indicator
            showSaveIndicator();
            return response.json();
        })
        .catch(error => {
            console.error('Error saving file:', error);
        });
    }
    
    // Show a brief save indicator
    function showSaveIndicator() {
        const saveIndicator = document.createElement('div');
        saveIndicator.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-3 py-1 rounded shadow-lg z-50';
        saveIndicator.textContent = '저장됨';
        document.body.appendChild(saveIndicator);
        
        setTimeout(() => {
            saveIndicator.style.opacity = '0';
            saveIndicator.style.transition = 'opacity 0.5s';
            setTimeout(() => {
                saveIndicator.remove();
            }, 500);
        }, 1000);
    }
    
    // Show toast notification
    function showToast(message, isError = false) {
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 ${isError ? 'bg-red-500' : 'bg-blue-500'} text-white px-3 py-2 rounded shadow-lg z-50`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.5s';
            setTimeout(() => {
                toast.remove();
            }, 500);
        }, 2000);
    }
    
    // Load file structure
    async function loadFileStructure() {
        try {
            const response = await fetch('/api/files');
            if (!response.ok) throw new Error('Failed to load file structure');
            
            const data = await response.json();
            console.log('File structure loaded:', data);
            
            const fileSystem = document.getElementById('fileSystem');
            if (fileSystem) {
                fileSystem.innerHTML = ''; // Clear before rendering
                renderFileTree(data, fileSystem);
            }
            
            return data;
        } catch (error) {
            console.error('Error loading file structure:', error);
            showToast('파일 구조 로드 실패', true);
        }
    }
    
    // Render file tree
    function renderFileTree(items, container) {
        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'py-1';
            div.dataset.type = item.type;
            div.dataset.path = item.id;
            
            const icon = item.type === 'folder' ? '📁' : '📄';
            div.innerHTML = `<span class="cursor-pointer hover:bg-gray-100 px-1 rounded">${icon} ${item.name}</span>`;
            
            const span = div.querySelector('span');
            
            // Make items draggable for file moves
            if (item.type === 'file') {
                span.draggable = true;
                span.addEventListener('dragstart', (e) => {
                    draggedItem = item.id;
                    e.dataTransfer.setData('text/plain', item.id);
                    e.dataTransfer.effectAllowed = 'move';
                });
                
                span.addEventListener('click', () => {
                    // If we have unsaved changes, save the current file first
                    if (currentFile && editor.value !== lastSavedContent) {
                        saveFile().then(() => loadFile(item.id));
                    } else {
                        loadFile(item.id);
                    }
                });
                
                // Add context menu for files (right-click)
                span.addEventListener('contextmenu', (e) => {
                    e.preventDefault();
                    showFileContextMenu(e, item.id);
                });
            } else if (item.type === 'folder') {
                // Add drop target for folders
                span.addEventListener('dragover', (e) => {
                    // Only allow dropping files, not folders
                    if (draggedItem && !draggedItem.endsWith('/')) {
                        e.preventDefault();
                        span.classList.add('bg-blue-100');
                    }
                });
                
                span.addEventListener('dragleave', () => {
                    span.classList.remove('bg-blue-100');
                });
                
                span.addEventListener('drop', async (e) => {
                    e.preventDefault();
                    span.classList.remove('bg-blue-100');
                    
                    const sourcePath = draggedItem;
                    const targetFolder = item.id;
                    
                    // Don't move a file to its own parent folder
                    const sourcePathParts = sourcePath.split('/');
                    sourcePathParts.pop(); // Remove filename
                    const sourceFolder = sourcePathParts.join('/');
                    
                    if (sourceFolder === targetFolder) {
                        showToast('파일이 이미 해당 폴더에 있습니다', true);
                        return;
                    }
                    
                    await moveFile(sourcePath, targetFolder);
                    draggedItem = null;
                });
                
                // Add context menu for folders (right-click)
                span.addEventListener('contextmenu', (e) => {
                    e.preventDefault();
                    showFolderContextMenu(e, item.id);
                });
            }
            
            container.appendChild(div);
            
            if (item.type === 'folder' && item.children && item.children.length) {
                const childContainer = document.createElement('div');
                childContainer.className = 'pl-4';
                div.appendChild(childContainer);
                renderFileTree(item.children, childContainer);
            }
        });
        
        // Add root-level drop target for moving files to root
        if (container.id === 'fileSystem') {
            container.addEventListener('dragover', (e) => {
                if (draggedItem && !draggedItem.endsWith('/') && !e.target.closest('[data-type="folder"]')) {
                    e.preventDefault();
                    container.classList.add('bg-blue-50');
                }
            });
            
            container.addEventListener('dragleave', () => {
                container.classList.remove('bg-blue-50');
            });
            
            container.addEventListener('drop', async (e) => {
                if (!e.target.closest('[data-type="folder"]')) {
                    e.preventDefault();
                    container.classList.remove('bg-blue-50');
                    
                    const sourcePath = draggedItem;
                    if (sourcePath) {
                        // Don't move a file if it's already at root
                        if (!sourcePath.includes('/')) {
                            showToast('파일이 이미 루트에 있습니다', true);
                            return;
                        }
                        
                        await moveFile(sourcePath, '');
                        draggedItem = null;
                    }
                }
            });
        }
    }
    
    // Show folder context menu
    function showFolderContextMenu(event, folderId) {
        // Remove existing context menus
        const existing = document.querySelector('.context-menu');
        if (existing) existing.remove();
        
        // Create context menu
        const menu = document.createElement('div');
        menu.className = 'context-menu absolute bg-white shadow-md rounded z-50';
        menu.style.left = `${event.pageX}px`;
        menu.style.top = `${event.pageY}px`;
        menu.innerHTML = `
            <div class="px-3 py-2 hover:bg-gray-100 cursor-pointer" id="newFileMenu">새 파일</div>
            <div class="px-3 py-2 hover:bg-gray-100 cursor-pointer" id="newFolderMenu">새 폴더</div>
            <div class="px-3 py-2 hover:bg-gray-100 cursor-pointer" id="renameMenu">이름 변경</div>
            <div class="px-3 py-2 hover:bg-gray-100 cursor-pointer text-red-600" id="deleteMenu">삭제</div>
        `;
        
        document.body.appendChild(menu);
        
        // Event listeners
        menu.querySelector('#newFileMenu').addEventListener('click', () => {
            document.body.removeChild(menu);
            showModal('file', folderId);
        });
        
        menu.querySelector('#newFolderMenu').addEventListener('click', () => {
            document.body.removeChild(menu);
            showModal('folder', folderId);
        });
        
        menu.querySelector('#renameMenu').addEventListener('click', () => {
            document.body.removeChild(menu);
            showRenameModal(folderId, 'folder');
        });
        
        menu.querySelector('#deleteMenu').addEventListener('click', () => {
            document.body.removeChild(menu);
            confirmDelete(folderId, 'folder');
        });
        
        // Close when clicking elsewhere
        document.addEventListener('click', function closeMenu() {
            if (document.querySelector('.context-menu')) {
                document.body.removeChild(menu);
                document.removeEventListener('click', closeMenu);
            }
        });
    }
    
    // Show file context menu
    function showFileContextMenu(event, fileId) {
        // Remove existing context menus
        const existing = document.querySelector('.context-menu');
        if (existing) existing.remove();
        
        // Create context menu
        const menu = document.createElement('div');
        menu.className = 'context-menu absolute bg-white shadow-md rounded z-50';
        menu.style.left = `${event.pageX}px`;
        menu.style.top = `${event.pageY}px`;
        menu.innerHTML = `
            <div class="px-3 py-2 hover:bg-gray-100 cursor-pointer" id="renameMenu">이름 변경</div>
            <div class="px-3 py-2 hover:bg-gray-100 cursor-pointer text-red-600" id="deleteMenu">삭제</div>
        `;
        
        document.body.appendChild(menu);
        
        // Event listeners
        menu.querySelector('#renameMenu').addEventListener('click', () => {
            document.body.removeChild(menu);
            showRenameModal(fileId, 'file');
        });
        
        menu.querySelector('#deleteMenu').addEventListener('click', () => {
            document.body.removeChild(menu);
            confirmDelete(fileId, 'file');
        });
        
        // Close when clicking elsewhere
        document.addEventListener('click', function closeMenu() {
            if (document.querySelector('.context-menu')) {
                document.body.removeChild(menu);
                document.removeEventListener('click', closeMenu);
            }
        });
    }
    
    // Show rename modal
    function showRenameModal(itemPath, itemType) {
        const itemName = itemPath.split('/').pop();
        
        // Get parent path
        const pathParts = itemPath.split('/');
        pathParts.pop();
        const parentPath = pathParts.join('/');
        
        // Create modal
        const renameModal = document.createElement('div');
        renameModal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        renameModal.id = 'renameModal';
        
        renameModal.innerHTML = `
            <div class="bg-white p-6 rounded-lg shadow-lg w-80">
                <h2 class="text-lg font-bold mb-4">이름 변경</h2>
                <input type="text" id="newNameInput" class="border rounded w-full px-2 py-1 mb-4" value="${itemName}">
                <div class="flex justify-end">
                    <button id="cancelRenameBtn" class="bg-gray-300 text-gray-800 px-4 py-1 rounded mr-2">취소</button>
                    <button id="confirmRenameBtn" class="bg-blue-500 text-white px-4 py-1 rounded">확인</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(renameModal);
        
        // Focus input and select the name (without extension for files)
        const newNameInput = document.getElementById('newNameInput');
        newNameInput.focus();
        
        if (itemType === 'file') {
            const dotIndex = itemName.lastIndexOf('.');
            if (dotIndex > 0) {
                newNameInput.setSelectionRange(0, dotIndex);
            } else {
                newNameInput.select();
            }
        } else {
            newNameInput.select();
        }
        
        // Add event listeners
        document.getElementById('cancelRenameBtn').addEventListener('click', () => {
            document.body.removeChild(renameModal);
        });
        
        document.getElementById('confirmRenameBtn').addEventListener('click', () => {
            const newName = newNameInput.value.trim();
            if (!newName) {
                alert('이름을 입력해주세요.');
                return;
            }
            
            // For files, ensure it has the .kiro extension
            let finalName = newName;
            if (itemType === 'file' && !finalName.endsWith('.kiro')) {
                // If original had extension, keep it
                const dotIndex = itemName.lastIndexOf('.');
                if (dotIndex > 0) {
                    finalName = newName + itemName.substring(dotIndex);
                } else {
                    finalName = newName + '.kiro';
                }
            }
            
            // Process the rename
            const newPath = parentPath ? `${parentPath}/${finalName}` : finalName;
            renameItem(itemPath, newPath, itemType);
            document.body.removeChild(renameModal);
        });
    }
    
    // Rename item (file or folder)
    async function renameItem(oldPath, newPath, itemType) {
        try {
            // First check if a file/folder with the same name already exists
            const fileStructure = await loadFileStructure();
            
            // Same duplicate check function as in handleModalConfirm
            const checkDuplicate = (items, path) => {
                if (!items) return false;
                
                // Direct check for root level items
                if (items.some(item => item.id === path)) {
                    return true;
                }
                
                // Check in folders for nested paths
                if (path.includes('/')) {
                    const pathParts = path.split('/');
                    const parentFolderName = pathParts[0];
                    const parentFolder = items.find(item => 
                        item.type === 'folder' && item.name === parentFolderName
                    );
                    
                    if (parentFolder && parentFolder.children) {
                        const remainingPath = pathParts.slice(1).join('/');
                        return checkDuplicate(parentFolder.children, remainingPath);
                    }
                }
                
                return false;
            };
            
            // Don't check if old path and new path are the same (just case change)
            if (oldPath.toLowerCase() !== newPath.toLowerCase() && checkDuplicate(fileStructure, newPath)) {
                showToast(`이미 같은 이름의 ${itemType === 'file' ? '파일' : '폴더'}이 존재합니다`, true);
                return;
            }
            
            if (itemType === 'file') {
                // For files, we need to get the content, create new file, delete old
                const response = await fetch(`/api/file?path=${encodeURIComponent(oldPath)}`);
                if (!response.ok) throw new Error('Failed to load file');
                
                const data = await response.json();
                const content = data.content;
                
                // Create file at new path
                const createResponse = await fetch('/api/file', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        path: newPath,
                        content: content
                    })
                });
                
                if (!createResponse.ok) throw new Error('Failed to create file at new location');
                
                // Delete old file
                const deleteResponse = await fetch(`/api/file?path=${encodeURIComponent(oldPath)}`, {
                    method: 'DELETE'
                });
                
                if (!deleteResponse.ok) throw new Error('Failed to delete original file');
                
                // Update currentFile reference if this was the open file
                if (currentFile === oldPath) {
                    currentFile = newPath;
                    document.title = `☘️Kiro - ${newPath.split('/').pop()}`;
                }
                
                showToast('파일 이름이 변경되었습니다');
            } else {
                // For folders, use the folder rename API
                const response = await fetch('/api/folder/rename', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        old_path: oldPath,
                        new_path: newPath
                    })
                });
                
                if (!response.ok) throw new Error('Failed to rename folder');
                
                // Update currentFile reference if the open file was in this folder
                if (currentFile && currentFile.startsWith(oldPath + '/')) {
                    currentFile = currentFile.replace(oldPath, newPath);
                    document.title = `☘️Kiro - ${currentFile.split('/').pop()}`;
                }
                
                showToast('폴더 이름이 변경되었습니다');
            }
            
            // Refresh file tree
            await loadFileStructure();
        } catch (error) {
            console.error('Error renaming item:', error);
            showToast(`이름 변경 실패: ${error.message}`, true);
        }
    }
    
    // Confirm delete
    function confirmDelete(itemPath, itemType) {
        const itemName = itemPath.split('/').pop();
        
        if (confirm(`${itemName}을(를) 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`)) {
            deleteItem(itemPath, itemType);
        }
    }
    
    // Delete item (file or folder)
    async function deleteItem(itemPath, itemType) {
        try {
            if (itemType === 'file') {
                const response = await fetch(`/api/file?path=${encodeURIComponent(itemPath)}`, {
                    method: 'DELETE'
                });
                
                if (!response.ok) throw new Error('Failed to delete file');
                
                // If this was the current file, clear the editor
                if (currentFile === itemPath) {
                    editor.value = '';
                    currentFile = null;
                    lastSavedContent = '';
                    document.title = '☘️Kiro';
                }
                
                showToast('파일이 삭제되었습니다');
            } else {
                const response = await fetch(`/api/folder?path=${encodeURIComponent(itemPath)}`, {
                    method: 'DELETE'
                });
                
                if (!response.ok) throw new Error('Failed to delete folder');
                
                // If current file was in this folder, clear the editor
                if (currentFile && (currentFile.startsWith(itemPath + '/') || currentFile === itemPath)) {
                    editor.value = '';
                    currentFile = null;
                    lastSavedContent = '';
                    document.title = '☘️Kiro';
                }
                
                showToast('폴더가 삭제되었습니다');
            }
            
            // Refresh file tree
            await loadFileStructure();
        } catch (error) {
            console.error('Error deleting item:', error);
            showToast(`삭제 실패: ${error.message}`, true);
        }
    }
    
    // Load file content
    function loadFile(path) {
        console.log('Loading file:', path);
        
        fetch(`/api/file?path=${encodeURIComponent(path)}`)
            .then(response => response.json())
            .then(data => {
                console.log('File content loaded:', data);
                
                if (editor) {
                    editor.value = data.content;
                    currentFile = path;
                    lastSavedContent = data.content;
                    document.title = `☘️Kiro - ${path.split('/').pop()}`;
                    console.log('Content set to editor, rendering preview');
                    
                    // Render to the appropriate view based on current mode
                    if (currentMode === 'edit') {
                        renderKiro(false);
                    } else {
                        renderKiro(true);
                    }
                    
                    // If in view mode, make sure we stay in view mode
                    if (currentMode === 'view') {
                        editModeView.classList.add('hidden');
                        viewModeView.classList.remove('hidden');
                    }
                }
            })
            .catch(error => {
                console.error('Error loading file:', error);
            });
    }
    
    // Initialize
    loadFileStructure();
}); 