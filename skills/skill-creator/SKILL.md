---
name: skill-creator
description: Guide for creating or updating skills that extend Manus via specialized knowledge, workflows, or tool integrations. For any modification or improvement request, MUST first read this skill and follow its update workflow instead of editing files directly.
license: Complete terms in LICENSE.txt
---

# Skill Creator

This skill provides guidance for creating effective skills.

## About Skills

Skills are modular, self-contained packages that extend Manus's capabilities by providing specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific domains or tasks—they transform Manus from a general-purpose agent into a specialized agent equipped with procedural knowledge that no model can fully possess.

### What Skills Provide

1. Specialized workflows - Multi-step procedures for specific domains
2. Tool integrations - Instructions for working with specific file formats or APIs
3. Domain expertise - Company-specific knowledge, schemas, business logic
4. Bundled resources - Scripts, references, and assets for complex and repetitive tasks

## Core Principles

### Concise is Key

The context window is a public good. Skills share the context window with everything else Manus needs: system prompt, conversation history, other Skills' metadata, and the actual user request.

**Default assumption: Manus is already very smart.** Only add context Manus doesn't already have. Challenge each piece of information: "Does Manus really need this explanation?" and "Does this paragraph justify its token cost?"

Prefer concise examples over verbose explanations.

### Set Appropriate Degrees of Freedom

Match the level of specificity to the task's fragility and variability:

**High freedom (text-based instructions)**: Use when multiple approaches are valid, decisions depend on context, or heuristics guide the approach.

**Medium freedom (pseudocode or scripts with parameters)**: Use when a preferred pattern exists, some variation is acceptable, or configuration affects behavior.

**Low freedom (specific scripts, few parameters)**: Use when operations are fragile and error-prone, consistency is critical, or a specific sequence must be followed.

Think of Manus as exploring a path: a narrow bridge with cliffs needs specific guardrails (low freedom), while an open field allows many routes (high freedom).

### Anatomy of a Skill

Every skill consists of a required SKILL.md file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── templates/        - Files used in output (templates, icons, fonts, etc.)
```

#### SKILL.md (required)

Every SKILL.md consists of:

- **Frontmatter** (YAML): Contains `name` and `description` fields. These are the only fields that Manus reads to determine when the skill gets used, thus it is very important to be clear and comprehensive in describing what the skill is, and when it should be used.
- **Body** (Markdown): Instructions and guidance for using the skill. Only loaded AFTER the skill triggers (if at all).

#### Bundled Resources (optional)

- **`scripts/`** - Executable code for repetitive or deterministic tasks (e.g., `rotate_pdf.py`). Token efficient, can run without loading into context.
- **`references/`** - Documentation loaded as needed (schemas, API docs, policies). Keeps SKILL.md lean. For large files (>10k words), include grep patterns in SKILL.md.
- **`templates/`** - Output assets not loaded into context (logos, fonts, boilerplate code).

**Avoid duplication**: Information lives in SKILL.md OR references, not both.

**Do NOT include**: README.md, CHANGELOG.md, or other auxiliary documentation. Skills are for AI agents, not users.

### Progressive Disclosure

Three-level loading system:
1. **Metadata** - Always in context (~100 words)
2. **SKILL.md body** - When skill triggers (<500 lines)
3. **Bundled resources** - As needed

Keep SKILL.md under 500 lines. When splitting content to references, clearly describe when to read them.

**Key principle:** Keep core workflow in SKILL.md; move variant-specific details to reference files.

Example structure for multi-domain skills:

```
bigquery-skill/
├── SKILL.md (overview + navigation)
└── references/
    ├── finance.md
    ├── sales.md
    └── product.md
```

Manus only loads the relevant reference file when needed.

## Skill Creation Process

Skill creation involves these steps:

1. Understand the skill with concrete examples
2. Plan reusable skill contents (scripts, references, templates)
3. Initialize the skill (run init_skill.py)
4. Edit the skill (implement resources and write SKILL.md)
5. Validate, package, and deliver the skill
6. Iterate based on real usage

Follow these steps in order, skipping only if there is a clear reason why they are not applicable.

### Step 1: Understanding the Skill with Concrete Examples

Skip this step only when the skill's usage patterns are already clearly understood.

Gather concrete examples of how the skill will be used. Ask questions like:
- "What functionality should this skill support?"
- "Can you give examples of how it would be used?"

Avoid asking too many questions at once. Conclude when you have a clear sense of the functionality.

### Step 2: Planning the Reusable Skill Contents

For each example, identify reusable resources:

| Resource Type | When to Use                     | Example                               |
| ------------- | ------------------------------- | ------------------------------------- |
| `scripts/`    | Code rewritten repeatedly       | `rotate_pdf.py` for PDF rotation      |
| `templates/`  | Same boilerplate each time      | HTML/React starter for webapp builder |
| `references/` | Documentation needed repeatedly | Database schemas for BigQuery skill   |

### Step 3: Initializing the Skill

At this point, it is time to actually create the skill.

Skip this step only if the skill being developed already exists, and iteration or packaging is needed. In this case, continue to the next step.

When creating a new skill from scratch, always run the `init_skill.py` script. The script conveniently generates a new template skill directory that automatically includes everything a skill requires, making the skill creation process much more efficient and reliable.

Usage (`<skill-creator-root>` is the directory containing this SKILL.md; use `python3` on macOS and Linux, `py -3` on Windows, and quote paths):

```bash
python3 "<skill-creator-root>/scripts/init_skill.py" <skill-name> [--output-dir "<absolute-directory>"]
```

The script:

- Creates the skill under `--output-dir`. Without it, uses `/home/ubuntu/skills/` on cloud runtimes and, on Work Locally, the Manus user skill directory: `user-skills` beside the directory that contains `skill-creator`, normally `~/.manus/user-skills`. If neither exists, it stops and asks for `--output-dir`
- Generates a SKILL.md template with proper frontmatter and TODO placeholders
- Creates example resource directories: `scripts/`, `references/`, and `templates/`
- Adds example files in each directory that can be customized or deleted

After initialization, customize or remove the generated SKILL.md and example files as needed.

On Work Locally:

- Keep skills in the Manus user skill directory so later tasks on this computer discover them.
- Do not create or edit skills in the directory that contains `skill-creator`. Manus manages it and replaces same-name skills when it syncs. To change one of those skills, edit a copy in the user skill directory.

### Step 4: Edit the Skill

When editing the (newly-generated or existing) skill, remember that the skill is being created for another instance of Manus to use. Include information that would be beneficial and non-obvious to Manus. Consider what procedural knowledge, domain-specific details, or reusable assets would help another Manus instance execute these tasks more effectively.

#### Learn Proven Design Patterns

Consult these helpful guides based on your skill's needs:

- **Multi-step processes**: See `references/workflows.md` for sequential workflows and conditional logic
- **Output formats or quality standards**: See `references/output-patterns.md` for template and example patterns
- **Progressive Disclosure Patterns**: See `references/progressive-disclosure-patterns.md` for splitting content across files.

These files contain established best practices for effective skill design.

#### Start with Reusable Skill Contents

Begin with the `scripts/`, `references/`, and `templates/` files identified in Step 2. This may require user input (e.g., brand assets for `templates/`, documentation for `references/`).

Test added scripts by running them to ensure they work correctly. For many similar scripts, test a representative sample.

Delete any unused example files from initialization.

#### Update SKILL.md

**Writing Guidelines:** Always use imperative/infinitive form.

##### Frontmatter

Write the YAML frontmatter with `name` and `description`:

- `name`: The skill name
- `description`: Primary trigger mechanism. Must include what the skill does AND when to use it (body only loads after triggering).
  - Example: "Document creation and editing with tracked changes. Use for: creating .docx files, modifying content, working with tracked changes."

##### Body

Write instructions for using the skill and its bundled resources.

### Step 5: Delivering the Skill

Once development of the skill is complete, validate and deliver it to the user.

#### Validate the Skill

Run the validation script to ensure the skill meets all requirements. It uses PyYAML when it is installed and otherwise a built-in parser for the usual frontmatter forms. Only when it reports that PyYAML is required, install PyYAML in a task-local virtual environment outside the skill directory and use that interpreter. Do not write your own YAML parser.

```bash
python3 "<skill-creator-root>/scripts/quick_validate.py" --path "<absolute-path-to-skill>"
```

If validation fails, fix the errors and run validation again. The validator rejects the template's `[TODO: ...]` description and repeated frontmatter keys.

A bare skill name, `quick_validate.py <skill-name>`, resolves in the same default directory as `init_skill.py`. Do not use a Desktop or web client type to infer the execution environment. Use the actual runtime path.

#### Package the Skill

On Work Locally, package a delivery archive after validation. On cloud runtimes, skip this step unless the user asks for an archive file, because attaching `SKILL.md` already packages the skill:

```bash
python3 "<skill-creator-root>/scripts/package_skill.py" "<absolute-path-to-skill>" "<absolute-path-to-output>/<skill-name>.skill"
```

Write the archive outside the skill directory, normally in the current working folder. The packager validates the source before it writes, so the archive needs no separate check. It creates a ZIP container whose root contains `SKILL.md`, `scripts/`, `references/`, and other skill files directly, with directory entries such as `references/`. It keeps executable bits, normalizes other permissions, and excludes known cache and temporary files. It rejects unsafe links, special files, path escapes, output paths inside the source, and existing output files.

Use `.skill` for a skill delivery archive. Use `.skill.zip` only when a delivery surface explicitly requires that name. Keep ordinary `.zip` attachments as ordinary attachments. Do not recursively package arbitrary local `SKILL.md` files.

#### Deliver to User

Deliver each skill once, with a single link; linking both the archive and `SKILL.md` shows the skill twice.

- On Work Locally, link only the `.skill` file by its absolute path, for example `[<skill-name>.skill](<absolute-path-to-output>/<skill-name>.skill)`. Manus uploads it and offers it as a skill the user can add to My Skills. A linked `SKILL.md` arrives as a plain file.
- On cloud runtimes, link only `/home/ubuntu/skills/<skill-name>/SKILL.md`; the system packages the skill directory into a skill card. When the user asked for an archive file, link that `.skill` instead of `SKILL.md`.

Do not claim that a skill was saved or installed without a successful result. Do not upload a replacement for a user's installed skill unless the user explicitly requests that operation.

### Step 6: Iterate

After testing the skill, users may request improvements. Often this happens right after using the skill, with fresh context of how the skill performed.

**Iteration workflow:**

1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify how SKILL.md or bundled resources should be updated
4. Implement changes and test again
