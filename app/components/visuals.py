import streamlit.components.v1 as components


def render_rainbow_animation(percentage: float) -> None:
    """
    Renders a realistic vector rainbow with 6 separate color bands using SVG/HTML.
    The animation fills the width of the container.

    Args:
        percentage (float): Probability percentage (0-100) to determine the arc length.
    """
    if percentage is None:
        percentage = 0.0
    percentage = float(percentage)

    # Official Rainbow Colors (CSS Hex)
    colors = ["#FF5F5F", "#FFBD59", "#FFEA61", "#87E787", "#5DB3FF", "#A78BFA"]

    # Configuration
    stroke_width = 40
    gap = 0
    base_radius = 280
    cx = 300
    cy = 300
    viewbox_width = 600
    viewbox_height = 350

    paths_html = ""
    tracks_html = ""

    for i, color in enumerate(colors):
        r = base_radius - (i * (stroke_width + gap))
        arc_len = 3.14159 * r
        target_offset = arc_len - (arc_len * (percentage / 100))
        d = f"M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}"

        # Background Track
        tracks_html += (
            f'<path class="track-band" d="{d}" stroke-width="{stroke_width}"/>'
        )

        # Animated Color Band
        paths_html += f"""
        <path class="rainbow-band"
              d="{d}"
              stroke="{color}"
              stroke-width="{stroke_width}"
              stroke-dasharray="{arc_len}"
              stroke-dashoffset="{arc_len}"
              style="--target-offset: {target_offset}; --delay: {i * 0.08}s;"
        />
        """

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        .container {{
            width: 100%; height: 100%; display: flex;
            flex-direction: column; align-items: center; justify-content: center;
            font-family: 'Segoe UI', sans-serif;
        }}
        .rainbow-svg {{
            width: 100%; height: 100%; max-width: none; overflow: visible;
        }}
        .rainbow-band {{
            fill: none; stroke-linecap: butt;
            animation: drawArch 1.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
            animation-delay: var(--delay);
        }}
        .track-band {{
            fill: none; stroke: #e2e8f0; stroke-linecap: butt; opacity: 0.6;
        }}
        @keyframes drawArch {{ to {{ stroke-dashoffset: var(--target-offset); }} }}
        .text-value {{
            font-size: 4rem; font-weight: 900; fill: #1e293b; text-anchor: middle;
        }}
        .text-label {{
            font-size: 1.2rem; font-weight: 700; fill: #64748b;
            text-anchor: middle; text-transform: uppercase; letter-spacing: 3px;
        }}
    </style>
    </head>
    <body>
        <div class="container">
            <svg class="rainbow-svg" viewBox="0 0 {viewbox_width} {viewbox_height}" preserveAspectRatio="xMidYMid meet">
                {tracks_html}
                {paths_html}
                <text x="{cx}" y="{cy - 40}" class="text-value">{percentage:.1f}%</text>
                <text x="{cx}" y="{cy + 5}" class="text-label">Probability</text>
            </svg>
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=400)
