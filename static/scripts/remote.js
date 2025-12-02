document.addEventListener('DOMContentLoaded', () => {
    Array.from(document.getElementsByTagName('button')).forEach((button) => {
        button.addEventListener('click', async () => {
            const label = button.textContent;
            button.textContent = '...';
            button.disabled = true;
            fetch(
                `remote/${button.id}`,
                {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json;charset=UTF-8'}
                }
            )
            .then(response => {
                if (!response.ok) {
                    alert(`Error: response code was ${response.status}`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Unexpected error');
            })
            .finally(() => {
                button.textContent = label;
                button.disabled = false;
            });
        });
    });
});
