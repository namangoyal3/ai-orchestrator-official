"""
Activate API — provision or configure a tool from the Namango catalog.

POST /v1/tools/{slug}/activate

Given a tool slug, returns everything needed to immediately use that tool:
  - install commands to run
  - env vars to set (with signup URL if API key needed)
  - Docker/deploy commands for self-hosted tools
  - MCP editor config snippets for MCP-type tools
  - One-click deploy URLs where available

execution_type routing:
  install       → returns install_cmd + docs_url
  api           → returns signup_url + env_vars + install_cmd
  self-host     → returns deploy_cmd + optional deploy_url (Railway template)
  hosted        → returns signup_url + deploy_url
  mcp           → returns editor_config snippets for Claude/Cursor/Windsurf
  recommend-only → returns docs_url only (no activation path)

Data flow:
  slug → find_tool() → execution_type → _build_next_steps() → ActivateResponse
    │                        │
    404 if not found         └─ recommend-only if missing (safe default)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.api.catalog_utils import find_tool

router = APIRouter(prefix="/v1/tools", tags=["Activate"])

# NOTE: GET /v1/tools/activation-types is registered here BEFORE /{slug}/activate
# so FastAPI doesn't capture "activation-types" as a slug parameter.
# The tools.py router also has GET /v1/tools/{slug} — static routes win over
# parameterized ones only within the same router, so we keep this endpoint
# on a distinct path prefix via the summary tag, not the path itself.
# Both routers share /v1/tools prefix — activation-types is safe because
# tools.py's /{slug} only matches TOOL_REGISTRY keys and returns 404 otherwise.


class ActivateResponse(BaseModel):
    slug: str
    name: str
    execution_type: str
    # install
    install_cmd: Optional[str] = None
    # api
    signup_url: Optional[str] = None
    env_vars: Optional[list[str]] = None
    # self-host / hosted
    deploy_cmd: Optional[str] = None
    deploy_url: Optional[str] = None
    # mcp
    editor_config: Optional[dict] = None
    mcp_server_url: Optional[str] = None
    # always present
    docs_url: Optional[str] = None
    github_url: Optional[str] = None
    # human-readable next steps
    next_steps: list[str]


def _build_next_steps(tool_name: str, tool_slug: str, cfg: dict, exec_type: str) -> list[str]:
    """Build ordered list of human-readable next steps for activating this tool."""
    steps = []

    if exec_type == "install":
        if cfg.get("install_cmd"):
            steps.append(f"Run: `{cfg['install_cmd']}`")
        if cfg.get("docs_url"):
            steps.append(f"Read the docs: {cfg['docs_url']}")

    elif exec_type == "api":
        if cfg.get("signup_url"):
            steps.append(f"Sign up and get your API key: {cfg['signup_url']}")
        if cfg.get("env_vars"):
            steps.append(f"Add to your .env: {', '.join(cfg['env_vars'])}")
        if cfg.get("install_cmd"):
            steps.append(f"Install the SDK: `{cfg['install_cmd']}`")

    elif exec_type == "self-host":
        if cfg.get("deploy_url"):
            steps.append(f"One-click deploy to Railway: {cfg['deploy_url']}")
        if cfg.get("deploy_cmd"):
            steps.append(f"Or self-host with Docker: `{cfg['deploy_cmd']}`")
        if cfg.get("github_url"):
            steps.append(f"Source: {cfg['github_url']}")

    elif exec_type == "hosted":
        if cfg.get("signup_url"):
            steps.append(f"Sign up: {cfg['signup_url']}")
        if cfg.get("deploy_url"):
            steps.append(f"Deploy your project: {cfg['deploy_url']}")
        if cfg.get("install_cmd"):
            steps.append(f"Install CLI: `{cfg['install_cmd']}`")

    elif exec_type == "mcp":
        if cfg.get("install_cmd"):
            steps.append(f"Install the MCP server: `{cfg['install_cmd']}`")
        editor_cfg = cfg.get("editor_config", {})
        if editor_cfg.get("claude"):
            claude_cmd = editor_cfg["claude"].get("command", "")
            steps.append(f"Add to Claude Code: `claude mcp add {tool_slug} --command {claude_cmd}`")
        if editor_cfg.get("cursor"):
            steps.append("Add to Cursor: Settings → MCP → paste the server config")

    elif exec_type == "recommend-only":
        if cfg.get("docs_url"):
            steps.append(f"Learn more: {cfg['docs_url']}")
        if cfg.get("github_url"):
            steps.append(f"GitHub: {cfg['github_url']}")

    return steps


@router.get("/activation-types", summary="List all execution types and what they mean")
async def activation_types():
    """Returns the execution_type taxonomy used across the catalog."""
    return {
        "types": {
            "install": "npm/pip/brew install locally — returns install_cmd",
            "api": "Managed SaaS — returns signup_url + env_vars + install_cmd",
            "self-host": "Docker/compose self-hosted — returns deploy_cmd + optional Railway URL",
            "hosted": "Deploy your code to a platform — returns signup_url + deploy_url",
            "mcp": "MCP server — returns editor_config for Claude/Cursor/Windsurf",
            "recommend-only": "No automated activation path yet — returns docs link only",
        }
    }


@router.post("/{slug}/activate", response_model=ActivateResponse, summary="Activate a tool from the catalog")
async def activate_tool(slug: str):
    """
    Returns everything needed to immediately start using a tool from the Namango catalog.

    - **install** tools: returns the install command and docs
    - **api** tools: returns signup URL, env var names, and SDK install command
    - **self-host** tools: returns Docker command and/or Railway one-click deploy URL
    - **hosted** tools: returns the platform signup + deploy URL
    - **mcp** tools: returns editor config snippets for Claude Code, Cursor, Windsurf
    - **recommend-only** tools: returns docs link (no automated activation path yet)
    """
    tool = find_tool(slug)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{slug}' not found in catalog")

    exec_type = tool.get("execution_type", "recommend-only")
    cfg = tool.get("execution_config", {})
    tool_name = tool.get("name", slug)
    tool_slug = tool.get("slug", slug)

    next_steps = _build_next_steps(tool_name, tool_slug, cfg, exec_type)

    return ActivateResponse(
        slug=tool_slug,
        name=tool_name,
        execution_type=exec_type,
        install_cmd=cfg.get("install_cmd"),
        signup_url=cfg.get("signup_url"),
        env_vars=cfg.get("env_vars"),
        deploy_cmd=cfg.get("deploy_cmd"),
        deploy_url=cfg.get("deploy_url"),
        editor_config=cfg.get("editor_config"),
        mcp_server_url=cfg.get("mcp_server_url"),
        docs_url=cfg.get("docs_url"),
        github_url=cfg.get("github_url") or tool.get("github_url"),
        next_steps=next_steps,
    )
