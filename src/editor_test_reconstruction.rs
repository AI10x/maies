/// The `Editor` struct, contains the state and configuration of the text
/// editor.
pub struct Editor {
    /// If not `None`, the current prompt mode (`Save`, `Find`, `GoTo`, or
    /// `Execute`). If `None`, we are in regular edition mode.
    prompt_mode: Option<PromptMode>,
    /// The current state of the cursor.
    cursor: CursorState,
    /// The padding size used on the left for line numbering.
    ln_pad: usize,
    /// The width of the current window. Will be updated when the window is
    /// resized.
    window_width: usize,
    /// The number of rows that can be used for the editor, excluding the status
    /// bar and the message bar
    screen_rows: usize,
    /// The number of columns that can be used for the editor, excluding the
    /// part used for line numbers
    screen_cols: usize,
    /// The collection of rows, including the content and the syntax
    /// highlighting information.
    rows: Vec<Row>,
    /// Whether the document has been modified since it was open.
    dirty: bool,
    /// The configuration for the editor.
    config: Config,
    /// The number of consecutive times the user has tried to quit without
    /// saving. After `config.quit_times`, the program will exit.
    quit_times: usize,
    /// The file name. If None, the user will be prompted for a file name the
    /// first time they try to save.
    // TODO: It may be better to store a PathBuf instead
    file_name: Option<String>,
    /// The current status message being shown.
    status_msg: Option<StatusMessage>,
    /// The syntax configuration corresponding to the current file's extension.
    syntax: SyntaxConf,
    /// The number of bytes contained in `rows`. This excludes new lines.
    n_bytes: u64,
    /// The copied buffer of a row
    copied_row: Vec<u8>,
    /// Whether to use ANSI color escape codes for rendering
    use_color: bool,
    /// The completion agent process
    completion_agent: Option<std::process::Child>,
    /// Channel to receive completions from the agent
    completion_receiver: Option<std::sync::mpsc::Receiver<String>>,
    /// Current ghost text suggestion
    ghost_text: Option<String>,
    /// Last time a key was pressed, for debounce
    last_keypress: Instant,
}

impl Default for Editor {
    fn default() -> Self {
        Self {
            prompt_mode: None,
            cursor: CursorState::default(),
            ln_pad: 0,
            window_width: 0,
            screen_rows: 0,
            screen_cols: 0,
            rows: Vec::new(),
            dirty: false,
            config: Config::load(),
            quit_times: 0,
            file_name: None,
            status_msg: None,
            syntax: SyntaxConf::default(),
            n_bytes: 0,
            copied_row: Vec::new(),
            use_color: true,
            completion_agent: None,
            completion_receiver: None,
            ghost_text: None,
            last_keypress: Instant::now(),
        }
    }
}

impl Editor {
    fn start_completion_agent(&mut self) {
        use std::process::{Command, Stdio};
        use std::sync::mpsc::channel;
        use std::io::{BufReader, BufRead};

        let (tx, rx) = channel();
        self.completion_receiver = Some(rx);

        let mut cmd = Command::new("./comp/bin/python3");
        cmd.arg("scripts/completion_agent.py")
           .stdin(Stdio::piped())
           .stdout(Stdio::piped())
           .env("AZURE_OPENAI_API_KEY", std::env::var("AZURE_OPENAI_API_KEY").unwrap_or_default())
           .env("AZURE_OPENAI_API_VERSION", std::env::var("AZURE_OPENAI_API_VERSION").unwrap_or_default())
           .env("AZURE_OPENAI_ENDPOINT", std::env::var("AZURE_OPENAI_ENDPOINT").unwrap_or_default());

        let mut child = cmd.spawn().expect("Failed to spawn completion agent");
        let mut stdout = BufReader::new(child.stdout.take().expect("Failed to open agent stdout"));

        std::thread::spawn(move || {
            let mut line = String::new();
            while stdout.read_line(&mut line).is_ok() {
                if !line.is_empty() {
                    let _unused = tx.send(line.clone());
                }
                line.clear();
            }
        });

        self.completion_agent = Some(child);
    }
}
