"""
generate_samples.py — Create small sample lecture PDFs for demo purposes.

Uses reportlab (lightweight PDF generation library) to produce simple
multi-page lecture PDFs.  Run once:

    pip install reportlab
    python generate_samples.py

The PDFs are written to the sample_data/ folder.
"""

import os
import textwrap

# ── Lecture content ──────────────────────────────────────────────────────────

LECTURES = {
    "TQM_Lecture.pdf": [
        # (page_title, body_text)
        (
            "Total Quality Management — Introduction",
            textwrap.dedent("""\
            Total Quality Management (TQM) is a management approach that aims for
            long-term success through customer satisfaction.  TQM is based on the
            participation of all members of an organization in improving processes,
            products, services, and the culture in which they work.

            Key idea: quality is everyone's responsibility, not just the quality
            department's.

            TQM originated from the work of W. Edwards Deming and Joseph Juran in
            post-war Japan and was later adopted worldwide.
            """),
        ),
        (
            "Principles of TQM",
            textwrap.dedent("""\
            The main principles of Total Quality Management are:

            1. Customer Focus — understanding and meeting customer needs is the
               primary goal.
            2. Total Employee Involvement — every employee participates in working
               toward common goals.
            3. Process-Centered Thinking — a fundamental part of TQM is a focus on
               process thinking and continuous improvement.
            4. Integrated System — all departments and functions must be
               interconnected with horizontal processes.
            5. Strategic and Systematic Approach — a strategic plan must integrate
               quality as a core component.
            6. Continual Improvement — a major thrust of TQM is continuous process
               improvement, often using PDCA (Plan-Do-Check-Act).
            7. Fact-Based Decision Making — decisions are based on data analysis,
               not opinions.
            8. Communication — effective communication ensures morale and
               motivation at all levels.
            """),
        ),
        (
            "TQM Tools and Techniques",
            textwrap.dedent("""\
            Common tools used in TQM include:

            - Pareto Charts: identify the most significant factors in a data set.
            - Cause-and-Effect (Fishbone) Diagrams: visualize potential causes of
              a problem organized by category.
            - Control Charts: monitor process stability over time.
            - Histograms: display frequency distribution of data.
            - Scatter Diagrams: show correlation between variables.
            - Flowcharts: map out a process step by step.
            - Check Sheets: structured forms for collecting and analyzing data.

            These are sometimes called the "Seven Basic Tools of Quality".
            """),
        ),
    ],

    "Manufacturing_Processes.pdf": [
        (
            "Manufacturing Processes — Overview",
            textwrap.dedent("""\
            Manufacturing is the process of converting raw materials into finished
            products through various techniques.  The choice of manufacturing
            process depends on the material, part geometry, production volume,
            required tolerances, and cost constraints.

            Major categories of manufacturing processes:
            - Casting and Molding
            - Forming and Shaping (forging, rolling, extrusion)
            - Machining (turning, milling, drilling)
            - Joining (welding, brazing, soldering)
            - Additive Manufacturing (3D printing)
            """),
        ),
        (
            "Casting Processes",
            textwrap.dedent("""\
            Casting is one of the oldest manufacturing processes.  Molten metal is
            poured into a mold cavity and allowed to solidify into the desired shape.

            Types of casting:
            - Sand Casting: uses a sand mold; suitable for large parts and low
              production volumes.
            - Die Casting: uses a metal mold under high pressure; ideal for high
              volume production of non-ferrous metals.
            - Investment Casting (Lost Wax): produces parts with excellent surface
              finish and dimensional accuracy.

            Advantages: complex shapes, large parts, wide range of alloys.
            Disadvantages: porosity defects, limited dimensional accuracy (in sand
            casting), high tooling cost (in die casting).
            """),
        ),
        (
            "Forging and Machining",
            textwrap.dedent("""\
            Forging is a forming process in which compressive forces are applied to
            a workpiece to shape it.  Forging improves the grain structure of the
            metal, resulting in superior mechanical properties compared to casting.

            - Open-Die Forging: the workpiece is compressed between flat dies.
            - Closed-Die (Impression) Forging: the workpiece is shaped within a
              die cavity; better dimensional accuracy.

            Machining removes material from a workpiece using cutting tools.
            Common operations:
            - Turning (lathe): produces cylindrical parts.
            - Milling: uses a rotating cutter to remove material.
            - Drilling: creates holes.

            Machining offers excellent dimensional accuracy and surface finish but
            generates waste material (chips).
            """),
        ),
    ],

    "Operations_Research.pdf": [
        (
            "Operations Research — Fundamentals",
            textwrap.dedent("""\
            Operations Research (OR) is the discipline of applying advanced
            analytical methods to help make better decisions.  OR uses mathematical
            modeling, statistics, and optimization to arrive at optimal or
            near-optimal solutions.

            Common OR techniques:
            - Linear Programming (LP)
            - Integer Programming
            - Network Models (shortest path, max flow)
            - Queuing Theory
            - Simulation
            - Decision Analysis
            """),
        ),
        (
            "Linear Programming",
            textwrap.dedent("""\
            Linear Programming (LP) is a mathematical technique for optimizing a
            linear objective function subject to linear equality and inequality
            constraints.

            Standard form:
              Maximize   c^T x
              Subject to Ax <= b,  x >= 0

            Key concepts:
            - Decision Variables: quantities to be determined.
            - Objective Function: the function to maximize or minimize.
            - Constraints: limitations or requirements expressed as inequalities.
            - Feasible Region: the set of all points satisfying constraints.
            - Optimal Solution: the point in the feasible region that gives the
              best objective value.

            The Simplex Method (Dantzig, 1947) is the classic algorithm for solving
            LP problems.  It iterates through vertices of the feasible region.
            """),
        ),
        (
            "Transportation and Assignment Problems",
            textwrap.dedent("""\
            The Transportation Problem is a special type of LP concerned with
            shipping goods from multiple sources to multiple destinations at
            minimum cost.

            Methods for finding an initial basic feasible solution:
            - North-West Corner Method
            - Least Cost Method
            - Vogel's Approximation Method (VAM)

            The Assignment Problem is a special case of the transportation problem
            where each source supplies exactly one unit and each destination
            demands exactly one unit.  The Hungarian Method is the standard
            algorithm for solving assignment problems optimally.
            """),
        ),
    ],
}

# ── PDF generation ───────────────────────────────────────────────────────────

def generate_pdfs():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
    except ImportError:
        print("reportlab is not installed.  Install it first:")
        print("  pip install reportlab")
        return

    out_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    os.makedirs(out_dir, exist_ok=True)

    for filename, pages in LECTURES.items():
        filepath = os.path.join(out_dir, filename)
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4

        for page_idx, (title, body) in enumerate(pages):
            # Title
            c.setFont("Helvetica-Bold", 18)
            c.drawString(2 * cm, height - 3 * cm, title)

            # Body text (simple line wrapping)
            c.setFont("Helvetica", 11)
            text_obj = c.beginText(2 * cm, height - 4.5 * cm)
            text_obj.setLeading(16)
            for line in body.split("\n"):
                # Wrap long lines
                while len(line) > 90:
                    text_obj.textLine(line[:90])
                    line = line[90:]
                text_obj.textLine(line)
            c.drawText(text_obj)

            # Page number
            c.setFont("Helvetica", 9)
            c.drawRightString(width - 2 * cm, 1.5 * cm, f"Page {page_idx + 1}")

            c.showPage()

        c.save()
        print(f"  [OK] Created {filepath}")


if __name__ == "__main__":
    print("Generating sample lecture PDFs…")
    generate_pdfs()
    print("Done!")
