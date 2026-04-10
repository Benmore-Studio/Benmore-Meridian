---
name: doctl-cli
description: Manage DigitalOcean Droplets, databases, domains, and infrastructure from the command line using doctl
context: fork
---

# DigitalOcean CLI (doctl) Skill

`doctl` is the official DigitalOcean CLI for managing Droplets, databases, domains, firewalls, and all DO resources. Use `doctl <command> --help` for full flag details on any command.

## Installation & Authentication

```bash
# Install via Homebrew
brew install doctl

# Authenticate (prompts for PAT)
doctl auth init

# Authenticate with named context (multiple accounts)
doctl auth init --context benmore

# Verify authentication
doctl account get

# Switch between accounts
doctl auth list
doctl auth switch --context benmore
```

**Authentication requires a Personal Access Token (PAT):**
1. Go to https://cloud.digitalocean.com/account/api/tokens
2. Click "Generate New Token"
3. Select scopes (Custom Scopes recommended for least-privilege)
4. Save the token — it's only shown once
5. Store in environment: `export DO_API_TOKEN="your-token"`

**Token scopes cannot be edited after creation.** Create a new token if you need different scopes.

## Configuration

Config file location: `~/Library/Application Support/doctl/config.yaml` (macOS)

```yaml
# Example config.yaml
access-token: dop_v1_your_token_here
output: json
context: default
```

```bash
# Override config file location
doctl --config /path/to/config.yaml compute droplet list

# Override API endpoint (self-hosted/testing)
doctl --api-url https://api.custom.endpoint/v2 compute droplet list

# Output formats
doctl compute droplet list -o json    # JSON output
doctl compute droplet list -o text    # Default text table

# Enable verbose/debug output
doctl compute droplet list -v         # Verbose
doctl compute droplet list --trace    # Full HTTP trace
```

**Environment variables:**

| Variable | Purpose |
|----------|---------|
| `DIGITALOCEAN_ACCESS_TOKEN` | Auth token (alternative to config) |
| `DIGITALOCEAN_CONTEXT` | Named auth context to use |
| `DIGITALOCEAN_API_URL` | Override API endpoint |

## Droplet Management

```bash
# List all Droplets
doctl compute droplet list
doctl compute droplet list --format ID,Name,PublicIPv4,Status,Region

# Get specific Droplet info
doctl compute droplet get <droplet-id>

# Create a Droplet
doctl compute droplet create my-droplet \
  --region nyc3 \
  --image ubuntu-24-04-x64 \
  --size s-1vcpu-1gb \
  --ssh-keys <fingerprint>

# Delete a Droplet (destructive!)
doctl compute droplet delete <droplet-id>

# SSH into a Droplet (auto-resolves IP)
doctl compute ssh <droplet-id>
doctl compute ssh <droplet-name>
```

## Droplet Actions

```bash
# Power on/off/cycle
doctl compute droplet-action power-on <droplet-id>
doctl compute droplet-action power-off <droplet-id>
doctl compute droplet-action power-cycle <droplet-id>

# Reboot (graceful)
doctl compute droplet-action reboot <droplet-id>

# Resize
doctl compute droplet-action resize <droplet-id> --size s-2vcpu-2gb

# Create snapshot
doctl compute droplet-action snapshot <droplet-id> --snapshot-name "my-snapshot"

# List actions history
doctl compute droplet-action list <droplet-id>
```

## Databases

```bash
# List database clusters
doctl databases list

# Get database info
doctl databases get <database-id>

# List databases in a cluster
doctl databases db list <database-id>

# List database users
doctl databases user list <database-id>

# Create a database
doctl databases db create <database-id> <db-name>

# Manage connection pools
doctl databases pool list <database-id>

# Manage firewall rules
doctl databases firewalls list <database-id>
doctl databases firewalls replace <database-id> --rules droplet:<droplet-id>
```

## Domains & DNS

```bash
# List domains
doctl compute domain list

# Create a domain
doctl compute domain create example.com --ip-address 159.203.174.239

# List DNS records
doctl compute domain records list example.com

# Create DNS record
doctl compute domain records create example.com \
  --record-type A \
  --record-name www \
  --record-data 159.203.174.239 \
  --record-ttl 300

# Delete DNS record
doctl compute domain records delete example.com <record-id>
```

## Firewalls

```bash
# List firewalls
doctl compute firewall list

# Create firewall
doctl compute firewall create \
  --name my-firewall \
  --inbound-rules "protocol:tcp,ports:22,address:0.0.0.0/0 protocol:tcp,ports:80,address:0.0.0.0/0 protocol:tcp,ports:443,address:0.0.0.0/0" \
  --outbound-rules "protocol:tcp,ports:all,address:0.0.0.0/0" \
  --droplet-ids <droplet-id>

# Add Droplets to firewall
doctl compute firewall add-droplets <firewall-id> --droplet-ids "<id1>,<id2>"
```

## Networking

```bash
# List VPCs
doctl vpcs list

# List reserved IPs
doctl compute reserved-ip list

# Assign reserved IP to Droplet
doctl compute reserved-ip-action assign <ip> <droplet-id>

# List load balancers
doctl compute load-balancer list
```

## Snapshots & Images

```bash
# List snapshots
doctl compute snapshot list

# List images (including custom)
doctl compute image list
doctl compute image list --public

# Delete snapshot
doctl compute snapshot delete <snapshot-id>
```

## Apps (App Platform)

```bash
# List apps
doctl apps list

# Create app from spec
doctl apps create --spec .do/app.yaml

# Get app info
doctl apps get <app-id>

# List deployments
doctl apps list-deployments <app-id>

# View logs
doctl apps logs <app-id>
doctl apps logs <app-id> --type build
doctl apps logs <app-id> --type run
```

## Kubernetes

```bash
# List clusters
doctl kubernetes cluster list

# Save kubeconfig
doctl kubernetes cluster kubeconfig save <cluster-id>

# List node pools
doctl kubernetes cluster node-pool list <cluster-id>
```

## Monitoring & Billing

```bash
# Account balance
doctl balance get

# Billing history
doctl billing-history list

# Invoices
doctl invoice list
doctl invoice get <invoice-id>

# Monitoring alerts
doctl monitoring alert list
```

## Spaces (S3-compatible Object Storage)

```bash
# List Spaces
doctl spaces list

# Create Space
doctl spaces create my-space --region nyc3
```

## SSH Keys

```bash
# List SSH keys
doctl compute ssh-key list

# Add SSH key
doctl compute ssh-key create my-key --public-key "$(cat ~/.ssh/id_ed25519.pub)"

# Delete SSH key
doctl compute ssh-key delete <key-id>
```

## Metadata API (From Inside a Droplet)

No authentication needed — only accessible from within the Droplet itself via link-local address:

```bash
# Full metadata JSON
curl -s http://169.254.169.254/metadata/v1.json | jq .

# Individual fields
curl -s http://169.254.169.254/metadata/v1/hostname
curl -s http://169.254.169.254/metadata/v1/region
curl -s http://169.254.169.254/metadata/v1/id
curl -s http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address
curl -s http://169.254.169.254/metadata/v1/interfaces/private/0/ipv4/address
```

## Output Formatting

```bash
# JSON output (useful for scripts)
doctl compute droplet list -o json

# Custom columns
doctl compute droplet list --format ID,Name,PublicIPv4,Status,Region

# Verbose mode
doctl compute droplet list -v
```

## Common OAuth Scopes for PATs

| Scope | Permission |
|-------|-----------|
| `droplet:read` | View Droplet info |
| `droplet:create` | Create Droplets |
| `droplet:update` | Power on/off, resize, rename |
| `droplet:delete` | Destroy Droplets |
| `database:read` | View managed databases |
| `database:update` | Modify databases |
| `domain:read` | View DNS records |
| `domain:update` | Manage DNS records |
| `ssh_key:read` | List SSH keys |
| `account:read` | View account info |
| `firewall:read` | View firewalls |
| `firewall:update` | Modify firewall rules |

**Principle of least privilege:** Only grant the scopes your workflow needs. Scopes are immutable after token creation.

## Troubleshooting

```bash
# Check auth status
doctl account get

# Debug API calls
doctl compute droplet list --trace

# Check doctl version
doctl version

# Update doctl
brew upgrade doctl
```
