/* Unit-circle perimeters divided by diameter: L_n = n sin(π/n), U_n = n tan(π/n). */
(() => {
    'use strict';
    const byId = id => document.getElementById(id);
    const slider = byId('sides-slider');
    const number = byId('sides-number');
    const play = byId('play-demo');
    const presets = [...document.querySelectorAll('[data-sides]')];
    const chart = { left: 48, right: 468, top: 26, bottom: 232 };
    let n = 6;
    let animation = null;
    let startTime = null;

    const bounds = sides => ({ lower: sides * Math.sin(Math.PI / sides), upper: sides * Math.tan(Math.PI / sides) });
    const x = sides => chart.left + Math.log(sides / 3) / Math.log(1000 / 3) * (chart.right - chart.left);

    function polygon(sides, radius, offset) {
        return Array.from({ length: sides }, (_, i) => {
            const angle = offset + 2 * Math.PI * i / sides;
            return `${(220 + radius * Math.cos(angle)).toFixed(4)},${(215 + radius * Math.sin(angle)).toFixed(4)}`;
        }).join(' ');
    }

    function drawChart() {
        // Keep a fixed vertical scale so tightening bounds never appear to widen.
        const min = 2.5;
        const max = 5.3;
        const y = value => chart.bottom - (value - min) / (max - min) * (chart.bottom - chart.top);
        const ticks = [2.5, 3, 4, 5];
        byId('chart-grid').innerHTML = ticks.map(value => `<line class="grid" x1="48" x2="468" y1="${y(value)}" y2="${y(value)}"/><text x="39" y="${y(value) + 4}" text-anchor="end">${value.toFixed(1)}</text>`).join('');
        byId('pi-line').setAttribute('y1', y(Math.PI));
        byId('pi-line').setAttribute('y2', y(Math.PI));
        byId('pi-chart-label').setAttribute('y', y(Math.PI) - 7);
        const samples = Array.from({ length: 361 }, (_, i) => 3 * Math.pow(1000 / 3, i / 360));
        function path(values, key) {
            return values.map((sides, i) => `${i ? 'L' : 'M'}${x(sides).toFixed(3)},${y(bounds(sides)[key]).toFixed(3)}`).join(' ');
        }
        const visible = samples.filter(sides => sides < n).concat(n);
        for (const key of ['lower', 'upper']) {
            byId(`${key}-full`).setAttribute('d', path(samples, key));
            byId(`${key}-progress`).setAttribute('d', path(visible, key));
            byId(`${key}-dot`).setAttribute('cx', x(n));
            byId(`${key}-dot`).setAttribute('cy', y(bounds(n)[key]));
        }
        byId('chart-cursor').setAttribute('x1', x(n));
        byId('chart-cursor').setAttribute('x2', x(n));
        byId('chart-n-label').setAttribute('x', Math.min(chart.right - 22, Math.max(chart.left + 22, x(n))));
        byId('chart-n-label').textContent = `n = ${n}`;
        byId('chart-description').textContent = `At n = ${n}, the lower bound is ${bounds(n).lower.toFixed(9)} and the upper bound is ${bounds(n).upper.toFixed(9)}. They enclose π.`;
    }

    function render(value) {
        n = Math.max(3, Math.min(1000, Math.round(value)));
        slider.value = n;
        slider.setAttribute('aria-valuetext', `${n} sides`);
        number.value = n;
        byId('geometry-sides').textContent = `n = ${n}`;
        // Fixed radius and viewport keep even the circumscribed triangle fully visible.
        byId('inner-polygon').setAttribute('points', polygon(n, 94, -Math.PI / 2));
        byId('outer-polygon').setAttribute('points', polygon(n, 94 / Math.cos(Math.PI / n), -Math.PI / 2 + Math.PI / n));
        const { lower, upper } = bounds(n);
        byId('lower-value').value = lower.toFixed(9);
        byId('upper-value').value = upper.toFixed(9);
        byId('gap-value').value = (upper - lower).toFixed(9);
        byId('geometry-description').textContent = `A circle of radius 1 with inscribed and circumscribed regular ${n}-sided polygons. The teal inscribed perimeter is shorter; the orange circumscribed perimeter is longer.`;
        presets.forEach(button => {
            const active = Number(button.dataset.sides) === n;
            button.classList.toggle('is-active', active);
            button.setAttribute('aria-pressed', String(active));
        });
        drawChart();
    }

    function stop() {
        if (animation !== null) cancelAnimationFrame(animation);
        animation = null;
        startTime = null;
        play.setAttribute('aria-pressed', 'false');
        play.textContent = '▶ Play demo';
    }

    function manual(value) {
        stop();
        if (Number.isFinite(value)) render(value);
    }
    slider.addEventListener('input', () => manual(Number(slider.value)));
    number.addEventListener('input', () => {
        if (number.validity.valid && number.value !== '') manual(Number(number.value));
    });
    number.addEventListener('change', () => manual(number.value === '' ? n : Number(number.value)));
    number.addEventListener('blur', () => { number.value = n; });
    presets.forEach(button => button.addEventListener('click', () => manual(Number(button.dataset.sides))));
    play.addEventListener('click', () => {
        if (animation !== null) return stop();
        render(3);
        play.setAttribute('aria-pressed', 'true');
        play.textContent = 'Ⅱ Pause demo';
        function tick(time) {
            if (startTime === null) startTime = time;
            const elapsed = time - startTime;
            // Pause briefly at 96 to make the requested milestone easy to inspect.
            const milestoneTime = 9000 * Math.log(96 / 3) / Math.log(1000 / 3);
            const progressTime = elapsed < milestoneTime ? elapsed : elapsed < milestoneTime + 1200 ? milestoneTime : elapsed - 1200;
            render(3 * Math.pow(1000 / 3, Math.min(progressTime / 9000, 1)));
            if (progressTime >= 9000) {
                stop();
                byId('demo-status').textContent = 'Demo complete: the number of sides has reached 1000.';
            } else animation = requestAnimationFrame(tick);
        }
        byId('demo-status').textContent = 'Demo started: the number of sides increases from 3 to 1000, with a brief pause at 96.';
        animation = requestAnimationFrame(tick);
    });
    document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
    render(6);
})();
