# /Users/rd/deemon/deemon/plugins/__init__.py
from pathlib import Path
import importlib.util
import logging

logger = logging.getLogger(__name__)

class Plugin:
    def __init__(self):
        pass

    def setup(self):
        pass

    def parseLink(self, link):
        pass

    def generateDownloadObject(self, dz, link, bitrate, listener):
        pass

_plugins = []

def load_plugins():
    global _plugins
    plugins_dir = Path(__file__).parent
    
    if not plugins_dir.exists():
        logger.debug("Plugins directory does not exist")
        return
    
    for plugin_file in plugins_dir.glob("*.py"):
        if plugin_file.name == "__init__.py":
            continue
        
        try:
            spec = importlib.util.spec_from_file_location(
                f"deemon.plugins.{plugin_file.stem}", 
                plugin_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                        try:
                            plugin_instance = attr()
                            if hasattr(plugin_instance, 'setup'):
                                plugin_instance.setup()
                            _plugins.append(plugin_instance)
                            logger.info(f"Loaded plugin: {attr_name}")
                        except Exception as e:
                            logger.error(f"Failed to initialize plugin {attr_name}: {e}")
        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_file.name}: {e}")

def get_plugins():
    return _plugins