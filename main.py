#!/usr/bin/env python3
"""
JContext - LLM Context Generator
Main entry point for the application.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jcontext.gui import JContextGUI


def main():
    """Main function to run the JContext application."""
    try:
        app = JContextGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
