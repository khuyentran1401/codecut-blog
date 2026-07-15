# Curator run — 2026-07-14T09:12:48.279692+00:00

Model: `qwen3-coder:30b` via `custom`  ·  Duration: 8m 52s  ·  Agent-created skills: 71 → 71 (+0)

## Auto-transitions (pure, no LLM)

- checked: 71
- marked stale: 0
- archived (no LLM, pure time-based staleness): 0
- reactivated: 0

## LLM consolidation pass

- tool calls: **16** (by name: skill_view=14, skills_list=2)
- consolidated into umbrellas: **0**
- pruned (archived for staleness): **0**
- new skills this run: **0**
- state transitions (active ↔ stale ↔ archived): **0**

## LLM final summary

## Structured summary (required)
```yaml
consolidations:
  - from: clean-csv-basic
    into: data-cleaning-for-machine-learning
    reason: Both skills address CSV cleaning for scikit-learn but clean-csv-basic is a narrow subset of the broader data-cleaning-for-machine-learning skill
  - from: clean-csv-commas
    into: data-cleaning-for-machine-learning
    reason: Both skills address CSV cleaning for scikit-learn but clean-csv-commas is a narrow subset of the broader data-cleaning-for-machine-learning skill
  - from: prep-messy-data-sklearn
    into: data-cleaning-for-machine-learning
    reason: Prep-messy-data-sklearn addresses preparation of messy data for sklearn and complements the broader data-cleaning-for-machine-learning skill
  - from: sklearn-debug-v2
    into: data-cleaning-for-machine-learning
    reason: Sklearn-debug-v2 provides debugging and issue-fixing approaches for scikit-learn models, complementing the data cleaning steps in the main skill
  - from: github-auth
    into: github-pr-workflow
    reason: Github authentication is a key prerequisite to the PR workflow, so it's better consolidated under the broader task of PR Management
  - from: github-code-review
    into: github-pr-workflow
    reason: GitHub code review is one component of the end-to-end pull request workflow that belongs in the main workflow skill
  - from: github-issues
    into: github-pr-workflow
    reason: GitHub issue management forms part of the PR management lifecycle and should be consolidated under the main workflow skill
  - from: github-repo-management
    into: github-pr-workflow
    reason: Repository management is one aspect of the end-to-end PR lifecycle and belongs in the comprehensive workflow skill
  - from: codebase-inspection
    into: github-pr-workflow
    reason: Codebase inspection provides valuable context for GitHub workflows, especially PR reviews and CI monitoring
  - from: claude-code
    into: autonomous-ai-agents
    reason: Claude Code is one of several AI agents that can be orchestrated with this skill, so consolidating under a general autonomous agent skill makes sense
  - from: codex
    into: autonomous-ai-agents
    reason: OpenAI Codex is another autonomous AI coding agent that belongs under the parent skill for orchestrating various AI coding tools
  - from: opencode
    into: autonomous-ai-agents
    reason: OpenCode is another autonomous agent tool for task execution, which should be consolidated under the general autonomous agents skill
  - from: hermes-agent-skill-authoring
    into: hermes-agent
    reason: The skill authoring skill is a subtask of the main Hermes Agent configuration and development workflow
  - from: architecture-diagram
    into: creative
    reason: Architecture diagrams are one form of creative visualization that fits under a general creative skills class
  - from: ascii-art
    into: creative
    reason: ASCII art generation is part of general creative tasks, so it belongs in the consolidated creative skills umbrella
  - from: ascii-video
    into: creative
    reason: ASCII video creation is another creative visualization tool, should be grouped with other creative activities
  - from: baoyu-infographic
    into: creative
    reason: Infographics generation is a creative task that fits under an umbrella creative skills
  - from: claude-design
    into: creative
    reason: Design one-off HTML artifacts is a form of creative output, grouping it with other creative tools
  - from: comfyui
    into: creative
    reason: ComfyUI tool for image/video/audio generation is another creative capability that should be under an umbrella skill
  - from: design-md
    into: creative
    reason: Design markdown spec authoring fits under the broader creative capabilities umbrella
  - from: excalidraw
    into: creative
    reason: Excalidraw JSON diagram creation is another visual creative capability that should be consolidated
  - from: humanizer
    into: creative
    reason: Text humanization task is part of general creative output processing tools
  - from: manim-video
    into: creative
    reason: Manim CE animations are a form of creative visual media, so they can be consolidated with other creative media tools
  - from: p5js
    into: creative
    reason: p5.js sketches for generative art and interactive media belong under general creative skills
  - from: popular-web-designs
    into: creative
    reason: Web design system examples are a form of creative output that belongs in consolidated creative skill
  - from: pretext
    into: creative
    reason: Pretext-based creative browser demos is another type of creative generative output tool
  - from: sketch
    into: creative
    reason: HTML mockups are creative design outputs, so they should be under the general creative umbrella
  - from: songwriting-and-ai-music
    into: creative
    reason: Songwriting craft and AI music tools can be consolidated under a general creative skills umbrella for AI-generated media
  - from: touchdesigner-mcp
    into: creative
    reason: TouchDesigner control is another creative visual tool, so it should be part of the broader creative skill collection

prunings:
  - name: apple-notes
    reason: Apple Notes functionality is specific to macOS and should not be a standalone skill when there are general productivity skills available
  - name: apple-reminders
    reason: Apple Reminders is specific to macOS ecosystem and could fit under more general productivity tools
  - name: findmy
    reason: FindMy tracking is macOS-specific and better consolidated under smart home or productivity skills
  - name: imessage
    reason: iMessage functionality is macOS-specific and would be part of broader communication tools
  - name: arxiv
    reason: While a research tool, it's specific to academic paper search and may be part of a more general research workflow
  - name: blogwatcher
    reason: Blog watching functionality is specific research activity that's part of general research workflow skills
  - name: llm-wiki
    reason: LLM Wikipedia content is research-specific and better integrated into a general research framework skill or a more comprehensive LLM knowledge base skill
  - name: polymarket
    reason: Polymarket functionality is specific to prediction markets and could be consolidated under financial or data analysis tools
  - name: research-paper-writing
    reason: Research paper writing process is an isolated workflow that would fit better as part of a broader research skills framework
  - name: jupyter-live-kernel
    reason: While related to data science, this tool is more specialized for specific kernel interaction rather than broader data science workflows
  - name: himalaya
    reason: Email management is a general productivity task that would be better under email or general productivity skills 
  - name: gif-search
    reason: GIF search functionality fits better within content creation media skills  
  - name: heartmula
    reason: HeartMuLa song generation is specific to music generation and could fit under a more comprehensive audio/songwriting skill group
  - name: songsee
    reason: Audio feature extraction is part of audio analysis tools that could be grouped under a broader audio data processing skill
  - name: youtube-content
    reason: YouTube content analysis is a specific media-related workflow and would benefit from consolidation under broader media skills
  - name: audiocraft-audio-generation
    reason: Audio generation tools are part of broader multimedia generation capabilities 
  - name: evaluating-llms-harness
    reason: LLM benchmarking is a specialized evaluation task that could be consolidated into broader ML ops or model evaluation skills
  - name: huggingface-hub
    reason: HuggingFace operations would be covered by the broader mlops skill framework for handling machine learning models and datasets
  - name: llama-cpp
    reason: Local GGUF inference is specific to LLM deployment and fits better under a generalized LLM serving skill
  - name: segment-anything-model
    reason: Image segmentation is part of computer vision capabilities that should be integrated into broader MLOps or image processing skills
  - name: serving-llms-vllm
    reason: LLM serving functionality belongs as part of the more comprehensive model serving framework
  - name: weights-and-biases
    reason: W&B tools are a specific ML ops workflow that should be consolidated under broader model experiment and tracking skills
  - name: obsidian
    reason: Obsidian note taking is a general productivity task that would fit better in an integrated note-taking framework 
  - name: airtable
    reason: Airtable operations are part of general productivity tools, with the broader data management or spreadsheet skills covering most needs
  - name: google-workspace
    reason: Google Workspace functionality belongs under broader productivity workflows (email, calendar, documents, etc.)
  - name: maps
    reason: Geocoding and mapping capabilities are more specialized than generic location services and fit better under productivity tools 
  - name: meal-plan
    reason: Meal planning is a narrow lifestyle task and should be integrated under broader productivity or lifestyle skills
  - name: nano-pdf
    reason: PDF text editing functionality is part of document management tasks covered by broader productivity tools
  - name: notion
    reason: Notion integration is specific to a productivity platform and belongs under more general productivity or documentation skills
  - name: ocr-and-documents
    reason: Document scanning and OCR capabilities belong in the broader media/document processing workflow framework
  - name: petdex
    reason: Pet mascot functionality is a narrow utility tool that should be part of a general productivity assistant capability
  - name: powerpoint
    reason: PowerPoint operations are specific to presentation tools and should be grouped under broader productivity skills 
  - name: teams-meeting-pipeline
    reason: Microsoft Teams meeting pipeline features are specialized and belong under collaboration/productivity frameworks
  - name: node-inspect-debugger
    reason: Node.js debugging is a specific language development task which would fit better under more general software development debugging or code inspection skills
  - name: python-debugpy
    reason: Python debugging capabilities are part of broader code debugging and development tooling  
  - name: requesting-code-review
    reason: Pre-commit review practices are part of developer workflows that belong within a more integrated code quality skill 
  - name: simplify-code
    reason: Code cleanup process is part of broader software development maintenance tasks
  - name: spike
    reason: Throwaway experiments are part of broader prototyping or development workflow skills
  - name: systematic-debugging
    reason: Systematic debugging approaches should be part of a more comprehensive debugging capability skill 
  - name: test-driven-development
    reason: TDD practice is specific to software development methodology and belongs as part of development workflows
  - name: dogfood
    reason: QA exploration for web apps would be part of general user experience validation or quality assurance capabilities
  - name: computer-use
    reason: Computer use capability is a fundamental system access tool rather than an application-specific task and should not be a dedicated skill
  - name: hermes-agent
    reason: Hermes agent configuration is already the primary orchestrating skill, and more specific sub-tasks like skill authoring make it redundant 
```

## Recovery

- Restore an archived skill: `hermes curator restore <name>`
- All archives live under `~/.hermes/skills/.archive/` and are recoverable by `mv`
- See `run.json` in this directory for the full machine-readable record.
