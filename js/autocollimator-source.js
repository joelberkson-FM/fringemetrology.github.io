// Wrap in a function to allow valid reconfiguration or multiple instances if needed
window.initSourceAutocollimator = function (config = {}) {
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
    const sourceY = centerY - 150;

    // Use Shared Colors from ExperimentLib
    const C_BG = ExperimentLib.Colors.BG;
    const C_WHITE = ExperimentLib.Colors.WHITE;
    const C_GREEN = ExperimentLib.Colors.GREEN;
    // const C_DIM = ExperimentLib.Colors.DIM; // Unused in this scope, but available

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

        // Eye
        ExperimentLib.drawEye(ctx, eyeLensX, centerY);

        // Eyepiece Lens
        ExperimentLib.drawLens(ctx, eyepieceX, centerY, 150, "Lens");

        // Reticle (The plane)
        ExperimentLib.drawReticle(ctx, reticleX, centerY);

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

        // Source Point (Physically moves)
        const drawnSourceX = beamsplitterX + sourceXOffset;
        ExperimentLib.drawStar(ctx, drawnSourceX, sourceY, 4, 6, 2, C_GREEN);
        ctx.fillStyle = C_WHITE;
        ctx.font = ExperimentLib.Fonts.Main;
        ctx.fillText("Source Point", drawnSourceX - 45, sourceY - 15);

        // --- 2. Ray Tracing: Outgoing (White) ---
        // Lens Aperture Targets (Fixed)
        const objTopY = centerY - 35;
        const objBotY = centerY + 35;

        // Dynamic Physics:
        // Virtual Source Calculation (same as before)
        // Virtual Source X = reticleX (300)
        // Virtual Source Y = centerY + sourceXOffset
        const vsX = reticleX;
        const vsY = centerY + sourceXOffset;

        // Beamsplitter Line Equation:
        // Pivot/Center is (beamsplitterX, centerY)
        // Slope is 1 (Top-Left to Bottom-Right on this canvas config)
        // y - centerY = 1 * (x - beamsplitterX)
        // => y = x + (centerY - beamsplitterX)
        const bsIntercept = centerY - beamsplitterX;

        // Function to find intersection of Ray (VS -> LensPoint) and BS Line
        function getBSIntersection(targetX, targetY) {
            // Ray Line: P = VS + t * (Target - VS)
            // x = vsX + t * (targetX - vsX)
            // y = vsY + t * (targetY - vsY)
            // Substitute into BS: y = x + bsIntercept
            // vsY + t(dy) = vsX + t(dx) + bsIntercept
            // t(dy - dx) = vsX + bsIntercept - vsY
            // t = (vsX + bsIntercept - vsY) / (dy - dx)

            const dx = targetX - vsX;
            const dy = targetY - vsY;

            // Check for parallel lines (shouldn't happen here)
            if (Math.abs(dy - dx) < 0.001) return { x: beamsplitterX, y: centerY };

            const t = (vsX + bsIntercept - vsY) / (dy - dx);

            return {
                x: vsX + t * dx,
                y: vsY + t * dy
            };
        }

        const hitTop = getBSIntersection(objectiveX, objTopY);
        const hitBot = getBSIntersection(objectiveX, objBotY);

        // Draw Source -> Beamsplitter (Hit Points)
        ctx.beginPath();
        ctx.moveTo(drawnSourceX, sourceY);
        ctx.lineTo(hitTop.x, hitTop.y);
        ctx.moveTo(drawnSourceX, sourceY);
        ctx.lineTo(hitBot.x, hitBot.y);
        ctx.strokeStyle = C_WHITE;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Draw Beamsplitter -> Objective
        ExperimentLib.drawRay(ctx, hitTop.x, hitTop.y, objectiveX, objTopY, C_WHITE);
        ExperimentLib.drawRay(ctx, hitBot.x, hitBot.y, objectiveX, objBotY, C_WHITE);

        // Objective -> Mirror (Collimated Beam)
        // If source is offset, beam is NOT parallel to axis. It has angle `beamAngle`.
        // Top ray starts at (objectiveX, objTopY) and goes at angle `beamAngle`.
        // y - y0 = m(x - x0). m = tan(beamAngle).
        // At mirrorX: y = objTopY + tan(beamAngle) * (mirrorX - objectiveX)

        const distObjMirror = mirrorX - objectiveX;

        // RE-CALCULATING BEAM ANGLE LOCALLY FOR CLARITY
        // +X offset -> Ray goes "Up" (Negative Angle) assuming Center of Lens is pivot.
        const rayAngle = Math.atan(-sourceXOffset / objFocalLength);

        const mirTopY = objTopY + (distObjMirror * Math.tan(rayAngle));
        const mirBotY = objBotY + (distObjMirror * Math.tan(rayAngle));

        ExperimentLib.drawRay(ctx, objectiveX, objTopY, mirrorX, mirTopY, C_WHITE);
        ExperimentLib.drawRay(ctx, objectiveX, objBotY, mirrorX, mirBotY, C_WHITE);

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


        // --- 4. Return Rays (Green) ---
        // Incoming Ray Angle: rayAngle
        // Mirror Tilt: angleRad
        // Reflected Ray Angle: 
        // If mirror is flat (0), reflected angle = -incident angle (relative to normal).
        // Incident Ray relative to optical axis: rayAngle.
        // Normal relative to optical axis: -angleRad (Mirror tilted by angleRad).
        // Deviation = 2 * (angleRad - rayAngle).

        const reflectedAngle = 2 * angleRad - rayAngle;

        // Calculate where rays hit the Objective on return
        // Start from the points where they hit the mirror: (mirrorX, mirTopY) and (mirrorX, mirBotY).
        // They travel at `reflectedAngle` back to Objective.
        // Delta X = objectiveX - mirrorX (Negative).
        // Delta Y = Delta X * tan(reflectedAngle).

        // Return Hit Y (top ray)
        const retTopY = mirTopY + (objectiveX - mirrorX) * Math.tan(reflectedAngle);
        const retBotY = mirBotY + (objectiveX - mirrorX) * Math.tan(reflectedAngle);

        // 4a. Mirror -> Objective
        ExperimentLib.drawRay(ctx, mirrorX, mirTopY, objectiveX, retTopY, C_GREEN);
        ExperimentLib.drawRay(ctx, mirrorX, mirBotY, objectiveX, retBotY, C_GREEN);

        // 4b. Objective -> Reticle (Focus)
        // Rays focused by objective meet at the focal plane (Reticle X).
        // Height h = f * tan(theta_in). 
        // Here theta_in = reflectedAngle.
        // So h = f * tan(reflectedAngle).
        const h = objFocalLength * Math.tan(reflectedAngle);
        const focusPointY = centerY + h;

        ctx.beginPath();
        ctx.strokeStyle = C_GREEN;
        // From Objective Top/Bot to Focus Point
        ctx.moveTo(objectiveX, retTopY);
        ctx.lineTo(reticleX, focusPointY);
        ctx.moveTo(objectiveX, retBotY);
        ctx.lineTo(reticleX, focusPointY);
        ctx.stroke();

        // 4c. Reticle -> Eyepiece (Expansion)
        // Rays pass through focus and hit Eyepiece
        // We project lines from focus point to Eyepiece lens edges to simulate full aperture usage
        // Or strictly follow the ray geometry. Let's strictly follow ray geometry for "these specific rays".
        // Geometrically: Line from ObjEdge -> FocusPoint -> Eyepiece.

        // Calculate Y at Eyepiece based on slope
        const slopeTop = (focusPointY - retTopY) / (reticleX - objectiveX);
        const slopeBot = (focusPointY - retBotY) / (reticleX - objectiveX);

        const epTopY = focusPointY + slopeTop * (eyepieceX - reticleX);
        const epBotY = focusPointY + slopeBot * (eyepieceX - reticleX);

        ctx.beginPath();
        ctx.moveTo(reticleX, focusPointY);
        ctx.lineTo(eyepieceX, epTopY);
        ctx.moveTo(reticleX, focusPointY);
        ctx.lineTo(eyepieceX, epBotY);
        ctx.stroke();

        // 4d. Eyepiece -> Eye Lens (Collimation)
        // We fix the endpoints at the eye to simulate the rays entering the pupil at a constant position.
        const eyePupilSpread = 7;

        ctx.beginPath();
        ctx.moveTo(eyepieceX, epTopY);
        ctx.lineTo(eyeLensX, centerY + eyePupilSpread);
        ctx.moveTo(eyepieceX, epBotY);
        ctx.lineTo(eyeLensX, centerY - eyePupilSpread);
        ctx.stroke();

        // --- 5. Annotations (Dashed Lines & Labels) ---



        // --- 6. Reticle View Overlay ---
        drawReticleView(h);
    }

    // --- Helper Functions ---

    // Note: drawEye, drawLens, drawReticle, drawRay, drawStar removed in favor of ExperimentLib

    function drawReticleView(h) {
        const viewX = 250;
        const viewY = 100;
        const viewR = 45;

        // Clip area
        ctx.save();
        ctx.setLineDash([]); // Ensure solid lines in reticle view
        ctx.beginPath();
        ctx.arc(viewX, viewY, viewR, 0, 2 * Math.PI);
        ctx.clip();

        // Background
        ctx.fillStyle = "#00102b";
        ctx.fill();

        // Crosshairs (always solid)
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(viewX - viewR, viewY);
        ctx.lineTo(viewX + viewR, viewY);
        ctx.moveTo(viewX, viewY - viewR);
        ctx.lineTo(viewX, viewY + viewR);
        ctx.strokeStyle = "rgba(255,255,255,0.3)";
        ctx.lineWidth = 1;
        ctx.stroke();

        // Measurement Spot
        // Scale h down slightly for the view
        const viewScale = 0.9;
        const spotY = viewY + (h * viewScale);

        ctx.beginPath();
        // Draw a little cross or star for the return spot
        ExperimentLib.drawStar(ctx, viewX, spotY, 4, 4, 1.5, C_GREEN);

        ctx.restore(); // End Clip

        // Circle Border
        ctx.setLineDash([]); // Ensure solid line
        ctx.beginPath();
        ctx.arc(viewX, viewY, viewR, 0, 2 * Math.PI);
        ctx.strokeStyle = C_WHITE;
        ctx.lineWidth = 2;
        ctx.stroke();

        // Label
        ctx.fillStyle = C_WHITE;
        ctx.font = ExperimentLib.Fonts.Main;
        ctx.textAlign = "center";
        ctx.fillText("Reticle View", viewX, viewY - 55);
    }

    // --- Helper for Displays ---
    function updateDisplays() {
        if (cfg.tiltDisplayId) {
            const el = document.getElementById(cfg.tiltDisplayId);
            if (el) el.textContent = parseFloat(slider.value).toFixed(2) + "°";
        }
        if (cfg.sourceDisplayId) {
            const el = document.getElementById(cfg.sourceDisplayId);
            if (el) el.textContent = parseFloat(sourceSlider.value).toFixed(1) + " mm";
        }
    }

    // --- Coupling Logic (Auto Align) ---
    function updateFromTilt() {
        if (cfg.autoAlignCheckboxId) {
            const autoAlign = document.getElementById(cfg.autoAlignCheckboxId);
            if (autoAlign && autoAlign.checked) {
                const angleRad = parseFloat(slider.value) * (Math.PI / 180);
                // Same physics: x = -f * tan(2*theta)
                let targetSourceX = objFocalLength * Math.tan(-2 * angleRad);

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
                // theta = 0.5 * atan(-x/f)
                let targetThetaRad = 0.5 * Math.atan(-sourceX / objFocalLength);
                let targetThetaDeg = targetThetaRad * (180 / Math.PI);

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

    updateDisplays();
    draw();
};

document.addEventListener('DOMContentLoaded', function () {
    // Only auto-init if we are NOT on a page that handles it manually.
    // However, if both scripts are loaded, we need to be careful.
    // For now, let's assume if the default elements exist, we init.
    // BUT since we are using unique IDs on the new page, this shouldn't fire there.
    // It WILL fire on `test.html` which is good.
    window.initSourceAutocollimator();
});
