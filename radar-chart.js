const AXIS_COUNT = 5;
const SIZE = 320;
const CENTER = SIZE / 2;
const MAX_RADIUS = 110;
const RING_COUNT = 4;
const LABEL_OFFSET = 26;

function pointOnAxis(index, radius) {
    const angle = (Math.PI * 2 * index) / AXIS_COUNT - Math.PI / 2;
    return [CENTER + radius * Math.cos(angle), CENTER + radius * Math.sin(angle)];
}

function polygonPoints(radius) {
    return Array.from({ length: AXIS_COUNT }, (_, i) => pointOnAxis(i, radius).join(',')).join(' ');
}

function svgEl(tag, attrs) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
    return el;
}

function anchorFor(x) {
    if (x < CENTER - 5) return 'end';
    if (x > CENTER + 5) return 'start';
    return 'middle';
}

function baselineFor(y) {
    if (y < CENTER - 5) return 'baseline';
    if (y > CENTER + 5) return 'hanging';
    return 'middle';
}

// categories: [{ label, score }] with score in 0-100, exactly AXIS_COUNT entries.
export function renderRadarChart(containerId, categories) {
    const container = document.getElementById(containerId);
    if (!container || categories.length !== AXIS_COUNT) return;

    container.innerHTML = '';

    const svg = svgEl('svg', {
        viewBox: `0 0 ${SIZE} ${SIZE}`,
        class: 'radar-svg',
        role: 'img',
        'aria-label': 'Profile radar chart across ' + categories.map((c) => c.label).join(', '),
    });

    for (let ring = 1; ring <= RING_COUNT; ring++) {
        svg.append(svgEl('polygon', {
            points: polygonPoints((MAX_RADIUS * ring) / RING_COUNT),
            class: 'radar-grid-ring',
        }));
    }

    categories.forEach((_, i) => {
        const [x, y] = pointOnAxis(i, MAX_RADIUS);
        svg.append(svgEl('line', { x1: CENTER, y1: CENTER, x2: x, y2: y, class: 'radar-axis-line' }));
    });

    const clampedScores = categories.map((cat) => Math.max(0, Math.min(100, cat.score)));

    svg.append(svgEl('polygon', {
        points: clampedScores.map((score, i) => pointOnAxis(i, (MAX_RADIUS * score) / 100).join(',')).join(' '),
        class: 'radar-data-polygon',
    }));

    clampedScores.forEach((score, i) => {
        const [x, y] = pointOnAxis(i, (MAX_RADIUS * score) / 100);
        svg.append(svgEl('circle', { cx: x, cy: y, r: 3.5, class: 'radar-data-dot' }));
    });

    categories.forEach((cat, i) => {
        const [x, y] = pointOnAxis(i, MAX_RADIUS + LABEL_OFFSET);
        const anchor = anchorFor(x);
        const baseline = baselineFor(y);

        const label = svgEl('text', { x, y, 'text-anchor': anchor, 'dominant-baseline': baseline, class: 'radar-label' });
        label.textContent = cat.label;

        const scoreLabel = svgEl('text', {
            x, y: y + 14, 'text-anchor': anchor, 'dominant-baseline': baseline, class: 'radar-label-score',
        });
        scoreLabel.textContent = Math.round(clampedScores[i]);

        svg.append(label);
        svg.append(scoreLabel);
    });

    container.append(svg);
}
