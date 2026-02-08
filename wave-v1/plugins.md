# HardWave Display Plugins

Plugins are sandboxed HTML pages loaded in an iframe that handle display and user interaction. The parent frame manages all sensitive operations (Telegram API, WebHID, credentials) while plugins focus purely on presentation.

## Security Model

Plugins are treated as **untrusted code**. They run in a sandboxed iframe with `sandbox="allow-scripts"`:

- No access to parent's DOM or JavaScript context
- No access to `localStorage`, `sessionStorage`, or cookies
- No access to parent URL or query parameters (API keys stay hidden)
- Cannot make same-origin requests
- All communication happens via `postMessage`

## Communication Protocol

### Receiving Messages (Parent → Plugin)

```javascript
window.addEventListener('message', (event) => {
  const msg = event.data;
  if (!msg || !msg.type) return;

  switch (msg.type) {
    case 'init':
      // msg.chatName - string, chat identifier to display
      // msg.keepAspectRatio - boolean, initial aspect ratio preference
      break;
    case 'error':
      // msg.message - string, error to display
      break;
    case 'displayOn':
      // Display has been enabled by admin
      break;
    case 'displayOff':
      // Display has been disabled by admin
      break;
    case 'keypress':
      // msg.key - string, raw key value (e.g., 'Enter', 'c')
      // msg.description - string|null, mapped name (e.g., 'START', 'COOK')
      break;
    case 'media':
      // msg.photoUrl - string|undefined, direct URL to photo
      // msg.videoUrl - string|undefined, direct URL to video
      // msg.sender - string, formatted sender name
      // msg.isAdmin - boolean, whether sender is admin
      break;
    case 'command':
      // msg.text - string, full command text (starts with '/')
      // msg.sender - string, formatted sender name
      // msg.isAdmin - boolean, whether sender is admin
      // msg.chatId - number, for sending reactions
      // msg.messageId - number, for sending reactions
      break;
    case 'hidResult':
      // msg.command - string, which command completed
      // msg.success - boolean, whether it succeeded
      // msg.error - string|undefined, error message if failed
      break;
  }
});
```

### Sending Messages (Plugin → Parent)

```javascript
function sendToParent(msg) {
  window.parent.postMessage(msg, '*');
}
```

#### Available Message Types

**Key Display Control**
```javascript
// Enable/disable the key overlay in parent
sendToParent({ type: 'keyDisplayMode', enabled: true });
```

**WebHID Commands**
```javascript
// Send running text to hardware display
sendToParent({
  type: 'hid',
  command: 'runningText',
  text: 'Hello World'
});

// Send raw display data
sendToParent({
  type: 'hid',
  command: 'raw',
  digits: [0, 0, 0, 0],  // 4 values, 0-127 each
  symbols: 0              // 0-4095
});
```

**Telegram Reactions**
```javascript
// Send emoji reaction to a message
sendToParent({
  type: 'reaction',
  chatId: 123456789,
  messageId: 42,
  emoji: '👀'
});
```

## Key Mapping

The parent maps hardware button presses to descriptive names:

| Key | Description |
|-----|-------------|
| `c`, `C` | COOK |
| `d`, `D` | DEFROST |
| `r`, `R` | REHEAT |
| `w`, `W` | WAVES |
| `t`, `T` | TIME |
| `e`, `E` | ELEMENTS |
| `+` | PLUS |
| `-` | MINUS |
| `z`, `Z` | TEN_MIN |
| `y`, `Y` | ONE_MIN |
| `x`, `X` | TEN_SEC |
| `Escape` | STOP |
| `Enter` | START |

Plugins receive both `key` (raw) and `description` (mapped name or null).

## Writing a Plugin

### Minimal Example

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>My Plugin</title>
  <style>
    body {
      margin: 0;
      background: #000;
      color: #fff;
      font-family: sans-serif;
    }
  </style>
</head>
<body>
  <div id="content">Loading...</div>

  <script>
    const contentEl = document.getElementById('content');

    window.addEventListener('message', (event) => {
      const msg = event.data;
      if (!msg || !msg.type) return;

      switch (msg.type) {
        case 'init':
          contentEl.textContent = 'Ready: ' + msg.chatName;
          // Enable key display overlay
          window.parent.postMessage({ type: 'keyDisplayMode', enabled: true }, '*');
          break;
        case 'media':
          if (msg.photoUrl) {
            contentEl.innerHTML = `<img src="${msg.photoUrl}" style="max-width:100%">`;
          }
          break;
      }
    });
  </script>
</body>
</html>
```

### Best Practices

1. **Always handle `init`** - This is when you receive configuration and should set up your UI.

2. **Enable key display if needed** - Send `keyDisplayMode` message during init if you want the key overlay.

3. **Handle `displayOn`/`displayOff`** - Respect admin control over display visibility.

4. **Don't assume message order** - Messages may arrive in any order; handle missing data gracefully.

5. **Use `description` for key handling** - Prefer checking `msg.description === 'START'` over `msg.key === 'Enter'` for hardware button actions.

6. **Request reactions via parent** - Never try to call Telegram API directly; send reaction requests to parent.

7. **Keep state minimal** - The parent handles persistence; plugins should be stateless where possible.

### Registering a Plugin

Add your plugin to the `PLUGINS` registry in `index.html`:

```javascript
const PLUGINS = {
  'media': 'plugin-media-display.html',
  'my-plugin': 'plugin-my-plugin.html',
};
```

### Loading Plugins via Telegram

Use the `/plugin` command (admin-only):

```
/plugin              - List available plugins (current marked with *)
/plugin media        - Load plugin by name
/plugin https://...  - Load plugin from URL (untrusted)
```

When loading by name, the path is resolved from the `PLUGINS` registry. When loading by URL, the URL is used directly (useful for testing external plugins).

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Parent (index.html)                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Telegram API │  │   WebHID     │  │  Key Display │       │
│  │  - Polling   │  │  - Commands  │  │  - Overlay   │       │
│  │  - Reactions │  │  - Time sync │  │  - Mapping   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │                │
│         └────────────┬────┴─────────────────┘                │
│                      │                                       │
│              postMessage (filtered data)                     │
│                      ▼                                       │
├─────────────────────────────────────────────────────────────┤
│              iframe sandbox="allow-scripts"                  │
│                      │                                       │
│                      ▼                                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Plugin (untrusted)                      │    │
│  │                                                      │    │
│  │  - Receives: media URLs, commands, keypresses       │    │
│  │  - Sends: HID requests, reactions, display mode     │    │
│  │  - No access to: API keys, parent URL, localStorage │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```
