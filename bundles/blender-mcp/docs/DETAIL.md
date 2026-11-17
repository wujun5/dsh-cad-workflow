# Blender MCP bridge

Connects this DSH profile to the Blender MCP server (`mcp-for-blender`, a third-party community plugin).

## What it provides
- `mcp__blender__execute_blender_code`: run Python inside the running Blender.
- `mcp__blender__look`: capture viewport/camera/rendered views to verify geometry.
- `mcp__blender__get_scene_info`: inspect objects, materials and topology.
- `mcp__blender__get_addon_status`, `search_assets`, `import_asset`, and optional AI generators.

## Prerequisites (one-time, manual)
1. In Blender: **Edit → Preferences → Add-ons → enable "Interface: MCP for Blender"** (the addon was installed to `C:\\Users\\Tim\\AppData\\Roaming\\Blender Foundation\\Blender\\5.3\\scripts\\addons\\blender_mcp.py`). Restart Blender if it does not appear.
2. In Blender's 3D viewport press **N** → **MCP for Blender** tab → **Start MCP Server** (default `localhost:9876`).
3. Fully quit and relaunch DSH so it starts the MCP client.

## Notes
- Only one MCP server instance should run. The server speaks stdio to DSH and TCP to the Blender addon.
- `execute_blender_code` runs arbitrary Python; save your work before using it.
- Safe mode can be enabled by setting env `BLENDER_MCP_SAFE_MODE=1` in the patch.
- See `D:\\Tim\\AIRoom\\Works-3D\\_cad_workflow\\README.md` for the full workflow and the headless fallback.
