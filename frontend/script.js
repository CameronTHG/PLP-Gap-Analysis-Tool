document.addEventListener('DOMContentLoaded', () => {
    const apiKeyInput = document.getElementById('api-key');
    const existingPagesFileInput = document.getElementById('existing-pages-file');
    const topicAttackFileInput = document.getElementById('topic-attack-file');
    const findOpportunitiesBtn = document.getElementById('find-opportunities-btn');
    const downloadCsvBtn = document.getElementById('download-csv-btn');
    const loaderContainer = document.querySelector('.loader-container');

    let existingPagesFile = null;
    let topicAttackFile = null;
    let apiKey = '';

    function updateButtonState() {
        if (existingPagesFile && topicAttackFile && apiKey) {
            findOpportunitiesBtn.disabled = false;
        } else {
            findOpportunitiesBtn.disabled = true;
        }
    }

    apiKeyInput.addEventListener('input', (event) => {
        apiKey = event.target.value;
        updateButtonState();
    });

    existingPagesFileInput.addEventListener('change', (event) => {
        existingPagesFile = event.target.files[0];
        updateButtonState();
    });

    topicAttackFileInput.addEventListener('change', (event) => {
        topicAttackFile = event.target.files[0];
        updateButtonState();
    });

    findOpportunitiesBtn.addEventListener('click', async () => {
        findOpportunitiesBtn.disabled = true;
        loaderContainer.style.display = 'block';
        downloadCsvBtn.style.display = 'none';

        const formData = new FormData();
        formData.append('existing_pages', existingPagesFile);
        formData.append('topic_attack', topicAttackFile);
        formData.append('api_key', apiKey);

        try {
            const response = await fetch('http://127.0.0.1:5001/api/find_opportunities', {
                method: 'POST',
                body: formData,
            });


            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                downloadCsvBtn.onclick = () => {
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = 'seo_opportunities.csv';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                };
                downloadCsvBtn.style.display = 'block';
            } else {
                const error = await response.json();
                alert(`Error: ${error.error}`);
            }
        } catch (error) {
            alert('An error occurred while processing the files.');
            console.error('Error:', error);
        } finally {
            loaderContainer.style.display = 'none';
            findOpportunitiesBtn.disabled = false;
        }
    });

    const readMoreLink = document.getElementById('read-more-link');
    const detailedLogic = document.getElementById('detailed-logic');

    readMoreLink.addEventListener('click', (event) => {
        event.preventDefault();
        if (detailedLogic.style.display === 'none') {
            detailedLogic.style.display = 'block';
            readMoreLink.textContent = 'Read less';
        } else {
            detailedLogic.style.display = 'none';
            readMoreLink.textContent = 'Read more';
        }
    });
});