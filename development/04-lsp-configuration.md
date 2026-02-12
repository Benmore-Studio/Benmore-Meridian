# Claude Code LSP Configuration Guide

## 📋 Overview

Language Server Protocol (LSP) provides Claude Code with real-time code intelligence, autocompletion, error checking, and navigation across your codebase. This guide covers setting up language servers for multiple languages and configuring Claude Code to use them effectively.

---

## 🤔 What is Language Server Protocol (LSP)?

**LSP** is a standardized protocol that enables editors and tools to communicate with language-specific servers for:

- **Autocompletion** — Context-aware code suggestions as you type
- **Error checking** — Real-time linting and type errors
- **Go to definition** — Jump to function/class definitions
- **Hover information** — Type hints and documentation on hover
- **Refactoring** — Rename symbols, extract functions, organize imports
- **Diagnostics** — Warnings, errors, and suggestions

LSP servers run as background processes. Claude Code communicates with them to provide intelligent code assistance across supported languages.

**Benefits for Claude Code:**
- More accurate code understanding
- Better context for code generation
- Faster error detection and fixing
- Improved refactoring recommendations
- Cross-file symbol resolution

---

## 🌍 Supported Languages

| Language | Primary Server | Alternatives |
|----------|---|---|
| **Python** | `pylsp` (Python LSP Server) | `pyright`, `pylint-daemon` |
| **TypeScript/JavaScript** | `typescript-language-server` | `deno_lsp`, `vscode-langservers-extracted` |
| **Rust** | `rust-analyzer` | — |
| **Go** | `gopls` (Go Language Server) | — |
| **Ruby** | `solargraph` | `ruby-lsp` |
| **Java** | `eclipse.jdt.ls` | `java-language-server` |
| **C/C++** | `clangd` | `ccls` |
| **CSS/HTML** | `vscode-langservers-extracted` | — |
| **JSON/YAML** | `yaml-language-server` | `json-language-server` |

---

## 💾 Installation

### Prerequisites

Ensure you have:
- Claude Code installed and updated to latest version
- Node.js/npm installed (for Node-based servers)
- Python 3.8+ (for Python servers)
- Homebrew (macOS) or system package manager

### Python LSP Setup

#### Option 1: Using `pylsp` (Recommended for General Use)

**Installation:**

```bash
# Using uv (fastest)
uv pip install python-lsp-server

# Or using pip
pip install python-lsp-server

# Install useful plugins
uv pip install \
  python-lsp-ruff \
  pylsp-mypy \
  python-lsp-black
```

**Verify installation:**

```bash
pylsp --version
```

#### Option 2: Using `pyright` (Recommended for Type Checking)

**Installation:**

```bash
# Using npm
npm install -g pyright

# Or using uv
uv pip install pyright

# Or using Homebrew (macOS)
brew install pyright
```

**Verify installation:**

```bash
pyright --version
```

#### Option 3: Using `pylint-daemon`

**Installation:**

```bash
pip install pylint
pylint-daemon --version
```

### TypeScript/JavaScript LSP Setup

#### Option 1: Using `typescript-language-server` (Recommended)

**Installation (Node project):**

```bash
# Local installation (recommended)
npm install --save-dev typescript typescript-language-server

# Or global installation
npm install -g typescript-language-server

# Verify
npx tsserver --version
```

#### Option 2: Using Deno LSP

**Installation:**

```bash
# Using Homebrew (macOS)
brew install deno

# Or from source
curl -fsSL https://deno.land/install.sh | sh

# Verify
deno --version
```

### Rust LSP Setup

**Installation:**

```bash
# Using rustup (recommended)
rustup component add rust-analyzer

# Or via Homebrew (macOS)
brew install rust-analyzer

# Verify
rust-analyzer --version
```

### Go LSP Setup

**Installation:**

```bash
# Using go install
go install github.com/golang/tools/gopls@latest

# Or via Homebrew (macOS)
brew install gopls

# Verify
gopls version
```

### Ruby LSP Setup

**Installation:**

```bash
# Using gem
gem install solargraph

# Or add to Gemfile
bundle add solargraph --group development

# Verify
solargraph version
```

### C/C++ LSP Setup

**Installation:**

```bash
# Using Homebrew (macOS)
brew install clangd

# Or on Ubuntu/Debian
sudo apt install clangd

# Verify
clangd --version
```

### CSS/HTML/JSON LSP Setup

**Installation:**

```bash
# Using npm
npm install -g vscode-langservers-extracted

# Verify
node -e "console.log(require('vscode-langservers-extracted/package.json').version)"
```

---

## ⚙️ Configuration

### Claude Code Global Settings

Edit `~/.claude/settings.json` to configure language servers globally:

**Basic Configuration (add to your settings.json):**

```json
{
  "lsp": {
    "enabled": true,
    "servers": {
      "python": {
        "command": "pylsp",
        "args": [],
        "filetypes": ["python"]
      },
      "typescript": {
        "command": "tsserver",
        "args": [],
        "filetypes": ["typescript", "typescriptreact", "javascript", "javascriptreact"]
      },
      "rust": {
        "command": "rust-analyzer",
        "args": [],
        "filetypes": ["rust"]
      },
      "go": {
        "command": "gopls",
        "args": ["serve"],
        "filetypes": ["go"]
      }
    }
  }
}
```

**Advanced Configuration with Settings:**

```json
{
  "lsp": {
    "enabled": true,
    "diagnosticsDelay": 500,
    "hoverDelay": 200,
    "completionChars": [".", ":", "-", ">", "/", "@"],
    "servers": {
      "python": {
        "command": "pylsp",
        "args": [],
        "filetypes": ["python"],
        "settings": {
          "pylsp": {
            "plugins": {
              "pycodestyle": {
                "enabled": true
              },
              "pyflakes": {
                "enabled": true
              },
              "mccabe": {
                "enabled": true
              },
              "pylint": {
                "enabled": false
              }
            }
          }
        }
      },
      "typescript": {
        "command": "tsserver",
        "args": ["--stdio"],
        "filetypes": ["typescript", "typescriptreact", "javascript", "javascriptreact"],
        "settings": {
          "typescript": {
            "preferences": {
              "quotePreference": "single",
              "importModuleSpecifierPreference": "relative"
            }
          }
        }
      },
      "rust": {
        "command": "rust-analyzer",
        "args": [],
        "filetypes": ["rust"],
        "settings": {
          "rust-analyzer": {
            "checkOnSave": {
              "command": "clippy"
            }
          }
        }
      }
    }
  }
}
```

### Per-Project Configuration

For project-specific LSP settings, create `.claude/lsp.json` in your project root:

**Example: Django Project with Python LSP**

Create `.claude/lsp.json`:

```json
{
  "servers": {
    "python": {
      "command": "pylsp",
      "args": ["--log-level", "debug"],
      "settings": {
        "pylsp": {
          "plugins": {
            "pycodestyle": {
              "maxLineLength": 100
            },
            "pyflakes": {
              "enabled": true
            },
            "autopep8": {
              "enabled": false
            },
            "yapf": {
              "enabled": false
            }
          }
        }
      },
      "initialization_options": {
        "workspace": "${workspaceFolder}"
      }
    }
  }
}
```

**Example: Next.js Project with TypeScript LSP**

Create `.claude/lsp.json`:

```json
{
  "servers": {
    "typescript": {
      "command": "tsserver",
      "args": ["--stdio"],
      "settings": {
        "typescript": {
          "tsdk": "./node_modules/typescript/lib",
          "enablePromptUseWorkspaceTsdk": true,
          "preferences": {
            "quotePreference": "single",
            "importModuleSpecifierPreference": "relative",
            "importModuleSpecifierEnding": "auto"
          }
        }
      }
    }
  }
}
```

**Example: Monorepo with Multiple Servers**

Create `.claude/lsp.json`:

```json
{
  "servers": {
    "python": {
      "command": "pylsp",
      "filetypes": ["python"],
      "rootPatterns": ["pyproject.toml", "setup.py", "requirements.txt"]
    },
    "typescript": {
      "command": "tsserver",
      "filetypes": ["typescript", "typescriptreact", "javascript", "javascriptreact"],
      "rootPatterns": ["tsconfig.json", "package.json"]
    },
    "rust": {
      "command": "rust-analyzer",
      "filetypes": ["rust"],
      "rootPatterns": ["Cargo.toml"]
    }
  }
}
```

---

## 🔧 Server-Specific Configuration

### Python LSP Server (pylsp)

**Configuration file:** `.pylsp.json` or `pyproject.toml`

**Example .pylsp.json:**

```json
{
  "pylsp": {
    "configurationSources": ["pycodestyle"],
    "plugins": {
      "pycodestyle": {
        "enabled": true,
        "maxLineLength": 100
      },
      "pyflakes": {
        "enabled": true
      },
      "autopep8": {
        "enabled": false
      },
      "rope": {
        "enabled": true
      },
      "mypy": {
        "enabled": true,
        "strict": false
      },
      "pylint": {
        "enabled": false
      }
    }
  }
}
```

**Example pyproject.toml (if using ruff):**

```toml
[tool.pylsp]
plugins.pycodestyle.enabled = false
plugins.pyflakes.enabled = false
plugins.ruff.enabled = true

[tool.pylsp.plugins.ruff]
extend-ignore = ["E203"]
line-length = 100

[tool.pylsp.plugins.mypy]
enabled = true
strict = false
```

### TypeScript Language Server

**Configuration file:** `tsconfig.json` (automatic)

**Example tsconfig.json:**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "lib": ["ES2020", "DOM"],
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "node",
    "noImplicitAny": true,
    "strictNullChecks": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### Rust Analyzer

**Configuration file:** `rust-analyzer.toml` or settings in VS Code-like editors

**Example rust-analyzer.toml:**

```toml
# In project root or ~/.config/rust-analyzer/rust-analyzer.toml

[assist]
emitMustUse = true

[checkOnSave]
command = "clippy"
allTargets = true

[inlayHints]
parameterHints = true
typeHints = true
chainingHints = true

[lens]
run = true
debug = true
```

### Go LSP Server (gopls)

**Configuration in VS Code settings (or equivalent):**

```json
{
  "gopls": {
    "gofumpt": true,
    "staticcheck": true,
    "usePlaceholders": true,
    "completeUnimported": true,
    "directoryFilters": ["-.*"],
    "semanticTokens": true
  }
}
```

---

## 🛠️ Integration with Claude Code Tools

### Using LSP with MCP Servers

Combine LSP with Context7 for maximum code intelligence:

```bash
# In your prompt, tell Claude to use both LSP and Context7
"Use LSP to check types and errors. use context7 to get latest Django docs."
```

### Using LSP with Skills

Create a skill that leverages LSP for code review:

**Example: `.claude/skills/lsp-code-review.md`**

```markdown
---
name: LSP Code Review
trigger: review code with lsp
---

# LSP-Powered Code Review

1. **Check diagnostics**: Use LSP to identify all errors and warnings
2. **Verify types**: Ensure type hints are correct and complete
3. **Find definitions**: Navigate to related definitions to understand context
4. **Refactor safely**: Suggest refactorings based on LSP analysis

## Process

- Get all LSP diagnostics for the file
- Group by severity (errors, warnings, info)
- Provide fixes with file locations
- Suggest refactorings
```

### Using LSP with Subagents

Spawn subagents to fix LSP-reported issues in parallel:

```bash
# Tell Claude to spawn subagents for each error category
"I have 50 TypeScript errors from LSP. Spawn subagents:
- One for missing type annotations (errors 1-15)
- One for null safety issues (errors 16-30)
- One for import fixes (errors 31-50)

Use LSP to verify each fix."
```

---

## 🔍 Troubleshooting

### LSP Server Not Starting

**Problem:** LSP server fails to start or immediately crashes.

**Solutions:**

1. **Verify server installation:**
   ```bash
   # Check if server is in PATH
   which pylsp
   which tsserver
   which rust-analyzer
   ```

2. **Test server directly:**
   ```bash
   # Try running the server in isolation
   pylsp --version
   rust-analyzer --version
   tsserver --version
   ```

3. **Check logs:**
   ```bash
   # Enable debug logging in settings.json
   {
     "lsp": {
       "debug": true,
       "logLevel": "debug"
     }
   }
   ```

4. **Reinstall server:**
   ```bash
   # Python
   pip uninstall python-lsp-server -y && pip install python-lsp-server

   # TypeScript
   npm uninstall -g typescript-language-server && npm install -g typescript-language-server
   ```

### Slow Autocompletion

**Problem:** Code completion is lagging or slow.

**Solutions:**

1. **Increase completion delay threshold:**
   ```json
   {
     "lsp": {
       "completionDelay": 500,
       "diagnosticsDelay": 1000
     }
   }
   ```

2. **Disable heavy plugins:**
   ```json
   {
     "pylsp": {
       "plugins": {
         "pylint": { "enabled": false },
         "rope": { "enabled": false }
       }
     }
   }
   ```

3. **Check system resources:**
   ```bash
   # Monitor LSP server memory usage
   ps aux | grep pylsp
   ps aux | grep tsserver
   ```

### Type Checking Shows Errors (But Code Works)

**Problem:** LSP reports type errors that don't match your project's actual configuration.

**Solutions:**

1. **Check project root detection:**
   ```json
   {
     "lsp": {
       "rootPatterns": ["pyproject.toml", "setup.py", "requirements.txt"]
     }
   }
   ```

2. **Verify type checking configuration:**
   ```bash
   # For Python
   cat pyproject.toml | grep -A 10 "[tool.mypy]"

   # For TypeScript
   cat tsconfig.json
   ```

3. **Adjust LSP strictness:**
   ```json
   {
     "pylsp": {
       "plugins": {
         "mypy": {
           "strict": false,
           "ignore_missing_imports": true
         }
       }
     }
   }
   ```

### No Autocompletion for Project Files

**Problem:** LSP provides completions for external libraries but not your own code.

**Solutions:**

1. **Ensure workspace is recognized:**
   ```json
   {
     "lsp": {
       "initialization_options": {
         "workspace": "${workspaceFolder}"
       }
     }
   }
   ```

2. **Check Python path:**
   ```bash
   # Add project to PYTHONPATH for Python LSP
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

3. **Verify file is indexed:**
   - Restart Claude Code
   - Wait 5-10 seconds for server to index files
   - Try autocompletion again

### LSP Crashes or Becomes Unresponsive

**Problem:** LSP server crashes or stops responding.

**Solutions:**

1. **Restart LSP server:**
   ```bash
   # Restart Claude Code to reload LSP servers
   # Or use: Cmd+K > "LSP: Restart Servers"
   ```

2. **Check for syntax errors in config:**
   ```bash
   # Validate JSON syntax in settings.json
   python -m json.tool ~/.claude/settings.json
   ```

3. **View server output:**
   ```json
   {
     "lsp": {
       "debug": true,
       "logLevel": "trace"
     }
   }
   ```

4. **Disable problematic plugins:**
   ```json
   {
     "pylsp": {
       "plugins": {
         "mypy": { "enabled": false },
         "pylint": { "enabled": false }
       }
     }
   }
   ```

---

## 📊 Performance Optimization

### Multi-Language Workspaces

For monorepos with multiple languages, optimize server configuration:

**Stagger server startup:**

```json
{
  "lsp": {
    "servers": {
      "python": {
        "command": "pylsp",
        "delay": 0,
        "enabled": true
      },
      "typescript": {
        "command": "tsserver",
        "delay": 2000,
        "enabled": true
      },
      "rust": {
        "command": "rust-analyzer",
        "delay": 4000,
        "enabled": true
      }
    }
  }
}
```

### Memory Management

**Limit LSP resource usage:**

```json
{
  "lsp": {
    "maxMemory": 1024,
    "indexFileLimit": 5000,
    "diagnosticsDelay": 1000
  }
}
```

### File Exclusions

**Exclude large directories from indexing:**

```json
{
  "lsp": {
    "exclude": [
      "node_modules/**",
      "dist/**",
      "build/**",
      "__pycache__/**",
      ".venv/**",
      "venv/**"
    ]
  }
}
```

---

## 🚀 Advanced Usage

### Language-Specific Tips

#### Python

**Enable type checking in development:**
```bash
# Install mypy plugin
pip install pylsp-mypy

# Enable strict mode for your project
[tool.mypy]
strict = true
ignore_missing_imports = true
```

**Organize imports automatically:**
```bash
# Install isort plugin
pip install pylsp-isort
```

#### TypeScript/JavaScript

**Ensure correct TypeScript version:**
```bash
# Use local TypeScript instead of global
npx tsserver --version

# Configure in settings
{
  "typescript": {
    "tsdk": "./node_modules/typescript/lib"
  }
}
```

**Enable strict mode:**
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
```

#### Rust

**Use clippy for linting:**
```toml
[rust-analyzer]
checkOnSave = { command = "clippy" }
```

**Enable inlay hints:**
```json
{
  "rust-analyzer": {
    "inlayHints": {
      "parameterHints": true,
      "typeHints": true,
      "chainingHints": true
    }
  }
}
```

---

## 📚 Resources

### Official Documentation

- **Language Server Protocol** — https://microsoft.github.io/language-server-protocol/
- **Claude Code Documentation** — https://claude.ai/help/code
- **LSP Specification** — https://microsoft.github.io/language-server-protocol/specifications/specification-current/

### Language-Specific Resources

- **Python LSP** — https://github.com/python-lsp/python-lsp-server
- **Pyright** — https://github.com/microsoft/pyright
- **TypeScript Language Server** — https://github.com/typescript-language-server/typescript-language-server
- **Rust Analyzer** — https://rust-analyzer.github.io/
- **gopls** — https://github.com/golang/tools/wiki/gopls
- **Solargraph (Ruby)** — https://solargraph.org/
- **Clangd (C/C++)** — https://clangd.llvm.org/

### Community Resources

- **LSP Implementations** — https://microsoft.github.io/language-server-protocol/implementors/servers/
- **Awesome LSP** — https://github.com/topics/language-server-protocol
- **Stack Overflow** — Tag: `lsp` or language-specific tags

---

## ✅ Verification Checklist

After configuring LSP, verify everything is working:

**Global Setup:**
- [ ] LSP enabled in `~/.claude/settings.json`
- [ ] Language servers installed and in PATH
- [ ] Can run `{server} --version` successfully

**Per-Project Setup:**
- [ ] `.claude/lsp.json` created (if project-specific settings needed)
- [ ] Project-specific config files exist (`tsconfig.json`, `pyproject.toml`, etc.)
- [ ] Workspace root detected correctly

**Functionality:**
- [ ] Autocompletion works (test with a `.`)
- [ ] Hover information shows type hints
- [ ] Error/warning diagnostics appear in real-time
- [ ] Go to definition navigates correctly
- [ ] No console errors or crashes

**Performance:**
- [ ] Autocompletion responds within 500ms
- [ ] No excessive memory usage (< 500MB per server)
- [ ] File indexing completes within 30 seconds

---

## 💡 Pro Tips

1. **Combine LSP with Context7** — LSP for local code intelligence, Context7 for external library docs

2. **Use LSP with code generation** — Let LSP validate generated code in real-time

3. **Enable strict mode** — Catch more issues during development, not in production

4. **Create project templates** — Save `.claude/lsp.json` in your project templates for quick setup

5. **Monitor server health** — Check `~/.claude/logs/` for LSP server output

6. **Keep servers updated** — Periodically update language servers for new features and fixes
   ```bash
   # Python
   pip install --upgrade python-lsp-server pyright

   # Node
   npm update -g typescript-language-server
   ```

7. **Leverage refactoring** — Use LSP's rename and extract functions in combination with Claude

---

**Need help?** Check the troubleshooting section or refer to individual language server documentation.
