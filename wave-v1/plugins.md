# Task guidance

Write a HTML page that will be loaded into iframe on a device with a screen, no mouse and some special layout integrated keyboard.

Parent frame has a connection to a telegram chat and to special 7-segment clock, it will manage all stuff, you just need to communicate with it via postMessage. Your code will run in a sandboxed iframe with `sandbox="allow-scripts"`.

Please keep code small enough but not smaller that it should be. Prioritize fast answer if it not hurts usability and code correctness. Add small instructions on what keys meaning is. Therefore not add comments they dont needed.

# Plugin Architecture

Plugins are loaded into an iframe by the parent frame. The parent handles:
- Telegram bot long-polling and message processing
- WebHID communication with 7-segment display hardware
- Key overlay display (big bouncing text on keypress)
- Admin commands: `/on`, `/off`, `/reload`, `/plugin <name|url>`

Plugins can be switched at runtime via `/plugin` command. Registered plugins are defined in parent's `PLUGINS` object with default key display settings.

# Receiving Messages (Parent → Plugin)

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

# Sending Messages (Plugin → Parent)

```javascript
function sendToParent(msg) {
  window.parent.postMessage(msg, '*');
}
```

**Key Display Control**
```javascript
// Enable/disable the key overlay in parent, it will display all pressed keys in a big, overlapping bounce
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

# Keypress Mapping

Raw key values are mapped to descriptions by parent:

| Raw Key | Description |
|---------|-------------|
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

Use `msg.description` for logical key handling:
```javascript
case 'keypress':
  if (msg.description === 'START') { /* Enter pressed */ }
  if (msg.description === 'PLUS') { /* + pressed */ }
  break;
```

# Keyboard

┌──────────────────────────────────────────┐
│                                          │
│  [ COOK ]                                │
│                                          │
├──────────────────────────────────────────┤
│                                          │
│  [ DEFROST ]                             │
│                                          │
├──────────────────────────────────────────┤
│                                          │
│  [ REHEAT ]                              │
│                                          │
├──────────────────────────────────────────┤
│                                          │
│  ┌─────────┐ ┌────────────┐ ┌─────────┐  │
│  │  WAVES  │ │  ELEMENTS  │ │  PLUS   │  │
│  │  TIME   │ │            │ │  MINUS  │  │
│  └─────────┘ └────────────┘ └─────────┘  │
│                                          │
├──────────────────────────────────────────┤
│  [ TEN_MIN ]  [ ONE_MIN ]  [ TEN_SEC ]   │
├──────────────────────────────────────────┤
│                                          │
│  [  STOP  ]                 [  START  ]  │
│                                          │
└──────────────────────────────────────────┘

# Plugin Template

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Plugin Name</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body {
      width: 100%;
      height: 100%;
      background: #000;
      color: #fff;
      overflow: hidden;
      font-family: sans-serif;
    }
  </style>
</head>
<body>
  <div id="app"></div>
  <script>
    let displayEnabled = true;

    function sendToParent(msg) {
      window.parent.postMessage(msg, '*');
    }

    window.addEventListener('message', (event) => {
      const msg = event.data;
      if (!msg || !msg.type) return;

      switch (msg.type) {
        case 'init':
          // msg.chatName, msg.keepAspectRatio available
          break;
        case 'displayOn':
          displayEnabled = true;
          break;
        case 'displayOff':
          displayEnabled = false;
          break;
        case 'keypress':
          // Use msg.description for mapped keys (COOK, START, etc)
          // Use msg.key for raw key value
          break;
        case 'media':
          // msg.photoUrl or msg.videoUrl, msg.sender, msg.isAdmin
          break;
        case 'command':
          // msg.text (full command), msg.sender, msg.isAdmin
          // msg.chatId, msg.messageId (for reactions)
          break;
      }
    });
  </script>
</body>
</html>
```

# Key Display Mode

Key display shows pressed keys as large overlay text in parent frame. Games should disable it for cleaner UX:

```javascript
// Disable key overlay (recommended for games)
sendToParent({ type: 'keyDisplayMode', enabled: false });

// Re-enable when leaving game mode
sendToParent({ type: 'keyDisplayMode', enabled: true });
```

Registered plugins set default via `keyDisplay` in PLUGINS config. Media plugin defaults to `true`, games should default to `false`.

# Command Handling Pattern

Handle telegram `/commands` sent to your plugin:

```javascript
case 'command':
  if (msg.text === '/start') {
    startGame();
    sendToParent({ type: 'reaction', chatId: msg.chatId, messageId: msg.messageId, emoji: '🎮' });
  }
  if (msg.text.startsWith('/score ')) {
    const value = msg.text.substring(7);
    // process value...
  }
  break;
```

# 7-Segment Display Details

**Running Text** - Scrolls text on hardware display. Max 46 chars. Supports ASCII and Cyrillic.

**Raw Mode** - Direct control over 4 digits (0-127 each) and symbol segments (0-4095 bitmask).

```javascript
// Display "1234" with specific segments
sendToParent({
  type: 'hid',
  command: 'raw',
  digits: [1, 2, 3, 4],  // Each 0-127
  symbols: 0b000000000001  // 12-bit bitmask
});
```

# Task

Make a snake game
