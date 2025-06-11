## Taken from https://github.com/alexzhang13/videogamebench

# Hold constants for game-playing agent

DOS_GAME_LITE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>JS-DOS Game Player</title>
    
    <!-- js-dos style sheet -->
    <link rel="stylesheet" href="https://v8.js-dos.com/8.xx/8.3.14/js-dos.css">
    
    <!-- js-dos -->
    <script src="https://v8.js-dos.com/8.xx/8.3.14/js-dos.js"></script>
</head>
<body>
    <div id="dos" style="width: 640px; height: 400px;"></div>
    <script>
        const props = Dos(document.getElementById("dos"), {{
            url: "{game_url}",
            autoStart: true,
        }});
        
        let isDown = false;
        let lastToggleTime = 0;
        
        function togglePause(event) {{
            // Only respond to Shift+PageUp combination
            if (event.key === 'PageUp' && event.shiftKey) {{
                console.log("Toggle pause");
                // Simulate Alt keydown
                document.dispatchEvent(new KeyboardEvent('keydown', {{
                    key: 'Alt',
                    code: 'AltLeft',
                    bubbles: true
                }}));
                
                // Simulate Pause keydown
                document.dispatchEvent(new KeyboardEvent('keydown', {{
                    key: 'Pause',
                    code: 'Pause',
                    altKey: true,
                    bubbles: true
                }}));
                
            }}
        }}

        document.addEventListener('keydown', togglePause);
    </script>
</body>
</html>"""

DOS_GAME_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>JS-DOS Game Player</title>
    
    <!-- js-dos style sheet -->
    <link rel="stylesheet" href="https://v8.js-dos.com/8.xx/8.3.14/js-dos.css">
    
    <!-- js-dos -->
    <script src="https://v8.js-dos.com/8.xx/8.3.14/js-dos.js"></script>
</head>
<body>
    <div id="dos" style="width: 640px; height: 400px;"></div>
    <script>
        const props = Dos(document.getElementById("dos"), {{
            url: "{game_url}",
            autoStart: true,
        }});
    </script>
</body>
</html>"""

### Mapping from game name to game URL
GAME_URL_MAP = {
    "civ": "https://br.cdn.dos.zone/published/br.jzcdse.Civilization.jsdos",
    "lotr2": "http://localhost:8080/lotr2.jsdos",
}

# Keyboard key reference for DOS games
KEYBOARD_KEYS = {
    # Letters
    "A": "KeyA", "B": "KeyB", "C": "KeyC", "D": "KeyD", "E": "KeyE",
    "F": "KeyF", "G": "KeyG", "H": "KeyH", "I": "KeyI", "J": "KeyJ",
    "K": "KeyK", "L": "KeyL", "M": "KeyM", "N": "KeyN", "O": "KeyO",
    "P": "KeyP", "Q": "KeyQ", "R": "KeyR", "S": "KeyS", "T": "KeyT",
    "U": "KeyU", "V": "KeyV", "W": "KeyW", "X": "KeyX", "Y": "KeyY", "Z": "KeyZ",
    
    # Numbers
    "0": "Digit0", "1": "Digit1", "2": "Digit2", "3": "Digit3", "4": "Digit4",
    "5": "Digit5", "6": "Digit6", "7": "Digit7", "8": "Digit8", "9": "Digit9",
    
    # Function keys
    "F1": "F1", "F2": "F2", "F3": "F3", "F4": "F4", "F5": "F5",
    "F6": "F6", "F7": "F7", "F8": "F8", "F9": "F9", "F10": "F10",
    "F11": "F11", "F12": "F12",
    
    # Arrow keys
    "LEFT": "ArrowLeft", "RIGHT": "ArrowRight", "UP": "ArrowUp", "DOWN": "ArrowDown",
    
    # Special keys
    "ENTER": "Enter", "ESC": "Escape", "TAB": "Tab", "SPACE": "Space",
    "BACKSPACE": "Backspace", "DELETE": "Delete", "INSERT": "Insert",
    "HOME": "Home", "END": "End", "PAGEUP": "PageUp", "PAGEDOWN": "PageDown",
    
    # Modifier keys
    "CTRL": "Control", "ALT": "Alt", "SHIFT": "Shift", "META": "Meta",
    
    # Common combinations
    "CTRL+C": "Control+KeyC", "CTRL+V": "Control+KeyV", "CTRL+X": "Control+KeyX",
    "CTRL+A": "Control+KeyA", "CTRL+Z": "Control+KeyZ", "CTRL+S": "Control+KeyS",
    "ALT+F4": "Alt+F4", "CTRL+ALT+DEL": "Control+Alt+Delete"
}
