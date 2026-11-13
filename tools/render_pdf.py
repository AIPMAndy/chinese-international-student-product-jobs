#!/usr/bin/env python3
"""Compatibility entry point for the browser-free ReportLab book renderer.

All command-line options are handled by render_pdf_reportlab.py. Prototype
screenshots are supplied as reviewed assets; building a PDF never launches a
browser or changes the source content.
"""
from render_pdf_reportlab import main

if __name__ == "__main__":
    main()
