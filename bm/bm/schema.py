"""JSON Schema and OpenAPI artifacts for public bm outputs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

JsonSchema = dict[str, Any]


def _array_schema(item_schema: JsonSchema) -> JsonSchema:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "array",
        "items": item_schema,
    }


_STRING = {"type": "string"}
_INTEGER = {"type": "integer"}
_NUMBER = {"type": "number"}
_BOOLEAN = {"type": "boolean"}

CLI_JSON_SCHEMAS: dict[str, JsonSchema] = {
    "status": _array_schema(
        {
            "type": "object",
            "required": ["name", "status", "scope", "project"],
            "additionalProperties": False,
            "properties": {
                "name": _STRING,
                "status": {"enum": ["symlinked", "copied", "missing", "broken"]},
                "scope": {"enum": ["general", "project"]},
                "project": _STRING,
            },
        }
    ),
    "skill-list": _array_schema(
        {
            "type": "object",
            "required": ["name", "scope", "project", "path"],
            "additionalProperties": False,
            "properties": {
                "name": _STRING,
                "scope": {"enum": ["general", "project"]},
                "project": _STRING,
                "path": _STRING,
            },
        }
    ),
    "registry-list": _array_schema(
        {
            "type": "object",
            "required": [
                "name",
                "installed_path",
                "source",
                "scope",
                "project",
                "version",
                "install_method",
            ],
            "additionalProperties": False,
            "properties": {
                "name": _STRING,
                "installed_path": _STRING,
                "source": {"enum": ["repo", "marketplace", "external"]},
                "scope": {"enum": ["general", "project"]},
                "project": _STRING,
                "version": _STRING,
                "install_method": {"enum": ["symlink", "copy", "external", "none"]},
            },
        }
    ),
    "prompt-list": _array_schema(
        {
            "type": "object",
            "required": [
                "name",
                "description",
                "tags",
                "scope",
                "project",
                "starred",
                "use_count",
            ],
            "additionalProperties": False,
            "properties": {
                "name": _STRING,
                "description": _STRING,
                "tags": {"type": "array", "items": _STRING},
                "scope": _STRING,
                "project": _STRING,
                "starred": _BOOLEAN,
                "use_count": _INTEGER,
            },
        }
    ),
    "suggest": _array_schema(
        {
            "type": "object",
            "required": ["name", "reason", "status", "score"],
            "additionalProperties": False,
            "properties": {
                "name": _STRING,
                "reason": _STRING,
                "status": _STRING,
                "score": _NUMBER,
            },
        }
    ),
    "debrief": _array_schema(
        {
            "type": "object",
            "required": ["name", "rationale", "score", "command"],
            "additionalProperties": False,
            "properties": {
                "name": _STRING,
                "rationale": _STRING,
                "score": _NUMBER,
                "command": _STRING,
            },
        }
    ),
}


BENMORE_JSON_SCHEMA_NAMES = [
    "benmore-projects",
    "benmore-channels",
    "benmore-context",
    "benmore-status",
    "benmore-team",
    "benmore-list",
    "benmore-overview",
    "benmore-lookup",
    "benmore-summary",
]

for schema_name in BENMORE_JSON_SCHEMA_NAMES:
    CLI_JSON_SCHEMAS[schema_name] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "description": (
            "Benmore API JSON output. The remote API is intentionally tolerant, so "
            "this schema preserves compatibility by accepting object or array payloads."
        ),
        "oneOf": [
            {"type": "object"},
            {"type": "array"},
        ],
    }


def get_cli_json_schema(name: str) -> JsonSchema:
    """Return a deep copy of a named CLI JSON Schema artifact."""
    try:
        return deepcopy(CLI_JSON_SCHEMAS[name])
    except KeyError as exc:
        choices = ", ".join(sorted(CLI_JSON_SCHEMAS))
        raise KeyError(f"Unknown schema {name!r}. Available schemas: {choices}") from exc


def build_benmore_openapi() -> dict[str, Any]:
    """Generate a compact OpenAPI document from benmore_client Pydantic models."""
    try:
        from benmore_client.models import (
            Channel,
            Document,
            GitHubBoard,
            Meeting,
            Project,
            ProjectContext,
            ProjectListResponse,
            ProjectStatus,
            TeamMember,
        )
        from pydantic import BaseModel
    except ImportError as exc:  # pragma: no cover - exercised by CLI error path.
        raise RuntimeError("benmore_client is required to generate OpenAPI") from exc

    models: list[type[BaseModel]] = [
        Channel,
        Document,
        GitHubBoard,
        Meeting,
        Project,
        ProjectContext,
        ProjectListResponse,
        ProjectStatus,
        TeamMember,
    ]
    schemas = {model.__name__: model.model_json_schema() for model in models}

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Benmore Client API",
            "version": "1.0.1",
            "description": "Generated from benmore_client Pydantic models.",
        },
        "servers": [{"url": "https://client.benmore.tech/api/v1"}],
        "paths": {
            "/projects/": {
                "get": {
                    "operationId": "projects_list",
                    "responses": {
                        "200": {
                            "description": "Paginated projects",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ProjectListResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/projects/search/": {
                "get": {
                    "operationId": "projects_search",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Search results",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ProjectListResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/projects/{project_id}/context/": {
                "get": {
                    "operationId": "projects_context",
                    "parameters": [_path_param("project_id")],
                    "responses": {
                        "200": {
                            "description": "Project context",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ProjectContext"}
                                }
                            },
                        }
                    },
                }
            },
            "/projects/{project_id}/status/": {
                "get": {
                    "operationId": "projects_status",
                    "parameters": [_path_param("project_id")],
                    "responses": {
                        "200": {
                            "description": "Project status",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ProjectStatus"}
                                }
                            },
                        }
                    },
                }
            },
            "/projects/{project_id}/team/": {
                "get": {
                    "operationId": "team_list",
                    "parameters": [_path_param("project_id")],
                    "responses": {
                        "200": {
                            "description": "Team members",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/TeamMember"},
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/projects/{project_id}/comms/": {
                "get": {
                    "operationId": "comms_raw",
                    "summary": "Slack channel metadata + linkage",
                    "description": (
                        "Returns Slack channel metadata/linkage for a project. "
                        "Use it to resolve a project to its channel ID. Client-channel "
                        "message *content* should be read via a Slack MCP/CLI integration, "
                        "not this endpoint; the API's stored copy (recent_messages) is a "
                        "fallback only and is deprecated for message retrieval."
                    ),
                    "parameters": [_path_param("project_id")],
                    "responses": {
                        "200": {
                            "description": "Slack communication payload (channel metadata)",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        }
                    },
                }
            },
        },
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-KEY",
                }
            },
            "schemas": schemas,
        },
        "security": [{"ApiKeyAuth": []}],
    }


def _path_param(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "in": "path",
        "required": True,
        "schema": {"type": "string"},
    }
