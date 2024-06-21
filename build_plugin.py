from pathlib import Path

import argparse

from agent_plugin_builder import build_agent_plugin


def main():
    parser = argparse.ArgumentParser(description="Build plugin")
    parser.add_argument("plugin_path", metavar="PLUGIN_PATH", type=str, help="Path to the plugin)")
    args = parser.parse_args()

    plugin_path = Path(args.plugin_path)
    if not plugin_path.exists():
        raise FileNotFoundError(f"Plugin path {plugin_path} does not exist")

    build_agent_plugin(plugin_path)


if __name__ == "__main__":
    main()
