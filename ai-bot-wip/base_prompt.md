# Task guidance

Write a HTML page that will be loaded into iframe on a device with a screen, no mouse and some special layout integrated keyboard.

Parent frame has a connection to a special 7-segment clock, it will manage all stuff, you just need to communicate with it via postMessage. Your code will run in a sandboxed iframe with `sandbox="allow-scripts"`.

Please keep code small enough but not smaller that it should be. Prioritize fast answer if it not hurts usability and code correctness. Do not write comments. When doing application add a simple educational info on which buttons to press on a HID keyboard.

Your iframe is fixed 1286 x 768.

# Plugin Architecture

Plugins are loaded into an iframe by the parent frame. The parent handles:
- WebHID communication with 7-segment display hardware

# Receiving Messages (Parent → Plugin)

```javascript
window.addEventListener('message', (event) => {
  const msg = event.data;
  if (!msg || !msg.type) return;

  switch (msg.type) {
    case 'error':
      // msg.message - string, error to display
      break;
    case 'keypress':
      // msg.key - string, raw key value (e.g., 'Enter', 'c')
      // msg.description - string|null, mapped name (e.g., 'START', 'COOK')
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

**WebHID Commands**
```javascript
// Send running text to hardware display
window.parent.postMessage({
  type: 'hid',
  command: 'runningText',
  text: 'Hello World'
}, '*');

// Send raw display data
window.parent.postMessage({
  type: 'hid',
  command: 'raw',
  digits: [0, 0, 0, 0],  // 4 values, 0-127 each
  symbols: 0              // 0-4095
}, '*');
```

# Keyboard

Use `msg.description` for logical key handling:
```javascript
case 'keypress':
  if (msg.description === 'START') { /* Enter pressed */ }
  if (msg.description === 'PLUS') { /* + pressed */ }
  break;
```

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
    function sendToParent(msg) {
      window.parent.postMessage(msg, '*');
    }

    window.addEventListener('message', (event) => {
      const msg = event.data;
      if (!msg || !msg.type) return;

      switch (msg.type) {
        case 'keypress':
          // Use msg.description for mapped keys (COOK, START, etc)
          // Use msg.key for raw key value
          break;
      }
    });
  </script>
</body>
</html>
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

