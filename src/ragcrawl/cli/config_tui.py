"""Textual TUI for ragcrawl configuration."""

from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Static,
)

from ragcrawl.config.user_config import UserConfig, UserConfigManager


class ConfirmDialog(ModalScreen[bool]):
    """A confirmation dialog."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }

    ConfirmDialog > Container {
        width: 50;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    ConfirmDialog .dialog-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    ConfirmDialog .dialog-message {
        text-align: center;
        margin-bottom: 1;
    }

    ConfirmDialog Horizontal {
        align: center middle;
        height: auto;
    }

    ConfirmDialog Button {
        margin: 0 1;
    }
    """

    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self.dialog_title = title
        self.message = message

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(self.dialog_title, classes="dialog-title")
            yield Label(self.message, classes="dialog-message")
            with Horizontal():
                yield Button("Yes", variant="error", id="yes")
                yield Button("No", variant="primary", id="no")

    @on(Button.Pressed, "#yes")
    def confirm(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def cancel(self) -> None:
        self.dismiss(False)


class ConfigField(Horizontal):
    """A single configuration field with label and input."""

    DEFAULT_CSS = """
    ConfigField {
        height: 3;
        margin: 0 0 1 0;
        padding: 0;
    }

    ConfigField .field-label {
        width: 20;
        height: 3;
        content-align: left middle;
        text-style: bold;
    }

    ConfigField Input {
        width: 1fr;
    }
    """

    def __init__(
        self,
        key: str,
        label: str,
        value: str,
        placeholder: str = "",
    ) -> None:
        super().__init__()
        self.key = key
        self.label_text = label
        self.value = value
        self.placeholder = placeholder or f"Enter {label.lower()}"

    def compose(self) -> ComposeResult:
        yield Label(self.label_text, classes="field-label")
        yield Input(
            value=self.value,
            id=f"input-{self.key}",
            placeholder=self.placeholder,
        )


class ConfigSection(Vertical):
    """A section of configuration options."""

    DEFAULT_CSS = """
    ConfigSection {
        height: auto;
        margin: 0 0 1 0;
        padding: 1;
        border: solid $primary;
        background: $surface-darken-1;
    }

    ConfigSection .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    """

    def __init__(self, title: str) -> None:
        super().__init__()
        self.title = title

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="section-title")


class ConfigTUI(App[None]):
    """Textual app for editing ragcrawl configuration."""

    CSS = """
    Screen {
        align: center middle;
        background: $background;
    }

    #main-container {
        width: 80;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: solid $primary;
    }

    .config-header {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .config-path {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    #button-bar {
        height: auto;
        align: center middle;
        margin-top: 1;
        padding-top: 1;
        border-top: solid $primary-darken-2;
    }

    #button-bar Button {
        margin: 0 1;
    }

    #status-bar {
        height: 1;
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }

    #status-bar.success {
        color: $success;
    }

    #status-bar.error {
        color: $error;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+r", "reset", "Reset"),
        Binding("escape", "quit", "Quit"),
    ]

    TITLE = "ragcrawl Configuration"

    def __init__(self) -> None:
        super().__init__()
        self.config_manager = UserConfigManager()
        self.config = self.config_manager.load()
        self.has_changes = False

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-container"):
            yield Label("⚙  ragcrawl Configuration", classes="config-header")
            yield Label(
                f"{self.config_manager.config_file}",
                classes="config-path",
            )

            # Storage Section
            with ConfigSection("Storage"):
                yield ConfigField(
                    key="storage_dir",
                    label="Storage Directory",
                    value=str(self.config.storage_dir),
                    placeholder="~/.ragcrawl",
                )
                yield ConfigField(
                    key="db_name",
                    label="Database Name",
                    value=self.config.db_name,
                    placeholder="ragcrawl.duckdb",
                )

            # HTTP Settings Section
            with ConfigSection("HTTP"):
                yield ConfigField(
                    key="user_agent",
                    label="User Agent",
                    value=self.config.user_agent,
                    placeholder="ragcrawl/0.1",
                )
                yield ConfigField(
                    key="timeout",
                    label="Timeout (sec)",
                    value=str(self.config.timeout),
                    placeholder="30",
                )
                yield ConfigField(
                    key="max_retries",
                    label="Max Retries",
                    value=str(self.config.max_retries),
                    placeholder="3",
                )

            # Crawl Defaults Section
            with ConfigSection("Crawl Defaults"):
                yield ConfigField(
                    key="default_max_pages",
                    label="Max Pages",
                    value=str(self.config.default_max_pages),
                    placeholder="100",
                )
                yield ConfigField(
                    key="default_max_depth",
                    label="Max Depth",
                    value=str(self.config.default_max_depth),
                    placeholder="5",
                )

            with Horizontal(id="button-bar"):
                yield Button("Save", variant="success", id="save-btn")
                yield Button("Reset", variant="warning", id="reset-btn")
                yield Button("Quit", variant="default", id="quit-btn")

            yield Static("Ctrl+S Save · Ctrl+R Reset · Esc Quit", id="status-bar")

        yield Footer()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Track when inputs change."""
        self.has_changes = True
        self.update_status("● Unsaved changes", "")

    def update_status(self, message: str, status_class: str) -> None:
        """Update the status bar."""
        status = self.query_one("#status-bar", Static)
        status.update(message)
        status.remove_class("success", "error")
        if status_class:
            status.add_class(status_class)

    def get_field_values(self) -> dict:
        """Get current values from all input fields."""
        values = {}
        for field in self.query(ConfigField):
            input_widget = field.query_one(Input)
            values[field.key] = input_widget.value
        return values

    def validate_and_save(self) -> bool:
        """Validate inputs and save configuration."""
        values = self.get_field_values()

        try:
            # Type conversions
            int_keys = {"timeout", "max_retries", "default_max_pages", "default_max_depth"}

            for key, value in values.items():
                if key in int_keys:
                    try:
                        values[key] = int(value)
                    except ValueError:
                        self.update_status(f"✗ Invalid number: {key}", "error")
                        return False
                elif key == "storage_dir":
                    path = Path(value).expanduser().resolve()
                    values[key] = path

            # Create new config
            new_config = UserConfig(**values)

            # Ensure storage directory exists
            new_config.ensure_storage_dir()

            # Save
            self.config_manager.save(new_config)
            self.config = new_config
            self.has_changes = False

            self.update_status("✓ Saved successfully", "success")
            return True

        except Exception as e:
            self.update_status(f"✗ Error: {e}", "error")
            return False

    def reset_to_defaults(self) -> None:
        """Reset all fields to default values."""
        default_config = UserConfig()

        # Update all input fields
        field_values = {
            "storage_dir": str(default_config.storage_dir),
            "db_name": default_config.db_name,
            "user_agent": default_config.user_agent,
            "timeout": str(default_config.timeout),
            "max_retries": str(default_config.max_retries),
            "default_max_pages": str(default_config.default_max_pages),
            "default_max_depth": str(default_config.default_max_depth),
        }

        for field in self.query(ConfigField):
            if field.key in field_values:
                input_widget = field.query_one(Input)
                input_widget.value = field_values[field.key]

        self.has_changes = True
        self.update_status("● Reset to defaults (unsaved)", "")

    @on(Button.Pressed, "#save-btn")
    def on_save_button(self) -> None:
        """Handle save button click."""
        self.validate_and_save()

    @on(Button.Pressed, "#reset-btn")
    def on_reset_button(self) -> None:
        """Handle reset button click."""
        def handle_confirm(result: bool) -> None:
            if result:
                self.reset_to_defaults()

        self.push_screen(
            ConfirmDialog(
                "Reset Configuration",
                "Reset all settings to defaults?"
            ),
            handle_confirm,
        )

    @on(Button.Pressed, "#quit-btn")
    def on_quit_button(self) -> None:
        """Handle quit button click."""
        self.action_quit()

    def action_save(self) -> None:
        """Save action (Ctrl+S)."""
        self.validate_and_save()

    def action_reset(self) -> None:
        """Reset action (Ctrl+R)."""
        def handle_confirm(result: bool) -> None:
            if result:
                self.reset_to_defaults()

        self.push_screen(
            ConfirmDialog(
                "Reset Configuration",
                "Reset all settings to defaults?"
            ),
            handle_confirm,
        )

    def action_quit(self) -> None:
        """Quit action."""
        if self.has_changes:
            def handle_confirm(result: bool) -> None:
                if result:
                    self.exit()

            self.push_screen(
                ConfirmDialog(
                    "Unsaved Changes",
                    "Quit without saving?"
                ),
                handle_confirm,
            )
        else:
            self.exit()


def run_config_tui() -> None:
    """Run the configuration TUI."""
    app = ConfigTUI()
    app.run()


if __name__ == "__main__":
    run_config_tui()
