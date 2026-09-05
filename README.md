<!--
SPDX-FileCopyrightText: 2020 Ilaï Deutel & Kibi Contributors
SPDX-License-Identifier: MIT or Apache-2.0
-->

# Maies

Maies is a minimalist, terminal-based text editor with optional AI-assisted
completion. It is based on [Kibi](https://github.com/ilai-deutel/kibi) and keeps
Kibi's compact Rust editor core, UTF-8 support, search, syntax highlighting, and
cross-platform terminal support while adding ghost-text completion and text
selection.

The package and executable are still named `kibi` so the fork remains close to
its upstream foundation. The project itself is documented here as Maies.

## What It Does

Maies provides:

- Terminal editing on Linux, macOS, Windows 10+, and WASI
- UTF-8 text handling and horizontal/vertical scrolling
- Incremental search and go-to-line navigation
- Configurable line numbers, tab width, quit confirmation, and status messages
- File-extension-based syntax highlighting
- Row copy, cut, paste, duplication, deletion, and comment toggling
- Shift-arrow text selection with replacement and deletion
- External command execution with output inserted into the document
- Optional OpenAI or Azure OpenAI completions shown as gray ghost text on
  Linux and macOS

AI completion is disabled unless `--ai`, `--system-prompt`, or
`--system-prompt-file` is passed. Normal editing does not require Python,
network access, or API credentials.

## Install

### Requirements

- A Rust toolchain compatible with the version in `Cargo.toml`
- A terminal with ANSI escape-sequence support
- Python 3.8+ only when using AI completion

Build Maies from this repository:

```bash
git clone https://github.com/AI10x/maies.git
cd maies
cargo build --release
./target/release/kibi --version
```

To install the `kibi` executable from this fork into Cargo's binary directory:

```bash
cargo install --git https://github.com/AI10x/maies.git --locked
```

Do not use `cargo install kibi` when you want Maies; that command installs the
upstream Kibi crate from crates.io.

## How To Use It

Open an empty buffer or an existing file:

```bash
kibi
kibi path/to/file.rs
kibi -- --file-name-starting-with-a-dash
```

Type normally, use arrow keys to move, press `Ctrl+S` to save, and press
`Ctrl+Q` to quit. Unsaved changes require repeated quit confirmation according
to `quit_times` in the configuration file.

### Selection And Clipboard

Hold Shift while pressing an arrow key to select text. Selected text is shown
with inverse video. Typing, Backspace, Delete, Enter, or Tab replaces or removes
the selection.

The current clipboard is row-oriented rather than a system clipboard:

- `Ctrl+C` copies the entire current row.
- `Ctrl+X` cuts the entire current row.
- `Ctrl+V` inserts the copied row below the cursor.

Copy and cut do not currently copy only the highlighted selection.

### AI Completion

AI completion runs through the embedded `scripts/completion_agent.py` helper.
Install its optional dependency in a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-ai.txt
export MAIES_PYTHON="$PWD/.venv/bin/python"
```

If you installed only the executable rather than cloning the repository, install
the optional dependency directly with `python3 -m pip install "openai>=1,<2"`.

For OpenAI, configure a model and API key:

```bash
export OPENAI_API_KEY="your-api-key"
export MAIES_AI_MODEL="gpt-4.1-mini"
kibi --ai path/to/file.rs
```

For Azure OpenAI, configure the Azure endpoint, API version, key, and deployment
name:

```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_API_VERSION="your-api-version"
export MAIES_AI_MODEL="your-deployment-name"
kibi --ai path/to/file.rs
```

`OPENAI_BASE_URL` can point the standard OpenAI client at a compatible API.
`DEPLOYMENT_NAME` is accepted as a fallback when `MAIES_AI_MODEL` is unset.

After editing pauses for 500 ms at the end of a line, Maies sends up to the
previous 100 lines and the current line prefix to the configured provider. The
first line of the response appears as gray ghost text:

- Press Tab to insert the full suggestion, including additional lines.
- Press any other editing or navigation key to dismiss the suggestion.
- Continue typing at a new position to request another suggestion.

Use a custom system prompt directly:

```bash
kibi --ai --system-prompt "Return only a concise code continuation." path/to/file.rs
```

Or load a prompt from a file:

```bash
kibi --ai --system-prompt-file /absolute/path/to/prompt.txt path/to/file.rs
```

The equivalent environment variables are `MAIES_SYSTEM_PROMPT` and
`MAIES_SYSTEM_PROMPT_FILE`. Prompt precedence is command-line prompt file,
command-line prompt, environment prompt file, environment prompt, then the
built-in completion prompt.

> **Privacy:** AI mode sends document context to the configured OpenAI-compatible
> service. Do not enable it for source or text that you are not permitted to
> share. AI mode is opt-in so opening a file normally never sends its contents.

## Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+S` | Save, prompting for a path for a new buffer |
| `Ctrl+Q` | Quit, with confirmation for unsaved changes |
| `Ctrl+F` | Incremental search; arrows move between matches |
| `Ctrl+G` | Go to `line[:column]` |
| `Ctrl+D` | Duplicate the current row |
| `Ctrl+R` | Remove the current row |
| `Ctrl+C` | Copy the current row to the internal clipboard |
| `Ctrl+X` | Cut the current row to the internal clipboard |
| `Ctrl+V` | Paste the copied row below the cursor |
| `Ctrl+E` | Run an external command and insert its standard output |
| `Ctrl+/` | Comment or uncomment the current row when supported |
| `Ctrl+Left` | Move to the previous word |
| `Ctrl+Right` | Move to the next word |
| `Shift+Arrow` | Extend a text selection |
| `Escape` | Clear the current selection |
| `Tab` | Accept ghost text, or insert a tab when none is visible |

## Configuration

The editor reads an INI-style `config.ini`:

```ini
# Number of columns represented by a tab; must be greater than zero.
tab_stop=4
# Quit attempts required when the buffer has unsaved changes.
quit_times=2
# Seconds for which status messages remain visible.
message_duration=3
# Display line numbers when the terminal is wide enough.
show_line_numbers=true
```

Configuration locations:

| Platform | User configuration |
| --- | --- |
| Linux/macOS | `$XDG_CONFIG_HOME/kibi/config.ini` or `~/.config/kibi/config.ini` |
| Windows | `%APPDATA%\Kibi\config.ini` |

On Linux and macOS, system configuration is also searched under
`$XDG_CONFIG_DIRS/kibi`, `/etc/xdg/kibi`, and `/etc/kibi`.

### Syntax Highlighting

Language definitions are INI files in `syntax.d/`. Maies chooses a definition by
matching the opened file's extension. Install the definitions for a source
checkout with:

```bash
mkdir -p ~/.local/share/kibi
ln -s "$PWD/syntax.d" ~/.local/share/kibi/syntax.d
```

User syntax directories are `$XDG_DATA_HOME/kibi/syntax.d` or
`~/.local/share/kibi/syntax.d` on Linux/macOS and
`%APPDATA%\Kibi\syntax.d` on Windows.

`cargo install` installs only the executable. If you did not keep a source
checkout, download the definitions separately:

```bash
git clone --depth 1 https://github.com/AI10x/maies.git /tmp/maies
mkdir -p ~/.local/share/kibi
cp -R /tmp/maies/syntax.d ~/.local/share/kibi/syntax.d
```

Each language file can define extensions, number highlighting, string and
comment delimiters, and two keyword classes. See `syntax.d/rust.ini` for a full
example.

## How The Source Is Organized

Maies is a Rust binary with a small library facade. Most behavior is deliberately
kept in direct data structures and functions rather than a large framework.

| Path | Responsibility |
| --- | --- |
| `src/main.rs` | Parses command-line options and starts the editor. |
| `src/lib.rs` | Exposes the supported library entry points and selects platform modules. |
| `src/editor.rs` | Owns editor state, the input loop, editing commands, prompts, rendering coordination, selection, and AI process lifecycle. |
| `src/row.rs` | Stores raw row bytes, rendered text, byte-to-screen-column maps, and per-character highlighting. |
| `src/syntax.rs` | Parses language definitions and assigns syntax highlight classes. |
| `src/config.rs` | Loads and validates global INI configuration. |
| `src/terminal.rs` | Provides terminal-size fallback and terminal restoration. |
| `src/unix.rs` | Implements UNIX raw mode, resize signals, and paths. |
| `src/windows.rs` | Implements Windows console modes and paths. |
| `src/wasi.rs` | Supplies the WASI platform adapter. |
| `src/xdg.rs` | Resolves XDG configuration and data directories. |
| `scripts/completion_agent.py` | Connects the Rust editor to OpenAI or Azure OpenAI. |
| `syntax.d/` | Contains language-specific highlighting definitions. |
| `tests/cli.rs` | Exercises command-line parsing and process exit behavior. |
| `fuzz/` | Fuzzes configuration loading. |
| `ci/` and `.github/workflows/` | Build, test, security, and release automation inherited from Kibi. |

### Editing And Rendering Flow

1. `main.rs` parses a file path and optional AI settings.
2. `editor.rs` enters raw terminal mode and loads the document into `Vec<Row>`.
3. Terminal bytes are decoded into logical keys such as arrows, Delete, and
   control-key commands.
4. Each key mutates the editor state and affected rows.
5. `Row::update` rebuilds rendered text, UTF-8/display-column mappings, and
   syntax highlighting.
6. The editor composes rows, status information, messages, selections, and ghost
   text into one ANSI output buffer and writes it to the alternate screen.
7. Saving serializes the row byte buffers with newline separators.

The editor stores cursor positions as byte offsets because document rows are
`Vec<u8>`. `Row` separately maps those byte positions to rendered terminal
columns, accounting for UTF-8 character width and expanded tabs.

### AI Completion Flow

1. AI mode starts only after explicit opt-in.
2. After a short idle period at the end of a row, Rust builds a bounded context.
3. Rust starts the embedded Python helper using `MAIES_PYTHON` or `python3`.
4. Requests and responses use request IDs and byte lengths, preserving multiline
   whitespace without relying on sentinel text.
5. A background reader returns the response to the editor through a channel.
6. The editor accepts the response only if its request ID and document context
   are still current, preventing stale suggestions from being displayed.
7. Provider and process failures are displayed in the status bar.

## Development

Run the standard checks from the repository root:

```bash
cargo test --locked
cargo fmt --check --all
cargo clippy --locked --all-targets
python3 -m py_compile scripts/completion_agent.py
cargo package --allow-dirty
```

The original Kibi project limited production Rust to 1,024 lines. Maies has
intentionally moved beyond that constraint to support selection and AI process
coordination, so the upstream line-count gate is not part of this fork's quality
policy.

## Troubleshooting

- `Could not start AI agent`: set `MAIES_PYTHON` to a Python executable where
  `requirements-ai.txt` is installed.
- `AI agent stopped`: run the configured Python manually and verify that the
  `openai` package and required environment variables are available.
- Authentication or deployment errors: verify the API key, endpoint, API
  version, and `MAIES_AI_MODEL` value for the selected provider.
- No syntax highlighting: install or link `syntax.d` into the appropriate data
  directory.
- Garbled terminal after an abnormal exit: run `reset` on UNIX-like systems.
- AI completion is currently supported on Linux and macOS. The core editor also
  builds for Windows and WASI, but their blocking input implementations do not
  yet wake the display when an asynchronous suggestion arrives.

## Upstream And License

Maies is derived from Kibi, created by Ilaï Deutel and the
[Kibi contributors](https://github.com/ilai-deutel/kibi#contributors). The
upstream project was inspired by Salvatore Sanfilippo's
[`kilo`](https://github.com/antirez/kilo).

The project is available under either of these licenses, at your option:

- [Apache License 2.0](LICENSE-APACHE)
- [MIT License](LICENSE-MIT)
