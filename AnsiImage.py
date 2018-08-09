import numpy as np
from PIL import Image
import copy

class AnsiImage:
    """
    Manages a rectangular image made of ansi character cells
    """
    
    CHAR_SIZE_X = 8
    CHAR_SIZE_Y = 16
    
    def __init__(self, min_line_len = None):
        """
        Optionally allows the specification of a minimum
        line length, used when loading
        """
        self.min_line_len = min_line_len
        self.ansi_image = []
        self.width = 0
        self.height = 0
        self.cursor_x = 0
        self.cursor_y = 0
        self.is_dirty = False
        
        # Selection related stuff
        self.selection = None
        self.selection_preliminary = set()
        self.selection_preliminary_remove = set()
        
        # The cursor
        self.cursor_shape = []
        for y in [0, 1, 14, 15]:
            for x in range(0, 8):
                self.cursor_shape.append((y, x))
        for y in range(2, 14):
            for x in [0, 1, 6, 7]:
                self.cursor_shape.append((y, x))
    
    def change_size(self, new_height, new_width):
        """
        Make the image larger or smaller, retaining contents
        """
        copy_width = min(self.width, new_width)
        copy_height = min(self.height, new_height)
        old_image = copy.deepcopy(self.ansi_image)
        self.clear_image(new_width, new_height)
        for y in range(copy_height):
            for x in range(copy_width):
               self.ansi_image[y][x] = old_image[y][x]
               
    def has_selection(self):
        """
        True if a selection exists, False if no
        """
        if self.selection == None or len(self.selection) == 0:
            return False
        return True
    
    def set_selection(self, new_selection_initial = None, append = False, remove = False, preliminary = False):
        """
        Sets the selection list
        """
        self.selection_preliminary = set()
        self.selection_preliminary_remove = set()
        if new_selection_initial != None:
            new_selection = []
            for entry in new_selection_initial:
                if entry[0] < 0 or entry[0] >= self.width or entry[1] < 0 or entry[1] >= self.height:
                    continue
                new_selection.append(entry)
                
            new_selection = copy.deepcopy(new_selection)
            if append == False or self.selection == None:
                self.selection = set()
            if preliminary == False:
                for sel_element in new_selection:
                    if remove == True and sel_element in self.selection:
                        self.selection.remove(sel_element)
                    else:
                        if remove == False:
                            self.selection.add(sel_element)
            else:
                for sel_element in new_selection:
                    if remove == True:
                        self.selection_preliminary_remove.add(sel_element)
                    else:
                        self.selection_preliminary.add(sel_element)
        else:
            self.selection = None
            
    def get_selected(self, selection = None):
        """
        Returns the selected characters, offset-augmnented
        """
        if selection == None:
            selection = self.selection
        if selection == None or len(selection) == 0:
            selection = [(self.cursor_x, self.cursor_y)]
            
        selected = []
        min_x = 1000000000
        min_y = 1000000000
        for x, y in selection:
            min_x = min(x, min_x)
            min_y = min(y, min_y)
            selected.append([x, y, self.ansi_image[y][x]])
        
        for sel_item in selected:
            sel_item[0] -= min_x
            sel_item[1] -= min_y
            
        return copy.deepcopy(selected)
    
    def paste(self, paste_object, x = None, y = None):
        """
        Pastes at given or (default) cursor position
        
        Returns what was there before
        """
        if x == None:
            x = self.cursor_x
        
        if y == None:
            y = self.cursor_y
            
        inverse = []
        for (x_off, y_off, char) in paste_object:
            char_x = x + x_off
            char_y = y + y_off
            if char_x >= self.width or char_y >= self.height:
                continue
            inverse.append([char_x, char_y, [None, None, None]])
            for num, value in enumerate(char):
                if value != None:
                    inverse[-1][2][num] = self.ansi_image[char_y][char_x][num]
                    self.ansi_image[char_y][char_x][num] = value
        self.is_dirty = True
        return inverse
    
    def generate_ansi_char(self, in_char, fg_bright, bg_bright, fg, bg):
        """
        Generate ansi char as array: char idx, fg pal idx, bg pal idx
        """
        if fg_bright:
            fg += 8
        if bg_bright:
            bg += 8
        return [ord(in_char), fg, bg]
    
    def move_cursor(self, x = None, y = None, relative = True):
        """
        Change position of the cursor.
        
        Returns True if cursor moved, False if no.
        """
        new_x = x
        new_y = y
        
        if x == None:
            new_x = self.cursor_x
        
        if y == None:
            new_y = self.cursor_y
        
        if relative == True:
            new_x += self.cursor_x
            new_y += self.cursor_y

        new_x = max(0, min(new_x, self.width - 1))
        new_y = max(0, min(new_y, self.height - 1))
        
        moved = False
        if new_x != self.cursor_x or new_y != self.cursor_y:
            moved = True
            
        self.cursor_x = new_x
        self.cursor_y = new_y
        return moved
    
    def set_cell(self, char = None, fore = None, back = None, x = None, y = None):
        """
        Sets the values of a character cell to the given values. Only replaces 
        values given. Uses cursor position if no position is given.
        
        Returns the set cells previous value, position-augmented and as list for convenience
        """
        if x == None:
            x = self.cursor_x
        if y == None:
            y = self.cursor_y
        
        prev_val = [x, y, [None, None, None]]
        
        if char != None:
            prev_val[2][0] = self.ansi_image[y][x][0]
            self.ansi_image[y][x][0] = char
        
        if fore != None:
            prev_val[2][1] = self.ansi_image[y][x][1]
            self.ansi_image[y][x][1] = fore
            
        if back != None:
            prev_val[2][2] = self.ansi_image[y][x][2]
            self.ansi_image[y][x][2] = back
        
        self.is_dirty = True
        return copy.deepcopy([prev_val])
    
    def get_cell(self, x = None, y = None):
        """
        Return value in given cell (or under cursor, by default)
        """
        if x == None:
            x = self.cursor_x
        if y == None:
            y = self.cursor_y
        return self.ansi_image[y][x]
    
    def get_cursor(self):
        """
        Return cursor x, y
        """
        return (self.cursor_x, self.cursor_y)
    
    def get_line_end(self, y = None):
        """
        Find x coordinate of the "line ending". -1 if empty
        """
        if y == None:
            y = self.cursor_y
        for x in range(self.width - 1, -1, -1):
            if self.ansi_image[y][x][0] != ord(' '):
                return x
        return -1
    
    def dirty(self, keep = True):
        """
        Returns if the image is "dirty" (i.e. has been modified) or
        sets dirty to false if keep is set to False
        """
        if keep == False:
            self.is_dirty = False
        return self.is_dirty
    
    def clear_image(self, new_width = None, new_height = None):
        """
        Sets the image to all black blank characters.
        Optionally also sets width and height.
        """
        if new_width != None:
            self.width = new_width
            
        if new_height != None:
            self.height = new_height
    
        self.ansi_image = []
        for i in range(self.height):
            line = []
            for j in range(self.width):
                line.append(self.generate_ansi_char(' ', False, False, 0, 0))
            self.ansi_image.append(line)
    
    def load_ans(self, ansi_path):
        """
        Loads and parses and ansi file. Documentation of parse_ans applies.
        Additionally assumes data is encoded as cp1252.
        """
        with open(ansi_path, "r", encoding='cp1252') as f:
            ansi_data = f.read()
        self.parse_ans(ansi_data)
        self.is_dirty = False
        
    def parse_ans(self, ansi_str):
        """
        Parses an .ans files content. Assumes well-formed, breaks if not so.
  
        Handled ansi escapes for us are SGR (m) and CUF (C).
        Within SGR, we care about 0 (reset), 1 (fg bright), 5 (bg bright), 30–37 (set fg), 40–47 (set bg).

        Everything else is ignored.
        """
        ansi_lines = []
        ansi_line = []
        char_idx = 0
        current_fg_bright = False
        current_bg_bright = False
        current_fg = 7
        current_bg = 0
        while char_idx < len(ansi_str) and ansi_str[char_idx] != '\x1a':
            # Begin ansi escape
            if ansi_str[char_idx] == "\x1b":
                char_idx += 2 
                escape_param_str = ""
                escape_char = ""
                while not (ansi_str[char_idx] == 'm' or ansi_str[char_idx] == 'C'):
                    escape_param_str += ansi_str[char_idx]
                    char_idx += 1
                escape_char = ansi_str[char_idx]
                escape_params = list(map(int, escape_param_str.split(";")))
                
                # SGR
                if escape_char == 'm':
                    for param in escape_params:
                        if param == 0:
                            current_fg_bright = False
                            current_bg_bright = False
                            current_fg = 7
                            current_bg = 0
                        
                        if param == 1:
                            current_fg_bright = True
                        
                        if param == 5:
                            current_bg_bright = True
                        
                        if param >= 30 and param <= 37:
                            current_fg = param - 30
                            
                        if param >= 40 and param <= 47:
                            current_bg = param - 40
                # CUF
                if escape_char == 'C':
                    for i in range(escape_params[0]):
                        ansi_line.append(self.generate_ansi_char(
                            ' ', 
                            current_fg_bright, 
                            current_bg_bright, 
                            current_fg, 
                            current_bg
                        ))
                        
                char_idx += 1
                continue
                
            # End of line
            if ansi_str[char_idx] == '\n':
                ansi_lines.append(ansi_line)
                ansi_line = []
                char_idx += 1
                continue
            
            # Normal character
            ansi_line.append(self.generate_ansi_char(
                ansi_str[char_idx], 
                current_fg_bright, 
                current_bg_bright, 
                current_fg, 
                current_bg
            ))
            char_idx += 1
        if len(ansi_line) != 0:
            ansi_lines.append(ansi_line)
        
        # Pad up to maximum length
        line_len = max(map(len, ansi_lines))
        if self.min_line_len != None:
            line_len = max(line_len, self.min_line_len)
        
        for line in ansi_lines:
            this_line_len = len(line)
            for i in range(line_len - this_line_len):
                line.append(self.generate_ansi_char(' ', False, False, 0, 0))
                
        self.ansi_image = ansi_lines
        self.width = len(ansi_lines[0])
        self.height = len(ansi_lines)
    
    def to_ans(self):
        """
        Returns a textual ansi representation of the image.
        
        No effort is made to reduce size at this time.
        """
        ansi_str = ""
        for y in range(0, self.height):
            for x in range(0, self.width):
                char_info = self.ansi_image[y][x]
            
                ansi_str += "\x1b[0;"
                    
                if char_info[1] >= 8:
                    ansi_str += "1;"
                ansi_str += str((char_info[1] % 8) + 30) + ";"
                
                if char_info[2] >= 8:
                    ansi_str += "5;"
                ansi_str += str((char_info[2] % 8) + 40)
                
                ansi_str += "m"
                ansi_str += chr(char_info[0])
            ansi_str += "\n"
        return ansi_str
    
    def save_ans(self, out_path):
        """
        Writes .ans file from this images contents
        """
        with open(out_path, "w", encoding='cp1252') as f:
            f.write(self.to_ans())
    
    def to_bitmap(self, ansi_graphics, transparent = False, cursor = False):
        """
        Returns pixel representation of this image as a PIL Image object
        """
        ansi_bitmap = np.ones((AnsiImage.CHAR_SIZE_Y * self.height, AnsiImage.CHAR_SIZE_X * self.width, 4))
        for y in range(0, self.height):
            for x in range(0, self.width):
                char_info = self.ansi_image[y][x]
                char_col = ansi_graphics.coloured_char(char_info[0], char_info[1], char_info[2])
                ansi_bitmap[
                    AnsiImage.CHAR_SIZE_Y * y : AnsiImage.CHAR_SIZE_Y * (y + 1),
                    AnsiImage.CHAR_SIZE_X * x : AnsiImage.CHAR_SIZE_X * (x + 1),
                    0:3
                ] = char_col
                
                # Make pixels transparent
                if transparent == True and char_info[0] == ord(' '):
                    ansi_bitmap[
                        AnsiImage.CHAR_SIZE_Y * y : AnsiImage.CHAR_SIZE_Y * (y + 1),
                        AnsiImage.CHAR_SIZE_X * x : AnsiImage.CHAR_SIZE_X * (x + 1),
                        3
                    ] = np.zeros((AnsiImage.CHAR_SIZE_Y, AnsiImage.CHAR_SIZE_X))
                    
                # Draw cursor on top
                if cursor == True and x == self.cursor_x and y == self.cursor_y:
                    for cursor_pix_y, cursor_pix_x in self.cursor_shape:
                        ansi_bitmap[AnsiImage.CHAR_SIZE_Y * y + cursor_pix_y, AnsiImage.CHAR_SIZE_X * x + cursor_pix_x, 0:3] = \
                            1.0 - ansi_bitmap[AnsiImage.CHAR_SIZE_Y * y + cursor_pix_y, AnsiImage.CHAR_SIZE_X * x + cursor_pix_x, 0:3]
                        ansi_bitmap[AnsiImage.CHAR_SIZE_Y * y + cursor_pix_y, AnsiImage.CHAR_SIZE_X * x + cursor_pix_x, 3] = 1.0
        
        # Invert selection
        full_selection = self.selection_preliminary
        if self.selection != None:
            full_selection = full_selection.union(self.selection)
        full_selection = full_selection.difference(self.selection_preliminary_remove)
        
        if len(full_selection) != 0:
            for x, y in full_selection:
                ansi_bitmap[
                    AnsiImage.CHAR_SIZE_Y * y : AnsiImage.CHAR_SIZE_Y * (y + 1),
                    AnsiImage.CHAR_SIZE_X * x : AnsiImage.CHAR_SIZE_X * (x + 1),
                    0:3
                ] = 1.0 - ansi_bitmap[
                    AnsiImage.CHAR_SIZE_Y * y : AnsiImage.CHAR_SIZE_Y * (y + 1),
                    AnsiImage.CHAR_SIZE_X * x : AnsiImage.CHAR_SIZE_X * (x + 1),
                    0:3
                ]
                        
        return Image.fromarray((ansi_bitmap * 255.0).astype('int8'), mode='RGBA')
    
