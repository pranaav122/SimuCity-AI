# SimuCity-AI-
Research-oriented multi-agent simulation platform for studying autonomous LLM agents, social interaction, resource allocation, and emergent collective behavior.
# SimuCity AI 🏙️

**An experimental laboratory for studying autonomous AI agents and emergent collective behavior.**

SimuCity AI is a research-oriented multi-agent simulation platform where autonomous LLM-powered agents inhabit a shared virtual environment, pursue individual goals, interact with other agents, manage resources, form relationships, and respond to changing environmental conditions.

Rather than building another AI chatbot, SimuCity separates **LLM reasoning from the simulation engine**, allowing agent behavior to be observed, measured, reproduced, and compared across different language models.

## Research Question

> **Can autonomous LLM-powered agents interacting in a shared environment produce measurable emergent collective behavior?**

## What We're Studying

- 🤖 Autonomous agent decision-making
- 🧠 Agent memory and planning
- 🤝 Cooperation and social interaction
- 💰 Resource allocation
- 🌐 Information propagation
- 👥 Group formation
- ⚡ Emergent collective behavior
- 📊 LLM behavioral evaluation
- 🔬 Reproducible AI experiments

## Architecture

```text
┌──────────────────────────────────────────┐
│              SimuCity World              │
│                                          │
│  Agents · Resources · Locations · Events │
└──────────────────┬───────────────────────┘
                   ↓
            Simulation Engine
                   ↓
          Agent Decision System
                   ↓
          ┌────────┴────────┐
          ↓                 ↓
      Claude            Other LLMs
          ↓                 ↓
          └────────┬────────┘
                   ↓
            Action Validator
                   ↓
             World State
                   ↓
          Metrics & Experiments
                   ↓
             Visualization
```

## Status

🚧 **Early development**

The system is being developed incrementally, beginning with the deterministic simulation engine before introducing LLM-powered autonomous agents.

Experimental results will be added only after the corresponding experiments have been implemented and evaluated.
