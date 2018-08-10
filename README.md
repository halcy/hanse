# HANSE
Halcy's Ansi Editor

Currently it doesn't do very much, but you can load .ans files, save .ans files, export to PNG and do some basic drawing (with the keyboard) and editing.

Basic controls:
  * Move cursor by clicking mouse or with arrow keys
  * Select foreground colour with left-click on palette, background colour with right-click
  * Select character by clicking into the character palette, insert it with enter (or doubleclick)
  * Right-click image to pick colours and character from image
  * F1-12 insert the characters shown in bottom bar
  * Use mouse or shift+arrow keys to select areas
    * Hold ctrl while selecting to add to exising selection - selections can be nonsquare
    * Hold ctrl+alt to subtract from selection
  * ctrl+c copies, ctrl-x cuts, ctrl-v pastes (only internally, not proper clipboard)
  * home/end work as "smart home/end" in editors usually does
  * del/ins delete / insert after the cursor
    * shift+del/ins delete/insert an entire column
    * ctrl+del/ins delete/insert in row direction, ctrl+shift+del/ins entire rows
    * del while there is a selection deletes contents of selection
  * ctrl+z/ctrl+y undo/redo
  
The Ansi(Whatever).py files can be used without Qt or any gui stuff whatsoever to read, write, manipulate and render .ans files.

Requires Numpy, PIL, PyQt5. Works on Linux and Windows.
