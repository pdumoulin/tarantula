document.addEventListener('DOMContentLoaded', () => {
    const app = document.getElementById('app');
    const PLAYING_STATUSES = ['PLAYING', 'BUFFERING'];
    const ACTIVE_STATUSES = ['PLAYING', 'BUFFERING', 'PAUSED'];

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

    const state = reactive({ loading: true, error: null, cast: null }, render);

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
        app.innerHTML = renderCast(state.cast);
    }

    function renderCast(cast) {
        if (!ACTIVE_STATUSES.includes(cast.playback_status)) {
            return '<p class="empty">Nothing Playing</p>';
        }
        const isPlaying = PLAYING_STATUSES.includes(cast.playback_status);
        const toggleLabel = isPlaying ? '⏸️' : '▶️';
        const duration = cast.duration ?? 0;
        const currentTime = cast.current_time ?? 0;
        const seekDisabled = cast.duration ? '' : 'disabled';
        const title = cast.title ? `<p class="title">${escapeHtml(cast.title)}</p>` : '';
        return `
            ${title}
            <div class="seek">
                <span class="time">${formatTime(currentTime)}</span>
                <input type="range" min="0" max="${duration}" step="1" value="${currentTime}" ${seekDisabled}>
                <span class="time">${formatTime(duration)}</span>
            </div>
            <div class="controls">
                <button data-action="toggle" class="btn">${toggleLabel}</button>
                <button data-action="stop" class="btn">⏹️</button>
                <button data-action="skip-back" class="btn btn-skip" ${seekDisabled}>⏪</button>
                <button data-action="skip-forward" class="btn btn-skip" ${seekDisabled}>⏩</button>
            </div>
        `;
    }

    function formatTime(seconds) {
        const total = Math.max(0, Math.round(seconds));
        const minutes = Math.floor(total / 60);
        const remainder = total % 60;
        return `${minutes}:${String(remainder).padStart(2, '0')}`;
    }

    function escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = String(value);
        return div.innerHTML;
    }

    // One listener on the container handles clicks for every button,
    // including ones that don't exist yet when render() rebuilds the markup.
    app.addEventListener('click', (event) => {
        const button = event.target.closest('button[data-action]');
        if (!button || button.disabled) {
            return;
        }
        switch (button.dataset.action) {
            case 'toggle':
                togglePlayback();
                break;
            case 'stop':
                runAction('/chromecast/stop');
                break;
            case 'skip-back':
                seekBy(-10);
                break;
            case 'skip-forward':
                seekBy(10);
                break;
        }
    });

    app.addEventListener('change', (event) => {
        const input = event.target.closest('input[type="range"]');
        if (!input || input.disabled) {
            return;
        }
        seekTo(Number(input.value));
    });

    function togglePlayback() {
        const isPlaying = PLAYING_STATUSES.includes(state.cast.playback_status);
        runAction(isPlaying ? '/chromecast/pause' : '/chromecast/play');
    }

    function seekBy(deltaSeconds) {
        runAction('/chromecast/seek_by', { seconds: deltaSeconds });
    }

    function seekTo(time) {
        const duration = state.cast.duration ?? 0;
        const clamped = Math.min(Math.max(time, 0), duration);
        runAction('/chromecast/seek', { time: clamped });
    }

    async function runAction(url, body) {
        if (state.loading) {
            return;
        }
        state.loading = true;
        try {
            const options = { method: 'POST' };
            if (body) {
                options.headers = { 'Content-Type': 'application/json;charset=UTF-8' };
                options.body = JSON.stringify(body);
            }
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`response code was ${response.status}`);
            }
            state.cast = await response.json();
        } catch (error) {
            console.error('Error:', error);
            alert('Unexpected error');
        } finally {
            state.loading = false;
        }
    }

    async function loadState() {
        state.loading = true;
        try {
            const response = await fetch('/chromecast', {
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) {
                throw new Error(`response code was ${response.status}`);
            }
            state.cast = await response.json();
        } catch (error) {
            console.error('Error:', error);
            state.error = error.message;
        } finally {
            state.loading = false;
        }
    }

    loadState();
});
