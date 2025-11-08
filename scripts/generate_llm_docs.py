#!/usr/bin/env python3
"""
Generate a single consolidated markdown file for LLM consumption.

This script combines CONTEXT.md, ARCHITECTURE.md, and API_REFERENCE.md
into a single downloadable file optimized for feeding to LLMs.
"""

from pathlib import Path


def generate_llm_documentation():
    """Combine all LLM documentation files into a single markdown file."""
    
    # Define source files
    root = Path(__file__).parent.parent
    context_file = root / "docs" / "llm_oriented" / "context.md"
    architecture_file = root / "docs" / "llm_oriented" / "architecture.md"
    api_file = root / "docs" / "llm_oriented" / "api_reference.md"
    output_file = root / "docs" / "llm_oriented" / "llm_documentation.md"

    # Get the version from the project file
    project_file = root / "pyproject.toml"
    version = project_file.read_text(encoding="utf-8").split("version = ")[1].split("\n")[0].strip()
    
    # Read all files
    context = context_file.read_text(encoding="utf-8")
    architecture = architecture_file.read_text(encoding="utf-8")
    api_ref = api_file.read_text(encoding="utf-8")
    
    # Combine with clear separators
    combined = f"""# CogStim – Complete LLM Documentation

**Single-file documentation optimized for Large Language Model consumption.**

This document combines all technical documentation for the CogStim repository:
1. **Context & Overview** - Quick start and core concepts
2. **Architecture** - System design and patterns
3. **API Reference** - Complete class and method documentation

**Version**: {version}  
**Last Updated**: Auto-generated  
**Repository**: https://github.com/eudald-seeslab/cogstim

---

{context}

---

{architecture}

---

{api_ref}
"""
    
    # Write combined file
    output_file.write_text(combined, encoding="utf-8")
    
    # Report size
    size_kb = len(combined.encode('utf-8')) / 1024
    lines = combined.count('\n')
    
    print(f"✓ Generated: {output_file}")
    print(f"  Size: {size_kb:.1f} KB")
    print(f"  Lines: {lines:,}")
    print(f"\nThis file can be directly uploaded to LLMs for context.")


if __name__ == "__main__":
    generate_llm_documentation()

