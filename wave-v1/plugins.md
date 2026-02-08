# Task guidance

Write a HTML page that will be loaded into iframe on a device with a screen, no mouse and some special layout integrated keyboard.

Parent frame has a connection to a telegram chat and to special 7-segment clock, it will manage all stuff, you just need to communicate with it via postMessage. Your code will run in a sandboxed iframe with `sandbox="allow-scripts"`.

Please keep code small enough but not smaller that it should be. Prioritize fast answer if it not hurts usability and code correctness. Add small instructions on what keys meaning is.

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

# Task

Make a snake game
