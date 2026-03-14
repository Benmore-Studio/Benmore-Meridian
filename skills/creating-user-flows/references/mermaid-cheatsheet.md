# Mermaid.js Cheatsheet for User Flows

## Flowchart Direction

Always use `flowchart TD` (top-down, vertical). Never use `flowchart LR` (horizontal).

## Node Shapes

| Shape | Syntax | Use For |
|-------|--------|---------|
| Rounded | `([text])` | Start/End points |
| Rectangle | `[text]` | Action steps |
| Diamond | `{text}` | Decision points |

## Arrow Types

| Arrow | Syntax | Use For |
|-------|--------|---------|
| Standard | `-->` | Normal flow |
| Labeled | `-->|Label|` | Conditional paths |
| Dotted | `-.->` | Optional or async steps |

## Subgraphs

Group related steps:

```
subgraph Onboarding
    SignUp --> Profile --> Questionnaire
end
```

- Always close with `end`
- Subgraphs can be nested
- Use for logical groupings (e.g., "Account Setup", "Payment Processing")

## Color Classes

### Standard palette (for detail diagrams)

Define at bottom of each flowchart using `classDef`:

```
classDef startEnd fill:#34d399,stroke:#059669,color:#000
classDef important fill:#fbbf24,stroke:#d97706,color:#000
classDef success fill:#34d399,stroke:#059669,color:#000
classDef warning fill:#f97316,stroke:#ea580c,color:#000
classDef special fill:#a78bfa,stroke:#7c3aed,color:#000
classDef error fill:#dc2626,stroke:#991b1b,color:#fff
```

### Overview palette (for overview diagrams)

Use a neutral stage class for all intermediate nodes:

```
classDef startEnd fill:#34d399,stroke:#059669,color:#000
classDef stage fill:#1e3a5f,stroke:#60a5fa,color:#fff
```

## Applying Classes

**CRITICAL: Always use batch notation at the bottom of the diagram. Never use inline `:::className`.**

Correct:
```
class Start,End startEnd
class Decision1,Decision2 important
class Error1,Error2 error
```

Wrong:
```
Start([Start]):::startEnd --> Step1
```

Multiple nodes can share a class in one line, comma-separated.

## Special Characters in Labels

Wrap text with special characters in double quotes:

```
Node["Text with (parentheses)"]
Node["Text with & ampersand"]
Node["Text with 'quotes'"]
```

Mermaid will error on unquoted `&`, `(`, `)`, `<`, `>` in node labels.

## Color Legend

Always include this color legend in both .md and .html outputs:

| Color | Meaning |
|-------|---------|
| Green | Start/End/Success states |
| Yellow | Important decision points |
| Orange | Warnings/Alerts |
| Purple | Special workflows |
| Red | Error states |

## Quick Reference: Complete Flowchart Template

```
flowchart TD
    Start([User Opens App]) --> Step1[First Action]
    Step1 --> Decision1{Has Account?}
    Decision1 -->|Yes| Login[Login]
    Decision1 -->|No| Register[Create Account]
    Login --> Dashboard[Dashboard]
    Register --> Dashboard
    Dashboard --> End([Flow Complete])

    classDef startEnd fill:#34d399,stroke:#059669,color:#000
    classDef important fill:#fbbf24,stroke:#d97706,color:#000

    class Start,End startEnd
    class Decision1 important
```
