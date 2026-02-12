# Claude Code Sandboxing Setup

## 📋 Overview

Claude Code's open-source sandbox runtime improves security while reducing permission prompts through file and network isolation. This guide covers everything you need to enable and use sandboxing in your Claude Code environment.

| Aspect | Benefit |
|--------|---------|
| **Safety** | Code runs in isolated environment, not directly on your system |
| **Fewer Prompts** | Reduced permission dialogs for file/network access |
| **File Isolation** | Restricted access to specific directories |
| **Network Isolation** | Controlled network access with allowlist |
| **Local Execution** | Runs on your machine, not cloud infrastructure |

---

## What is Claude Code Sandboxing?

Claude Code's sandbox runtime is an **open-source execution environment** that isolates code execution from your host system while maintaining full Claude Code functionality.

### Key Concepts

**Sandbox Runtime**
- Open-source execution layer for Claude Code
- Runs code in a restricted, isolated environment
- Available on macOS and Linux (Windows support coming soon)
- Hosted locally on your machine

**Why Sandboxing Matters**
- **Security:** Code can't access files outside the sandbox without explicit permission
- **Permission Model:** Fewer prompts for common operations within the sandbox
- **Isolation:** Network calls are restricted to configured allowlist
- **Control:** You decide what the sandbox can access

**What Gets Isolated**
- File system access (restricted to designated directories)
- Network requests (require allowlist configuration)
- System resources (controlled allocation)
- Environment variables (selective exposure)

---

## Requirements

### Supported Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| **macOS** | ✅ Supported | Intel and Apple Silicon |
| **Linux** | ✅ Supported | Ubuntu, Debian, Fedora, etc. |
| **Windows** | 🚧 Coming Soon | Not yet supported |

### System Requirements

- **Disk Space:** ~500MB for sandbox runtime installation
- **Memory:** 2GB available RAM (recommended 4GB+)
- **CPU:** Any modern processor (Intel/AMD/Apple Silicon)
- **Network:** Internet access for initial download and MCP servers
- **Terminal:** Bash, Zsh, or compatible shell
- **Claude Code:** Version 1.24.0 or later

### Prerequisites

- Claude Code installed and configured
- Git (for repository management)
- Basic command-line familiarity
- Administrator access to install and configure sandbox

---

## Installation

### Quick Start (Recommended)

The fastest way to enable sandboxing is using the `/sandbox` command in Claude Code:

```bash
/sandbox
```

This command will:
1. Detect your platform (macOS/Linux)
2. Download the sandbox runtime
3. Extract and configure it
4. Add sandbox configuration to your Claude Code settings
5. Verify the installation

**Expected output:**
```
✅ Sandbox runtime installed
✅ Configuration created at ~/.claude/settings.json
✅ Sandbox ready to use
```

### Manual Setup

If the quick start doesn't work or you prefer manual configuration:

#### Step 1: Download Sandbox Runtime

```bash
# Create sandbox directory
mkdir -p ~/.claude/sandbox

# Download latest release (macOS/Linux)
LATEST=$(curl -s https://api.github.com/repos/anthropic-experimental/sandbox-runtime/releases/latest | grep -oP '"browser_download_url": "\K[^"]*sandbox-runtime[^"]*' | grep "$(uname -m)")
wget "$LATEST" -O ~/.claude/sandbox/runtime.tar.gz

# Extract
cd ~/.claude/sandbox
tar -xzf runtime.tar.gz
rm runtime.tar.gz
```

#### Step 2: Configure Claude Code Settings

Add sandbox configuration to `~/.claude/settings.json`:

```json
{
  "sandboxRuntime": {
    "enabled": true,
    "path": "~/.claude/sandbox/sandbox-runtime",
    "fileAccess": {
      "allowedDirs": [
        "~",
        "/tmp",
        "/var/tmp"
      ],
      "restrictedDirs": [
        "/etc",
        "/sys",
        "/proc",
        "/root",
        "/Users/*/Library/Passwords*"
      ]
    },
    "networkAccess": {
      "enabled": true,
      "allowlist": [
        "api.github.com",
        "registry.npmjs.org",
        "pypi.org",
        "github.com",
        "npm.js.org",
        "*.anthropic.com"
      ],
      "denylist": []
    }
  }
}
```

#### Step 3: Verify Installation

Test the sandbox is working:

```bash
# In Claude Code terminal
/sandbox status
```

Expected output:
```
Sandbox Runtime Status
  Status: ✅ Running
  Version: 1.0.0
  Platform: macOS (Apple Silicon)
  File Isolation: Enabled
  Network Isolation: Enabled
  Uptime: 0h 2m
```

---

## How It Works

### File Isolation Mechanism

The sandbox restricts file system access to designated directories:

```
Host System (Full Access)
    ↓
Sandbox Boundary
    ↓
Sandbox (Restricted Access)
  ├── Allowed: ~/Desktop, ~/Documents, ~/projects, /tmp
  ├── Restricted: /etc, /sys, /proc, ~/.ssh
  └── Denied: System files, passwords, credentials
```

**Rules:**
- By default, sandbox can only access your current project and `/tmp`
- Request explicit permission for files outside allowed directories
- Some directories (passwords, SSH keys) are always blocked
- Symlinks to restricted directories are blocked

### Network Isolation Capabilities

The sandbox controls outbound network requests:

```
Sandbox Process
    ↓
Network Request (DNS lookup, HTTP, HTTPS)
    ↓
Network Filter
    ├── Allowed: Hosts in allowlist
    ├── Blocked: Hosts in denylist
    └── Denied: Everything else
    ↓
Internet / Internal Network
```

**Default Allowlist:**
- `api.github.com` — GitHub REST API
- `registry.npmjs.org` — NPM package registry
- `pypi.org` — Python package index
- `github.com` — GitHub web interface
- `*.anthropic.com` — Anthropic services
- `localhost` — Local services

**Common Denied Requests:**
- Internal IP ranges (192.168.x.x, 10.0.0.0/8)
- Private DNS services
- Credential endpoints
- AWS/Azure metadata services

### Permission Model

When code attempts restricted operations:

1. **Allowed (No Prompt)**
   - Reading files in allowed directories
   - Network requests to allowlisted hosts
   - Writing to temp directories
   - Environment variable access (whitelisted)

2. **Restricted (Prompt)**
   - Accessing files outside allowed directories
   - Network requests to non-allowlisted hosts
   - Modifying system configuration
   - Installing system packages

3. **Blocked (Denied)**
   - Accessing SSH/GPG keys
   - Reading passwords/secrets
   - Modifying system files
   - Executing privileged commands (sudo)

---

## Configuration & Customization

### Extending Allowed Directories

To allow sandbox access to additional directories, update your settings:

```json
{
  "sandboxRuntime": {
    "fileAccess": {
      "allowedDirs": [
        "~",
        "/tmp",
        "/var/tmp",
        "~/Documents/client-projects",
        "~/work/internal-tools"
      ]
    }
  }
}
```

### Adding Network Allowlist Entries

To allow API calls to additional services:

```json
{
  "sandboxRuntime": {
    "networkAccess": {
      "allowlist": [
        "api.openai.com",
        "api.stripe.com",
        "supabase.co",
        "*.vercel.app",
        "localhost:3000",
        "localhost:8000"
      ]
    }
  }
}
```

### Disabling Sandbox (Temporarily)

To run a command without sandboxing:

```bash
# Option 1: Use /no-sandbox command in Claude Code
/no-sandbox

# Option 2: Edit settings to disable
{
  "sandboxRuntime": {
    "enabled": false
  }
}

# Option 3: Environment variable (override settings)
CLAUDE_SANDBOX_DISABLED=true /claude
```

### Per-Project Configuration

Create `.claude/sandbox.json` in your project root for project-specific settings:

```json
{
  "fileAccess": {
    "allowedDirs": [
      ".",
      "/tmp",
      "./data",
      "../shared-data"
    ]
  },
  "networkAccess": {
    "allowlist": [
      "internal-api.company.com",
      "*.localhosting.dev"
    ]
  },
  "environment": {
    "CI": "true",
    "NODE_ENV": "development"
  }
}
```

---

## Benefits & Use Cases

### Improved Security

**Benefit:** Code execution is isolated from your system.

**Use Cases:**
- Running untrusted scripts from tutorials or examples
- Executing code from open-source projects
- Testing code with unknown dependencies
- Experimenting with potentially dangerous operations

**Example:** Installing a package with unknown security history
```bash
# In sandbox: Limited damage if package contains malicious code
npm install potentially-dangerous-package

# Without sandbox: Could modify system files, steal credentials
```

### Reduced Permission Prompts

**Benefit:** Common operations no longer trigger permission dialogs.

**Comparison:**

| Operation | Without Sandbox | With Sandbox |
|-----------|-----------------|--------------|
| Reading project files | ✅ No prompt | ✅ No prompt |
| Writing to /tmp | ❌ Prompt | ✅ No prompt |
| Installing npm packages | ❌ Prompt | ✅ No prompt |
| Running tests | ❌ Prompt | ✅ No prompt |
| Accessing ~/.ssh | ❌ Prompt | ❌ Blocked |

### Development Workflow Improvements

**Faster iteration:** No permission dialogs slowing down work
```bash
# Without sandbox: Prompted for each file operation
npm test
# Prompt: Allow access to node_modules? [y/n]
# Prompt: Allow writing to ./coverage? [y/n]

# With sandbox: Runs immediately
npm test
```

**Cleaner logs:** Less noise from permission prompts
```bash
# Without sandbox
Warning: File access denied. Allow? [y/n]
Permission granted to ./src
Permission denied to ~/.ssh

# With sandbox
Running tests...
✅ All tests pass
```

### Team Security

**Benefit:** Standardized sandbox configuration across team.

**Scenario:** Onboarding new developer
```bash
# .claude/sandbox.json (checked into repo)
{
  "fileAccess": {
    "allowedDirs": [".", "./node_modules", "/tmp"]
  },
  "networkAccess": {
    "allowlist": ["registry.npmjs.org", "api.github.com"]
  }
}

# New developer installs project
git clone ...
/claude  # Auto-loads .claude/sandbox.json
# ✅ Sandbox automatically configured per team standards
```

---

## Limitations & Considerations

### Platform Support

**Current Status:**
- ✅ macOS: Full support (Intel and Apple Silicon)
- ✅ Linux: Full support (most distributions)
- 🚧 Windows: Coming soon (estimated Q2 2026)

**Windows Workaround:** Use Windows Subsystem for Linux (WSL2):
```bash
# Inside WSL2 terminal
/claude
# Sandbox works normally inside Linux environment
```

### Performance Impact

**Typical Overhead:**
- Startup: +200-500ms per command
- Execution: +5-10% runtime overhead
- Memory: +50-100MB for sandbox process

**When to Disable Sandbox:**
- Performance-critical benchmarking
- Real-time interactive applications
- High-frequency file I/O operations

### Known Issues & Workarounds

#### Issue 1: Symlinks Across Boundaries

**Problem:** Sandbox blocks symlinks pointing outside allowed directories.

```bash
# ❌ Won't work
ln -s ~/.ssh/id_rsa ./key  # Symlink to blocked directory

# ✅ Workaround
cp ~/.ssh/id_rsa.pub ./public_key  # Copy file instead
```

#### Issue 2: Git Credentials

**Problem:** Sandbox can't access SSH keys or git credentials for private repos.

```bash
# ✅ Solution 1: Use HTTPS with Personal Access Token
git clone https://token@github.com/org/repo.git

# ✅ Solution 2: Add repo to allowlist (macOS)
# Edit settings to allow ~/.ssh access for specific commands
{
  "sandboxRuntime": {
    "fileAccess": {
      "exceptions": [
        {
          "command": "git",
          "path": "~/.ssh"
        }
      ]
    }
  }
}
```

#### Issue 3: Docker Inside Sandbox

**Problem:** Docker daemon access is restricted.

```bash
# ❌ Won't work
docker run -it ubuntu

# ✅ Workaround 1: Disable sandbox for Docker
/no-sandbox
docker build -t myapp .

# ✅ Workaround 2: Use allowed host paths
docker run -v /tmp/my-project:/app myapp
```

### Roadmap & Future Improvements

**Planned (Q1 2026):**
- [ ] Windows support
- [ ] Container runtime integration
- [ ] GPU access configuration
- [ ] Custom permission policies

**Under Consideration:**
- [ ] Remote sandbox execution (cloud)
- [ ] Multi-user sandbox sharing
- [ ] Hardware accelerator access
- [ ] Persistent sandbox state

---

## Commands & Operations

### Sandbox Management

```bash
# View sandbox status
/sandbox status

# Enable/disable sandbox
/sandbox enable
/sandbox disable

# Check sandbox version
/sandbox version

# View sandbox logs
/sandbox logs

# Reset sandbox to defaults
/sandbox reset
```

### Permission Management

```bash
# View pending permissions
/sandbox permissions

# Grant one-time permission
/sandbox allow-once /path/to/file

# Grant permanent permission
/sandbox allow /path/to/file

# Revoke permission
/sandbox revoke /path/to/file

# Clear all permission history
/sandbox clear-permissions
```

### Debugging & Troubleshooting

```bash
# Test file access
/sandbox test-file /path/to/test

# Test network access
/sandbox test-network example.com

# Show sandbox environment
/sandbox env

# Enable verbose logging
CLAUDE_SANDBOX_DEBUG=1 /claude
```

---

## Troubleshooting

### Sandbox Won't Start

**Symptom:** Error "Sandbox runtime not available"

**Solutions:**
1. Reinstall sandbox: `/sandbox install`
2. Check disk space: `df -h ~/.claude/sandbox`
3. Verify permissions: `ls -la ~/.claude/sandbox`
4. Check for corrupted files: `/sandbox verify`

```bash
# Full reset
rm -rf ~/.claude/sandbox
/sandbox  # Will reinstall
```

### Permission Denied Errors

**Symptom:** "Permission denied" when accessing files

**Diagnosis:**
```bash
# Check what's being blocked
/sandbox test-file ~/file.txt

# View allowed directories
grep allowedDirs ~/.claude/settings.json
```

**Solution:** Add directory to allowlist
```json
{
  "sandboxRuntime": {
    "fileAccess": {
      "allowedDirs": ["~", "/tmp", "~/my-project"]
    }
  }
}
```

### Network Requests Failing

**Symptom:** "Network request blocked" or timeout errors

**Diagnosis:**
```bash
# Check network allowlist
/sandbox test-network api.example.com

# View blocked requests in logs
/sandbox logs | grep "network"
```

**Solution:** Add host to allowlist
```json
{
  "sandboxRuntime": {
    "networkAccess": {
      "allowlist": ["api.example.com", "*.example.com"]
    }
  }
}
```

### Performance Issues

**Symptom:** Commands running slowly with sandbox enabled

**Solutions:**
1. Check sandbox resource usage: `/sandbox stats`
2. Disable for performance-critical tasks: `/no-sandbox`
3. Add frequently-accessed directories to allowlist (reduces permission checks)
4. Close other sandbox instances: `/sandbox cleanup`

---

## Best Practices

### 1. Keep Sandbox Enabled by Default

Sandboxing should be your default for daily development:

```json
{
  "sandboxRuntime": {
    "enabled": true,
    "defaultOnStartup": true
  }
}
```

### 2. Use `.claude/sandbox.json` for Projects

Version-control sandbox configuration per project:

```bash
# .claude/sandbox.json (in repo)
{
  "fileAccess": {
    "allowedDirs": [".", "/tmp", "./node_modules"]
  },
  "networkAccess": {
    "allowlist": ["registry.npmjs.org", "api.github.com"]
  }
}
```

### 3. Minimize Allowed Directories

More restricted = more secure. Only allow what's needed:

```json
{
  "fileAccess": {
    "allowedDirs": [
      ".",              // Current project only
      "/tmp",           // Temp files
      "/var/tmp"        // More temp files
    ]
  }
}
```

### 4. Regularly Review Permissions

Check and clean up permissions periodically:

```bash
# View all granted permissions
/sandbox permissions

# Revoke unused permissions
/sandbox revoke ~/old-project
```

### 5. Document Exceptions

When you disable sandbox or add exceptions, document why:

```bash
# ✅ Good
# Disabled sandbox for Docker build (can't access daemon in sandbox)
/no-sandbox
docker build -t myapp .

# ✅ Good
# Added ~/.ssh exception for git operations (required for private repos)
{
  "exceptions": [
    {
      "command": "git",
      "paths": ["~/.ssh", "~/.gitconfig"]
    }
  ]
}
```

---

## Security Considerations

### What Sandbox Protects Against

✅ **Protects Against:**
- Untrusted npm packages accessing files outside project
- Malicious scripts reading SSH keys or credentials
- Unauthorized network requests to internal services
- Accidental system file modifications
- Third-party code accessing sensitive directories

❌ **Doesn't Protect Against:**
- Vulnerabilities in your own code
- Intentional privilege escalation (with your confirmation)
- Local privilege escalation exploits on your OS
- Network attacks on allowlisted services
- Man-in-the-middle attacks (use HTTPS/TLS)

### Principle of Least Privilege

Only grant access when needed:

```json
{
  "fileAccess": {
    "allowedDirs": [
      ".",              // ✅ Minimal: just your project
      "/tmp"            // ✅ Safe: temp files only
    ]
  }
}
```

NOT:

```json
{
  "fileAccess": {
    "allowedDirs": [
      "~",              // ❌ Too broad: entire home directory
      "/"               // ❌ Too broad: entire filesystem
    ]
  }
}
```

### Audit Trail

Sandbox logs all access attempts:

```bash
# View access log
/sandbox logs --filter access

# Review recent permissions
/sandbox permissions --recent

# Export audit report
/sandbox audit-report > sandbox-audit.json
```

---

## Integration with Claude Code Ecosystem

### With MCP Servers

Sandbox works seamlessly with MCP servers:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  },
  "sandboxRuntime": {
    "networkAccess": {
      "allowlist": ["api.context7.io"]
    }
  }
}
```

### With Skills

Skills run inside the sandbox:

```markdown
# Custom Skill

This skill runs inside the sandbox.

\`\`\`bash
# Safe: Runs with sandbox restrictions
npm test
\`\`\`
```

### With Subagents

Subagents inherit sandbox configuration:

```bash
# Subagent spawned in sandbox by default
task "Review code in sandbox" --subagent developer
# ✅ Subagent sandbox: restricted file access, network allowlist
```

---

## Resources

### Official Documentation

- **Sandbox Runtime GitHub:** https://github.com/anthropic-experimental/sandbox-runtime
- **Claude Code Docs — Sandboxing:** https://code.claude.com/docs/en/sandboxing
- **Claude Code Release Notes:** https://code.claude.com/docs/releases

### Learn More

- **Claude Code Overview:** https://code.claude.com/
- **MCP Servers:** See `03-claude-code-ecosystem.md`
- **Skills System:** See `03-claude-code-ecosystem.md`
- **Security Best Practices:** https://security.anthropic.com/

### Community Resources

- Claude Code GitHub Discussions: https://github.com/anthropic-labs/claude-code/discussions
- Anthropic Security Blog: https://anthropic.com/security
- DevSecOps Best Practices: https://owasp.org/www-project-devsecops/

---

## Next Steps

### New to Claude Code?

1. **Start:** Enable sandbox with `/sandbox`
2. **Configure:** Review default settings in `~/.claude/settings.json`
3. **Verify:** Run `/sandbox status` to confirm it's working
4. **Learn:** Read about MCP servers in `03-claude-code-ecosystem.md`

### Experienced Developers?

1. **Integrate:** Add `.claude/sandbox.json` to your project
2. **Automate:** Configure sandbox in CI/CD pipelines
3. **Monitor:** Set up audit logging for security compliance
4. **Optimize:** Tune allowlist based on your workflow

### Team Leads?

1. **Standardize:** Create organization-wide sandbox config
2. **Document:** Add sandbox setup to onboarding guide
3. **Monitor:** Implement permission audit reports
4. **Update:** Keep sandbox runtime updated across team

---

## Summary Checklist

### Installation
- [ ] Sandbox runtime installed (`/sandbox`)
- [ ] Configuration verified (`/sandbox status`)
- [ ] Settings saved to `~/.claude/settings.json`

### Configuration
- [ ] Allowed directories configured
- [ ] Network allowlist set up
- [ ] Per-project `.claude/sandbox.json` created
- [ ] Permissions reviewed and minimized

### Integration
- [ ] Sandbox enabled by default
- [ ] MCP servers configured with correct allowlist
- [ ] Skills tested with sandbox enabled
- [ ] Subagents working correctly

### Security
- [ ] Audit logging enabled
- [ ] Permission audit conducted
- [ ] Sensitive paths blocked
- [ ] Exceptions documented

### Team
- [ ] Sandbox configuration shared with team
- [ ] Onboarding guide updated
- [ ] Best practices documented
- [ ] Support process established

---

**Ready to sandbox?** Start with `/sandbox` and enjoy safer, smoother development!
