// Wrap in a function to allow valid reconfiguration or multiple instances if needed
window.initSLAAutocollimator = function (config = {}) {
    const defaultIds = {
        canvasId: 'simCanvas',
        tiltSliderId: 'tiltSlider',
        sourceSliderId: 'sourceSlider'
    };

    // Merge defaults
    const cfg = { ...defaultIds, ...config };

    const canvas = document.getElementById(cfg.canvasId);
    if (!canvas) return; // Exit if canvas not found (e.g. on other pages)

    // Mobile Detection: Do not load/display on small screens
    if (window.innerWidth < 768) {
        const section = canvas.closest('.autocollimator-section') || canvas.closest('.container');
        if (section) {
            section.style.display = 'none';
        }
        return; // Stop execution
    }

    const ctx = canvas.getContext('2d');
    const slider = document.getElementById(cfg.tiltSliderId);
    const sourceSlider = document.getElementById(cfg.sourceSliderId);

    if (!slider || !sourceSlider) {
        console.warn("Source Autocollimator: Sliders not found.", cfg);
        return;
    }

    // Add Reset Button
    // We want it in the top-left of the main container
    const container = canvas.closest('.container') || canvas.parentElement;
    if (container) {
        // Ensure container is relative for absolute positioning (it is in CSS, but safeguards help)
        if (getComputedStyle(container).position === 'static') {
            container.style.position = 'relative';
        }

        ExperimentLib.addResetButton(container, () => {
            slider.value = 0;
            sourceSlider.value = 0;
            // dispatch input event so any listeners update (drawing logic)
            // or just call draw();
            updateDisplays();
            draw();
        }, { position: 'top-left' });
    }

    // --- Configuration ---
    // Use canvas.width/height directly so it responds to attributes
    let width = canvas.width;
    let height = canvas.height;
    let centerY = height / 2 + 30; // Shifted down slightly

    // X Positions (The Optical Train)
    const eyeRetinaX = 40;
    const eyeLensX = 100;
    const eyepieceX = 220;    // Lens 2
    const reticleX = 300;     // The Focal Plane
    const beamsplitterX = 450;
    const objectiveX = 680;   // Lens 1
    const mirrorX = 900;

    const objFocalLength = objectiveX - reticleX;
    const distObjMirror = mirrorX - objectiveX; // 220
    const sourceY = centerY - 150;

    // Use Shared Colors from ExperimentLib
    const C_BG = ExperimentLib.Colors.BG;
    const C_WHITE = ExperimentLib.Colors.WHITE;
    const C_GREEN = ExperimentLib.Colors.GREEN;
    // const C_DIM = ExperimentLib.Colors.DIM; // Unused in this scope, but available

    // Apply Limits
    if (sourceSlider) {
        sourceSlider.min = -23.1;
        sourceSlider.max = 23.1;
    }

    // Update dimensions on resize (if we decide to make it responsive via JS later)
    // For now, relies on width/height attributes or CSS scaling. 
    // Usually good to re-read width/height in draw loop if they change.

    // Main Draw Loop
    function draw() {
        // Ensure we use current canvas dimensions
        width = canvas.width;
        height = canvas.height;
        centerY = height / 2 + 30;

        ctx.clearRect(0, 0, width, height);

        // Reset context state that might linger from previous frame
        ctx.textAlign = 'start';


        const angleDeg = parseFloat(slider.value);
        const angleRad = angleDeg * (Math.PI / 180);

        const sourceXOffset = parseFloat(sourceSlider.value); // mm
        // Physics: 
        // 1. Source moves laterally by X.
        // 2. Virtual source moves laterally by X.
        // 3. Beam leaves collimator at angle theta = atan(X / f) relative to axis.
        const beamAngle = Math.atan(sourceXOffset / objFocalLength);


        // --- 1. Draw Static Optical Components ---

        // Optical Axis
        ctx.beginPath();
        ctx.setLineDash([5, 5]);
        ctx.strokeStyle = ExperimentLib.Colors.AXIS;
        ctx.moveTo(eyeLensX, centerY);
        ctx.lineTo(mirrorX, centerY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Sensor (was Eye)
        ctx.beginPath();
        ctx.lineWidth = 4;
        ctx.strokeStyle = C_WHITE; // Sensor matches mirror style
        // Vertical line for sensor
        ctx.moveTo(eyeLensX, centerY - 30);
        ctx.lineTo(eyeLensX, centerY + 30);
        ctx.stroke();

        ctx.fillStyle = C_WHITE;
        ctx.font = ExperimentLib.Fonts.Label;
        ctx.fillText("Sensor", eyeLensX - 20, centerY + 50);

        // Eyepiece Lens
        ExperimentLib.drawLens(ctx, eyepieceX, centerY, 150, "Lens");

        // Aperture (was Reticle)
        // Draw two blocking rectangles with a gap in the middle
        const apWidth = 4;
        const apHeight = 50;
        const gap = 1;

        ctx.fillStyle = "#FFFFFF";
        // Top block
        ctx.fillRect(reticleX - apWidth / 2, centerY - gap - apHeight, apWidth, apHeight);
        // Bottom block
        ctx.fillRect(reticleX - apWidth / 2, centerY + gap, apWidth, apHeight);

        ctx.fillStyle = C_WHITE;
        ctx.font = ExperimentLib.Fonts.Label;
        ctx.fillText("Aperture", reticleX - 25, centerY + 70);

        // Objective Lens
        ExperimentLib.drawLens(ctx, objectiveX, centerY, 200, "Lens");

        // Beamsplitter
        ctx.beginPath();
        ctx.moveTo(beamsplitterX - 40, centerY - 40);
        ctx.lineTo(beamsplitterX + 40, centerY + 40);
        ctx.strokeStyle = ExperimentLib.Colors.BEAMSPLITTER;
        ctx.lineWidth = 3;
        ctx.stroke();
        ctx.fillStyle = C_WHITE;
        ctx.font = ExperimentLib.Fonts.Label;
        ctx.fillText("Beamsplitter", beamsplitterX - 45, centerY + 65);

        // Micro Display (was Source Point)
        const drawnSourceX = beamsplitterX + sourceXOffset;

        // Draw a small rectangle for the display (Stationary)
        ctx.fillStyle = "#000000ff";
        // Fixed at beamsplitterX
        ctx.fillRect(beamsplitterX - 45, sourceY - 4, 90, 8);

        // Draw the "active pixel" (Moves with drawnSourceX)
        ctx.fillStyle = C_GREEN;
        ctx.fillRect(drawnSourceX - 3, sourceY - 3, 6, 6);

        ctx.fillStyle = C_WHITE;
        ctx.font = ExperimentLib.Fonts.Main;
        ctx.fillText("Micro Display", beamsplitterX - 45, sourceY - 25);

        // --- 2. Ray Tracing: Adjusted to User Request ---
        // Constraint: Output ray from active pixel always goes "down" and hits Mirror Center
        // Path: Source -> Beamsplitter -> Objective -> Mirror

        // 1. Source (Active Pixel) -> Beamsplitter
        const sourcePixelX = drawnSourceX;
        const sourcePixelY = sourceY;

        // Calculate where a vertical drop hits the BS (45deg line)
        // BS Line eq: y = x - beamsplitterX + centerY
        // We drop vertically, so x = sourcePixelX.
        const bsHitY = sourcePixelX - beamsplitterX + centerY;

        ctx.beginPath();
        ctx.moveTo(sourcePixelX, sourcePixelY);
        ctx.lineTo(sourcePixelX, bsHitY);
        ctx.strokeStyle = C_WHITE;
        ctx.lineWidth = 1;
        ctx.stroke();

        // 2. Beamsplitter -> Objective
        // Vertical ray reflects 90deg -> Horizontal
        // Travels from (sourcePixelX, bsHitY) to Objective at same height
        ctx.beginPath();
        ctx.moveTo(sourcePixelX, bsHitY);
        ctx.lineTo(objectiveX, bsHitY);
        ctx.stroke();

        // 3. Objective -> Mirror (Forced to Center)
        // Ray pivots at Objective to hit Mirror Center (mirrorX, centerY)
        // const distObjMirror = mirrorX - objectiveX; // Now defined in outer scope

        // Calculate the angle required to hit the center
        // slope = (targetY - startY) / dist
        // slope = (centerY - bsHitY) / distObjMirror
        const raySlope = (centerY - bsHitY) / distObjMirror;
        const rayAngle = Math.atan(raySlope);
        const mirHitY = centerY; // Forced to center

        ExperimentLib.drawRay(ctx, objectiveX, bsHitY, mirrorX, mirHitY, C_WHITE);


        // --- 3. Mirror Component ---
        ctx.save();
        ctx.translate(mirrorX, centerY);
        ctx.rotate(angleRad);

        // Mirror Body
        ctx.fillStyle = C_WHITE;
        ctx.fillRect(-3, -80, 6, 160);

        ctx.font = ExperimentLib.Fonts.Main;
        ctx.textAlign = "center";
        ctx.fillText("Mirror", 0, 100);
        ctx.restore();


        // --- 4. Return Ray (Green) ---
        // Angle relative to axis: reflectedAngle
        // Starts at (mirrorX, mirHitY)
        const reflectedAngle = 2 * angleRad - rayAngle;

        // Calculate hit point back on Objective (X = objectiveX)
        // Ray travels left: deltaX = objectiveX - mirrorX (negative)
        // slope = tan(reflectedAngle)
        const returnObjY = mirHitY + (objectiveX - mirrorX) * Math.tan(reflectedAngle);

        // 4a. Mirror -> Objective
        ExperimentLib.drawRay(ctx, mirrorX, mirHitY, objectiveX, returnObjY, C_GREEN);

        // 4b. Objective -> Aperture (Focus)
        // Ray focuses at the focal plane (ReticleX).
        // Height h = f * tan(theta_in) = f * tan(reflectedAngle).
        const h = objFocalLength * Math.tan(reflectedAngle);
        const focusPointY = centerY + h;

        ctx.beginPath();
        ctx.strokeStyle = C_GREEN;
        ctx.moveTo(objectiveX, returnObjY);
        ctx.lineTo(reticleX, focusPointY);
        ctx.stroke();

        // 4c. Aperture -> Eyepiece -> Sensor
        // We continue the ray path from the Aperture (Focus Point) through the Eyepiece to the Sensor.
        // CHECK: Does the ray pass through the aperture?
        // Gap is defined above as `const gap = 2;` (which is +/- 2 from center, so total 4mm opening? actually gap variable is usually from center)
        // Let's re-read the aperture drawing logic:
        // ctx.fillRect(reticleX - apWidth / 2, centerY - gap - apHeight, apWidth, apHeight);
        // This suggests the "gap" starts at centerY - gap.
        // So the opening is indeed +/- gap.

        let isHit = false;

        if (Math.abs(h) <= gap) {
            isHit = true;
            // Ray Passes!
            // Geometric projection from previous segment.

            // Slope of the ray segment (Objective -> Aperture)
            const slope = (focusPointY - returnObjY) / (reticleX - objectiveX);

            // Calculate hit at Eyepiece
            const epHitY = focusPointY + slope * (eyepieceX - reticleX);

            // Calculate hit at Sensor
            const sensorHitY = epHitY + slope * (eyeLensX - eyepieceX);

            ctx.beginPath();
            ctx.moveTo(reticleX, focusPointY);
            ctx.lineTo(eyepieceX, epHitY); // Through Eyepiece
            ctx.lineTo(eyeLensX, sensorHitY); // To Sensor
            ctx.stroke();
        } else {
            // Ray Blocked!
            // We already drew the line TO the reticle/aperture in step 4b.
            // We can optionally draw a small "hit" marker or just stop.
            // Let's just stop.
        }

        // --- 5. Annotations (Dashed Lines & Labels) ---



        // --- 6. Annotations (Dashed Lines & Labels) --- (End of drawing)

        // --- 7. Sensor View Overlay ---
        drawSensorView(isHit);
    }

    // --- Helper Functions ---

    // Note: drawEye, drawLens, drawReticle, drawRay, drawStar removed in favor of ExperimentLib

    function drawSensorView(isHit) {
        ctx.save();
        ctx.setLineDash([]); // Ensure solid lines

        const viewX = 250;
        const viewY = 100;
        const viewW = 80;
        const viewH = 60;

        // 1. Fill Background (Always start with Black/Dark)
        // This ensures "when not aligned, I want the Sensor view to always show as a dark rectangle"
        ctx.fillStyle = "#000000";
        ctx.fillRect(viewX - viewW / 2, viewY - viewH / 2, viewW, viewH);

        // 2. If Hit, Fill with White
        // "This touches the sensor but I don't see the white sensor view"
        if (isHit) {
            ctx.fillStyle = "#FFFFFF"; // Explicit White
            ctx.fillRect(viewX - viewW / 2, viewY - viewH / 2, viewW, viewH);
        }

        // 3. Draw Box Outline
        ctx.strokeStyle = "#FFFFFF";
        ctx.lineWidth = 2;
        ctx.strokeRect(viewX - viewW / 2, viewY - viewH / 2, viewW, viewH);

        // 4. Label
        ctx.fillStyle = "#FFFFFF";
        ctx.font = ExperimentLib.Fonts.Main;
        ctx.textAlign = "center";

        ctx.fillText("Sensor View", viewX, viewY - 45);
        ctx.restore();
    }



    function updateDisplays() {
        if (cfg.tiltDisplayId) {
            const el = document.getElementById(cfg.tiltDisplayId);
            if (el) el.textContent = parseFloat(slider.value).toFixed(2) + "°";
        }
        if (cfg.sourceDisplayId) {
            const el = document.getElementById(cfg.sourceDisplayId);
            if (el) el.textContent = parseFloat(sourceSlider.value).toFixed(1) + " px";
        }
    }

    // --- Coupling Logic ---
    // Goal: 1 counter acts the other to stay aligned.
    // Alignment Condition: Ray hits the true return path center (aperture center).
    // Due to the "forced center" ray tracing logic, this corresponds to:
    // angle(ray from lens) = 2 * mirror_angle
    // atan(-sourceX / distObjMirror) = 2 * mirror_angle
    // sourceX = -distObjMirror * tan(2 * mirror_angle)

    function updateFromTilt() {
        if (cfg.autoAlignCheckboxId) {
            const autoAlign = document.getElementById(cfg.autoAlignCheckboxId);
            if (autoAlign && autoAlign.checked) {
                const angleRad = parseFloat(slider.value) * (Math.PI / 180);
                // Condition for alignment using distObjMirror (220)
                let targetSourceX = distObjMirror * Math.tan(-2 * angleRad);

                // Clamp to slider range
                const min = parseFloat(sourceSlider.min);
                const max = parseFloat(sourceSlider.max);
                if (targetSourceX < min) targetSourceX = min;
                if (targetSourceX > max) targetSourceX = max;

                sourceSlider.value = targetSourceX;
            }
        }
        updateDisplays();
        draw();
    }

    function updateFromSource() {
        if (cfg.autoAlignCheckboxId) {
            const autoAlign = document.getElementById(cfg.autoAlignCheckboxId);
            if (autoAlign && autoAlign.checked) {
                const sourceX = parseFloat(sourceSlider.value);
                // sourceX = -dist * tan(2*theta)
                // -sourceX/dist = tan(2*theta)
                // 2*theta = atan(-sourceX/dist)
                // theta = 0.5 * atan(-sourceX / distObjMirror)

                let targetThetaRad = 0.5 * Math.atan(-sourceX / distObjMirror);
                let targetThetaDeg = targetThetaRad * (180 / Math.PI);

                // Clamp
                const min = parseFloat(slider.min);
                const max = parseFloat(slider.max);
                if (targetThetaDeg < min) targetThetaDeg = min;
                if (targetThetaDeg > max) targetThetaDeg = max;

                slider.value = targetThetaDeg;
            }
        }
        updateDisplays();
        draw();
    }

    slider.addEventListener('input', updateFromTilt);
    sourceSlider.addEventListener('input', updateFromSource);

    if (cfg.autoAlignCheckboxId) {
        const autoAlign = document.getElementById(cfg.autoAlignCheckboxId);
        if (autoAlign) {
            autoAlign.addEventListener('change', updateFromTilt);
        }
    }

    window.addEventListener('resize', draw);

    // Initial update
    updateDisplays();
    draw();
};

document.addEventListener('DOMContentLoaded', function () {
    // Only auto-init if we are NOT on a page that handles it manually.
    // However, if both scripts are loaded, we need to be careful.
    // For now, let's assume if the default elements exist, we init.
    // BUT since we are using unique IDs on the new page, this shouldn't fire there.
    // It WILL fire on `test.html` which is good.
    window.initSLAAutocollimator();
});
