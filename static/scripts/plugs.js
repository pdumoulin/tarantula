document.addEventListener('DOMContentLoaded', () => {
    const app = document.getElementById('app');

    // Wraps target (and everything nested inside it) in a Proxy whose `set`
    // trap calls onChange. Every nested object/array gets its own Proxy that
    // closes over the same onChange, so a mutation at any depth re-renders
    // without needing to bubble the change up manually.
    function reactive(target, onChange) {
        if (target === null || typeof target !== 'object') {
            return target;
        }
        for (const key of Object.keys(target)) {
            target[key] = reactive(target[key], onChange);
        }
        return new Proxy(target, {
            set(obj, prop, value) {
                obj[prop] = reactive(value, onChange);
                onChange();
                return true;
            }
        });
    }

    const state = reactive({ loading: true, error: null, plugs: [] }, render);

    // Single render function used for the first paint and every update after,
    // so the DOM is always just a projection of the current state.
    function render() {
        if (state.loading) {
            app.innerHTML = '<div class="spinner"></div>';
            return;
        }
        if (state.error) {
            app.innerHTML = `<p class="error">Error: ${escapeHtml(state.error)}</p>`;
            return;
        }
        app.innerHTML = state.plugs.map(renderButton).join('');
    }

    function renderButton(plug) {
        const statusClass = plug.status === null
            ? 'statusError'
            : `status${plug.status ? 'True' : 'False'}`;
        const label = plug.pending ? '...' : escapeHtml(plug.name);
        const disabled = plug.pending ? 'disabled' : '';
        return `<button data-id="${plug.id}" class="plug ${statusClass}" ${disabled}>${label}</button>`;
    }

    function escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = String(value);
        return div.innerHTML;
    }

    // One listener on the container handles clicks for every button,
    // including ones that don't exist yet when render() rebuilds the markup.
    app.addEventListener('click', (event) => {
        const button = event.target.closest('button[data-id]');
        if (!button || button.disabled) {
            return;
        }
        togglePlug(Number(button.dataset.id));
    });

    async function togglePlug(id) {
        const plug = state.plugs.find((p) => p.id === id);
        if (!plug || plug.pending) {
            return;
        }
        const nextStatus = !plug.status;
        plug.pending = true;
        try {
            const response = await fetch(`/plugs/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json;charset=UTF-8' },
                body: JSON.stringify({ status: nextStatus })
            });
            if (!response.ok) {
                throw new Error(`response code was ${response.status}`);
            }
            plug.status = nextStatus;
        } catch (error) {
            console.error('Error:', error);
            alert('Unexpected error');
        } finally {
            plug.pending = false;
        }
    }

    async function loadPlugs() {
        try {
            const response = await fetch('/plugs', {
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) {
                throw new Error(`response code was ${response.status}`);
            }
            const data = await response.json();
            state.plugs = data.map((plug) => ({ ...plug, pending: false }));
        } catch (error) {
            console.error('Error:', error);
            state.error = error.message;
        } finally {
            state.loading = false;
        }
    }

    loadPlugs();
});
