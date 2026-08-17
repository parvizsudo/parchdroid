"""
Path resolution helpers for Parchdroid
"""
import os
from pathlib import Path

# Paths
SRC_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = SRC_DIR.parent

def get_data_dir() -> Path:
    """Get the data directory containing UI, icons, and locales."""
    # Check development directory first
    dev_data = BASE_DIR / "data"
    if dev_data.exists() and (dev_data / "ui").exists():
        return dev_data
    
    # Check system-wide install paths
    for path in [
        Path("/usr/share/parchdroid"),
        Path("/usr/local/share/parchdroid"),
    ]:
        if path.exists():
            return path
            
    return dev_data

def get_ui_path(filename: str) -> str:
    """Get the full path to a .ui file."""
    data_dir = get_data_dir()
    ui_path = data_dir / "ui" / filename
    if ui_path.exists():
        return str(ui_path)
    
    # Fallback to src/ui/templates if present
    alt_path = SRC_DIR / "ui" / "templates" / filename
    if alt_path.exists():
        return str(alt_path)
        
    return str(ui_path)

def get_locale_dir() -> str:
    """Get the gettext locale directory."""
    dev_locale = BASE_DIR / "data" / "locale"
    if dev_locale.exists():
        return str(dev_locale)
    return "/usr/share/locale"
