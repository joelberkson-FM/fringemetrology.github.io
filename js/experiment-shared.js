/**
 * experiment-shared.js
 * Shared library for Fringe Metrology experiments/simulations.
 * Contains common colors, fonts, and drawing helpers.
 */

const ExperimentLib = {
    // --- Colors ---
    Colors: {
        BG: "#011D49",
        WHITE: "#ffffff",
        GREEN: "#cce85e",
        DIM: "rgba(255, 255, 255, 0.3)",
        AXIS: "rgba(255, 255, 255, 0.15)",
        BEAMSPLITTER: "rgba(255, 255, 255, 0.5)",
        LENS_GLASS: "rgba(200, 230, 255, 0.1)",
        ANNOTATION: "rgba(255,255,255,0.4)"
    },

    // --- Fonts ---
    Fonts: {
        Main: "400 14px Montserrat",
        Italic: "italic 400 16px Montserrat",
        Label: "400 14px Montserrat" // Standardized Label Font
    },

    // --- UI Helpers ---
    /**
     * Adds a Reset button to a container.
     * @param {HTMLElement} container The container to append the button to.
     * @param {Function} onClick The callback to run when clicked.
     */
    addResetButton: function (container, onClick, options = {}) {
        if (!container) return;
        console.log("Adding reset button to", container);
        const btn = document.createElement('button');
        btn.textContent = "Reset";

        // Base styles
        const styles = {
            padding: "8px 24px",
            backgroundColor: "transparent",
            border: "1px solid #cce85e",
            color: "#cce85e",
            fontFamily: "Montserrat, sans-serif",
            fontSize: "12px",
            fontWeight: "600",
            textTransform: "uppercase",
            letterSpacing: "1px",
            cursor: "pointer",
            borderRadius: "4px",
            transition: "all 0.2s ease",
            zIndex: "100" // Ensure it's on top
        };

        // Positioning logic
        if (options.position === 'top-left') {
            Object.assign(styles, {
                position: "absolute",
                top: "20px",
                left: "20px",
                marginTop: "0"
            });
        } else {
            styles.marginTop = "15px";
        }

        Object.assign(btn.style, styles);

        btn.addEventListener('mouseover', () => {
            btn.style.backgroundColor = "rgba(204, 232, 94, 0.1)";
            btn.style.boxShadow = "0 0 10px rgba(204, 232, 94, 0.3)";
        });
        btn.addEventListener('mouseout', () => {
            btn.style.backgroundColor = "transparent";
            btn.style.boxShadow = "none";
        });

        btn.addEventListener('click', onClick);
        container.appendChild(btn);
    },

    // --- Drawing Helpers ---

    /**
     * Draws a simple representation of a human eye.
     * @param {CanvasRenderingContext2D} ctx 
     * @param {number} x Center X position of the eye's lens
     * @param {number} y Center Y position
     */
    drawEye: function (ctx, x, y) {
        ctx.save();
        ctx.strokeStyle = this.Colors.WHITE;
        ctx.lineWidth = 2;

        const lensX = x;
        const retinaX = x - 25;

        // Top edge
        ctx.beginPath();
        ctx.moveTo(retinaX, y);
        ctx.lineTo(lensX + 10, y - 25);
        ctx.stroke();

        // Bottom edge
        ctx.beginPath();
        ctx.moveTo(retinaX, y);
        ctx.lineTo(lensX + 10, y + 25);
        ctx.stroke();

        // Biconvex lens at front
        ctx.beginPath();
        ctx.ellipse(lensX, y, 5, 15, 0, 0, 2 * Math.PI);
        ctx.stroke();

        // Label
        ctx.fillStyle = this.Colors.WHITE;
        ctx.font = this.Fonts.Label;
        ctx.fillText("Eye", retinaX - 5, y + 45);
        ctx.restore();
    },

    /**
     * Draws a generic lens.
     * @param {CanvasRenderingContext2D} ctx 
     * @param {number} x Center X
     * @param {number} y Center Y
     * @param {number} height Lens height
     * @param {string} [label] Optional label text
     */
    drawLens: function (ctx, x, y, height, label) {
        ctx.save();
        ctx.beginPath();
        // Biconvex lens shape
        ctx.ellipse(x, y, 6, height / 2, 0, 0, 2 * Math.PI);
        ctx.strokeStyle = this.Colors.WHITE;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Glass look
        ctx.fillStyle = this.Colors.LENS_GLASS;
        ctx.fill();

        if (label) {
            ctx.fillStyle = this.Colors.WHITE;
            ctx.font = this.Fonts.Label;
            ctx.fillText(label, x - 15, y - (height / 2 + 15));
        }
        ctx.restore();
    },

    /**
     * Draws a reticle (focal plane) with tick marks.
     * @param {CanvasRenderingContext2D} ctx 
     * @param {number} x Center X
     * @param {number} y Center Y
     */
    drawReticle: function (ctx, x, y) {
        ctx.save();
        // Vertical line for plane
        ctx.beginPath();
        ctx.moveTo(x, y - 50);
        ctx.lineTo(x, y + 50);
        ctx.strokeStyle = this.Colors.WHITE;
        ctx.lineWidth = 2;
        ctx.stroke();

        // Tick marks
        ctx.lineWidth = 1;
        for (let i = -40; i <= 40; i += 10) {
            ctx.beginPath();
            ctx.moveTo(x - 3, y + i);
            ctx.lineTo(x + 3, y + i);
            ctx.stroke();
        }

        ctx.fillStyle = this.Colors.WHITE;
        ctx.font = this.Fonts.Label;
        ctx.fillText("Reticle", x - 20, y - 60);
        ctx.restore();
    },

    /**
     * Draws a simple ray line.
     * @param {CanvasRenderingContext2D} ctx 
     * @param {number} x1 
     * @param {number} y1 
     * @param {number} x2 
     * @param {number} y2 
     * @param {string} color 
     */
    drawRay: function (ctx, x1, y1, x2, y2, color) {
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.restore();
    },

    /**
     * Draws a star/sparkle shape.
     * @param {CanvasRenderingContext2D} ctx 
     * @param {number} cx Center X
     * @param {number} cy Center Y
     * @param {number} spikes Number of points
     * @param {number} outerRadius Outer radius
     * @param {number} innerRadius Inner radius
     * @param {string} color Fill color
     */
    drawStar: function (ctx, cx, cy, spikes, outerRadius, innerRadius, color) {
        ctx.save();
        let rot = Math.PI / 2 * 3;
        let x = cx;
        let y = cy;
        let step = Math.PI / spikes;

        ctx.beginPath();
        ctx.moveTo(cx, cy - outerRadius)
        for (i = 0; i < spikes; i++) {
            x = cx + Math.cos(rot) * outerRadius;
            y = cy + Math.sin(rot) * outerRadius;
            ctx.lineTo(x, y)
            rot += step

            x = cx + Math.cos(rot) * innerRadius;
            y = cy + Math.sin(rot) * innerRadius;
            ctx.lineTo(x, y)
            rot += step
        }
        ctx.lineTo(cx, cy - outerRadius)
        ctx.closePath();
        ctx.fillStyle = color;
        ctx.fill();
        ctx.restore();
    },

    /**
     * Initial setup helper to ensure high-DPI handling could go here in future.
     */
    init: function () {
        // Placeholder for any global initialization if needed.
    }
};

// Expose to window if needed (usually implicit, but good for clarity)
window.ExperimentLib = ExperimentLib;
