import json
import os
from pathlib import Path
from typing import Any, Dict
import urllib.request

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.errors import ExtensionError

__version__ = '1.0.0'

def load_versions_config(app: Sphinx) -> Dict[str, Any]:
    """Load versions configuration from either local file or remote URL."""
    config = app.config
    
    try:
        # Load from remote URL if configured for remote
        if config.versions_source.lower() == 'remote':
            if not hasattr(config, 'versions_remote_url'):
                raise ExtensionError("versions_remote_url must be set when versions_source is 'remote'")
            with urllib.request.urlopen(config.versions_remote_url) as response:
                return json.loads(response.read())
        else:
            # Get absolute path relative to conf.py file
            local_path = Path(app.confdir) / config.versions_local_path
            with open(local_path) as f:
                return json.load(f)
    except Exception as e:
        if config.versions_raise_on_error:
            raise ExtensionError(f"Failed to load versions configuration: {e}")
        
        app.warn(f"Could not load versions configuration: {e}")
        # Return a minimal default configuration
        return {
            "versions": [
                {
                    "name": "latest",
                    "branch": "main",
                    "is_default": True
                }
            ]
        }

def update_context(app: Sphinx, pagename: str, templatename: str, context: Dict, doctree: Any) -> None:
    """Update the HTML context with version information."""
    context['versions'] = app.config.versions_config['versions']
    context['current_version'] = os.getenv('SPHINX_VERSION', 'latest')

def setup(app: Sphinx) -> Dict[str, Any]:
    """Setup the extension."""
    # Add configuration values
    app.add_config_value('versions_source', 'local', 'env')
    app.add_config_value('versions_local_path', '../versions.json', 'env')
    app.add_config_value('versions_remote_url', None, 'env')  # Now optional
    app.add_config_value('versions_raise_on_error', False, 'env')
    
    # Connect events
    app.connect('config-inited', lambda app, config: setattr(config, 'versions_config', 
                                                            load_versions_config(app)))
    app.connect('html-page-context', update_context)
    
    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }