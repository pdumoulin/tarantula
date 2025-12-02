document.addEventListener('DOMContentLoaded', () => {
    Array.from(document.getElementsByTagName('button')).forEach((button) => {
        button.addEventListener('click', async () => {
            const action = !button.classList.contains('statusTrue');
            const label = button.textContent;
            button.textContent = '...';
            button.disabled = true;
            fetch(
                `plugs/${button.id}`,
                {
                    method: 'PATCH',
                    headers: {'Content-Type': 'application/json;charset=UTF-8'},
                    body: JSON.stringify({'status': action})
                }
            )
            .then(response => {
                if (!response.ok) {
                    alert(`Error: response code was ${response.status}`);
                }
                else {
                    button.classList.replace(
                        `status${String(!action).charAt(0).toUpperCase() + String(!action).slice(1)}`,
                        `status${String(action).charAt(0).toUpperCase() + String(action).slice(1)}`
                    );
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
