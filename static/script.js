document.addEventListener('DOMContentLoaded', () => {
    const uploadInput = document.getElementById('image-upload');
    const uploadBox = document.querySelector('.upload-box');
    const uploadText = document.getElementById('upload-text');
    const previewSection = document.getElementById('preview-section');
    const imagePreview = document.getElementById('image-preview');
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');
    const loading = document.getElementById('loading');

    uploadInput.addEventListener('change', handleFileSelect);

    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('dragging');
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('dragging');
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('dragging');
        const files = e.dataTransfer.files;
        if (files.length) {
            uploadInput.files = files;
            handleFileSelect({ target: uploadInput });
        }
    });

    async function handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) {
            showError('No file selected.');
            return;
        }

        if (!file.type.startsWith('image/')) {
            showError('Please upload an image file.');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            showError('Image size must be less than 5MB.');
            return;
        }

        const reader = new FileReader();
        reader.onload = () => {
            imagePreview.src = reader.result;
            previewSection.classList.remove('hidden');
            resultsSection.classList.add('hidden');
            uploadText.textContent = 'Upload another image';
        };
        reader.readAsDataURL(file);

        const formData = new FormData();
        formData.append('file', file);

        loading.classList.remove('hidden');
        try {
            console.log('Sending request to /analyze-image at', new Date().toISOString());
            const response = await fetch('http://localhost:8000/analyze-image', {
                method: 'POST',
                body: formData
            });

            console.log('Response received:', {
                status: response.status,
                ok: response.ok,
                headers: [...response.headers.entries()]
            });

            if (!response.ok) {
                let errorDetail = 'Unknown server error';
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.detail || `Server error: ${response.status}`;
                } catch (jsonError) {
                    console.error('Error parsing server error:', jsonError);
                }
                showError(errorDetail);
                loading.classList.add('hidden');
                return;
            }

            const result = await response.json();
            console.log('Backend response:', result);

            if (!result || typeof result !== 'object' ||
                !Array.isArray(result.problems) ||
                !Array.isArray(result.problem_types) ||
                !Array.isArray(result.suggestions)) {
                console.warn('Invalid response structure:', result);
                showError('Invalid response format from server.');
                loading.classList.add('hidden');
                return;
            }

            loading.classList.add('hidden');

            if (result.problems.length > 0) {
                displayResults(result);
            } else {
                resultsContent.innerHTML = '<p>No problems detected in the image.</p>';
                resultsSection.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Fetch error details:', {
                message: error.message,
                name: error.name,
                stack: error.stack,
                timestamp: new Date().toISOString()
            });
            loading.classList.add('hidden');
            showError(`Connection failed: ${error.message}. Please check if the server is running.`);
        }
    }

    function displayResults(data) {
        resultsContent.innerHTML = '';
        data.problems.forEach((problem, index) => {
            const card = document.createElement('div');
            card.className = 'result-card';
            card.innerHTML = `
                <h3>Problem ${index + 1}</h3>
                <p><strong>Issue:</strong> ${problem}</p>
                <p><strong>Type:</strong> ${data.problem_types[index]}</p>
                <p><strong>Suggestion:</strong> ${data.suggestions[index]}</p>
            `;
            resultsContent.appendChild(card);
        });
        resultsSection.classList.remove('hidden');
    }

    function showError(message) {
        resultsContent.innerHTML = `<p class="error">${message}</p>`;
        resultsSection.classList.remove('hidden');
    }
});