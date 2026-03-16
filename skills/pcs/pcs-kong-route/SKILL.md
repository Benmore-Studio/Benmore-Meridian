---
name: pcs-kong-route
description: Use when adding or modifying Kong Gateway routes for PCS microservices - covers declarative YAML config, service definitions, route paths, strip_path behavior, health checks, JWT bypass, and plugin configuration
context: fork
---

# PCS: Kong Gateway Route

Add or modify Kong declarative routes for PCS microservices.

## Config Location

`kong/kong.yml` (format version 3.0, DB-less mode)

## Service Template

```yaml
  - name: {service-name}
    url: http://{service-name}:{port}
    connect_timeout: 30000
    write_timeout: 30000
    read_timeout: 30000
    healthchecks:
      active:
        healthy:
          interval: 30
          successes: 2
        unhealthy:
          interval: 10
          http_failures: 3
        http_path: /health
        timeout: 5
    routes:
      - name: {service}-routes
        paths:
          - "/api/v1/{resource}"
        strip_path: false
        protocols: ["http", "https"]
```

## Port Map

| Port | Service |
|------|---------|
| 8001 | auth-service |
| 8002 | organization-service |
| 8003 | tazworks-service |
| 8004 | tazworks-mcp |
| 8005 | background-service |
| 8007 | product-service |
| 8008 | order-service |
| 8009 | api-gateway (BFF) |

## strip_path Behavior

| `strip_path` | Client sends | Upstream receives |
|---|---|---|
| `false` (default) | `/api/v1/orders` | `/api/v1/orders` |
| `true` | `/api/v1/screening/orders` | `/orders` (prefix stripped) |

Use `strip_path: true` only when upstream URL already includes a path prefix (e.g., `url: http://service:8005/api/v1`).

## JWT Bypass (Anonymous Access)

For routes that must skip JWT validation (webhooks, health, MCP):

```yaml
    routes:
      - name: webhook-routes
        paths:
          - "/webhooks"
        strip_path: false
        protocols: ["http", "https"]
        plugins:
          - name: jwt
            config:
              anonymous: "anonymous-consumer"
```

## Global Plugins (already configured)

| Plugin | Purpose |
|--------|---------|
| `cors` | Allow frontend origins (localhost:3000, :5173) |
| `rate-limiting` | 10/sec, 600/min |
| `response-transformer` | Security headers (HSTS, X-Frame-Options, etc.) |
| `correlation-id` | X-Request-ID generation |
| `jwt` | Token validation + claim extraction |
| `pre-function` | Extract JWT claims to X-User-Id, X-Org-Id, X-Roles, X-Permissions headers |

## Special Patterns

### Namespaced routes with prefix stripping

When two services share similar paths, namespace one:

```yaml
  - name: background-service
    url: http://background-service:8005/api/v1    # Upstream includes /api/v1
    routes:
      - name: screening-routes
        paths:
          - "/api/v1/screening"
        strip_path: true    # Strips /api/v1/screening, upstream gets /orders etc.
```

### BFF aggregation routes

BFF is NOT a proxy. Only routes for composite/dashboard endpoints:

```yaml
  - name: api-gateway
    url: http://api-gateway:8009
    routes:
      - name: bff-routes
        paths:
          - "/api/v1/dashboard"
          - "/api/v1/aggregate"
        strip_path: false
```

### Long-timeout services (MCP, SSE)

```yaml
  - name: tazworks-mcp
    url: http://tazworks-mcp:8004
    write_timeout: 300000     # 5 minutes for SSE
    read_timeout: 300000
```

## Checklist

1. [ ] Service name matches Docker service name
2. [ ] Port matches service's actual port
3. [ ] Health check path exists on the service (`GET /health`)
4. [ ] Routes don't conflict with existing paths
5. [ ] `strip_path` matches upstream URL structure
6. [ ] JWT bypass added if route is unauthenticated
7. [ ] Timeouts appropriate for use case (default 30s, SSE up to 5min)
8. [ ] docker-compose.yml updated with service block
9. [ ] Route tested: `curl -i http://localhost:8080/api/v1/{resource}`

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Path conflict with existing service | Namespace under unique prefix |
| `strip_path: true` but upstream expects full path | Set `strip_path: false` or adjust upstream URL |
| Missing health check endpoint | Add `GET /health` route in service |
| Forgot JWT bypass on webhook | Add `anonymous: "anonymous-consumer"` plugin |
| Wrong port in `url` | Check Port Map table above |
