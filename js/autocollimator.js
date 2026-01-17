document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('simCanvas');
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
    const slider = document.getElementById('tiltSlider');

    // Add Reset Button
    // We want it in the top-left of the main container
    const container = canvas.closest('.container') || canvas.parentElement;
    if (container) {
        // Ensure container is relative for absolute positioning
        if (getComputedStyle(container).position === 'static') {
            container.style.position = 'relative';
        }

        ExperimentLib.addResetButton(container, () => {
            slider.value = 0;
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

        // Source Point
        ExperimentLib.drawStar(ctx, beamsplitterX, sourceY, 4, 6, 2, C_GREEN);
        ctx.fillStyle = C_WHITE;
        ctx.font = ExperimentLib.Fonts.Label;
        ctx.fillText("Source Point", beamsplitterX - 45, sourceY - 15);

        // --- 2. Ray Tracing: Outgoing (White) ---
        // Source -> Beamsplitter
        ctx.beginPath();
        ctx.moveTo(beamsplitterX, sourceY);
        // Hit points on Beamsplitter (Simulating beam width)
        const spread = 15;
        const bsTopX = beamsplitterX - spread;
        const bsTopY = centerY - spread;
        const bsBotX = beamsplitterX + spread;
        const bsBotY = centerY + spread;

        ctx.lineTo(bsTopX, bsTopY);
        ctx.moveTo(beamsplitterX, sourceY);
        ctx.lineTo(bsBotX, bsBotY);
        ctx.strokeStyle = C_WHITE;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Beamsplitter -> Objective
        const objTopY = centerY - 35;
        const objBotY = centerY + 35;

        ExperimentLib.drawRay(ctx, bsTopX, bsTopY, objectiveX, objTopY, C_WHITE);
        ExperimentLib.drawRay(ctx, bsBotX, bsBotY, objectiveX, objBotY, C_WHITE);

        // Objective -> Mirror (Parallel)
        // Adjust mirror hit points based on tilt to keep lines visually clean
        // (Visual trick: we draw to a vertical line at mirrorX, ignoring slight depth change from tilt)
        ExperimentLib.drawRay(ctx, objectiveX, objTopY, mirrorX, objTopY, C_WHITE);
        ExperimentLib.drawRay(ctx, objectiveX, objBotY, mirrorX, objBotY, C_WHITE);

        // --- 3. Mirror Component ---
        ctx.save();
        ctx.translate(mirrorX, centerY);
        ctx.rotate(angleRad);

        // Mirror Body
        ctx.fillStyle = C_WHITE;
        ctx.fillRect(-3, -80, 6, 160);

        ctx.font = ExperimentLib.Fonts.Label;
        ctx.textAlign = "center";
        ctx.fillText("Mirror", 0, 100);
        ctx.restore();


        // --- 4. Return Rays (Green) ---
        // Logic: The mirror is tilted by alpha. The reflected ray is tilted by 2*alpha.
        const reflectAngle = 2 * angleRad;

        // Calculate where rays hit the Objective on return
        // Distance from mirror to objective
        const distToObj = mirrorX - objectiveX;

        // The return rays are parallel to each other, but angled relative to optical axis
        const retTopY = objTopY - (distToObj * Math.tan(reflectAngle));
        const retBotY = objBotY - (distToObj * Math.tan(reflectAngle));

        // 4a. Mirror -> Objective
        ExperimentLib.drawRay(ctx, mirrorX, objTopY, objectiveX, retTopY, C_GREEN);
        ExperimentLib.drawRay(ctx, mirrorX, objBotY, objectiveX, retBotY, C_GREEN);

        // 4b. Objective -> Reticle (Focus)
        // Rays focused by objective meet at the focal plane (Reticle X)
        // Height h = f * tan(theta)
        const h = objFocalLength * Math.tan(reflectAngle);
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

        // Draw the 2alpha angle indication
        if (Math.abs(angleDeg) > 1) {
            ctx.beginPath();
            ctx.setLineDash([4, 4]);
            ctx.strokeStyle = ExperimentLib.Colors.ANNOTATION;
            // Dashed line continuing straight from objective
            ctx.moveTo(objectiveX, objTopY);
            ctx.lineTo(objectiveX + 150, objTopY);
            ctx.stroke();
        }

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
        ctx.font = ExperimentLib.Fonts.Label;
        ctx.textAlign = "center";
        ctx.fillText("Reticle View", viewX, viewY - 55);
    }

    slider.addEventListener('input', draw);
    window.addEventListener('resize', draw);

    // Initial draw
    draw();
});
