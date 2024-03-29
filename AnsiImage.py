import numpy as np
from PIL import Image
import copy
import time
import os

class AnsiImage:
    """
    Manages a rectangular image made of ansi character cells
    """
    def __init__(self, graphics, min_line_len = None, has_autosave=False):
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
        self.write_allowed = [True, True, True]
        self.steps_since_autosave = 0
        self.autosave_steps = 10
        self.autosave_counter = 0
        self.autosave_max = 25
        self.has_autosave = has_autosave
        
        self.ansi_graphics = graphics
        self.char_size_x = self.ansi_graphics.get_char_size()[0]
        self.char_size_y = self.ansi_graphics.get_char_size()[1]
        
        # Selection related stuff
        self.selection = None
        self.selection_preliminary = set()
        self.selection_preliminary_remove = set()
        self.redraw_set = set()
        self.ansi_bitmap = None
        self.have_cache = False
        self.cache_params = None
        
        # The cursor
        self.rebuild_cursor()
        
    def get_size(self):
        """
        Return the current canvas size in characters
        """
        return (self.width, self.height)
    
    def rebuild_cursor(self):
        self.cursor_shape = []
        for y in [0, 1, self.char_size_y - 2, self.char_size_y - 1]:
            for x in range(0, self.char_size_x):
                self.cursor_shape.append((y, x))
        for y in range(2, self.char_size_y - 2):
            for x in [0, 1, self.char_size_x - 2, self.char_size_x - 1]:
                self.cursor_shape.append((y, x))
        
    
    def get_char_size(self):
        """
        Return the character size, in pixels
        """
        return (self.char_size_x, self.char_size_y)
    
    def change_graphics(self, new_graphics):
        """
        Changes the graphics in use
        """
        self.ansi_graphics = new_graphics
        self.char_size_x = self.ansi_graphics.get_char_size()[0]
        self.char_size_y = self.ansi_graphics.get_char_size()[1]
        self.have_cache = False
        self.rebuild_cursor()
        
    def change_size(self, new_width, new_height, new_state = None):
        """
        Make the image larger or smaller, retaining contents.
        
        Returns the previous state of the image as a tuple of (width, height, image state)
        that can be used to reverse the operation
        """
        copy_width = min(self.width, new_width)
        copy_height = min(self.height, new_height)
        
        old_height = self.height
        old_width = self.width
        old_image = copy.deepcopy(self.ansi_image)
        
        self.clear_image(new_width, new_height)
        if new_state == None:
            for y in range(copy_height):
                for x in range(copy_width):
                    self.ansi_image[y][x] = old_image[y][x]
            self.have_cache = False
        else:
            self.ansi_image = copy.deepcopy(new_state)
            
        self.have_cache = False
        self.is_dirty = True
        return (old_width, old_height, old_image)
        
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
        self.redraw_set.update(self.selection_preliminary)
        self.redraw_set.update(self.selection_preliminary_remove)
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
                if self.selection != None:
                    self.redraw_set.update(self.selection)
                self.selection = set()
            if preliminary == False:
                for sel_element in new_selection:
                    if remove == True and sel_element in self.selection:
                        self.selection.remove(sel_element)
                        self.redraw_set.add(sel_element)
                    else:
                        if remove == False:
                            self.selection.add(sel_element)
                            self.redraw_set.add(sel_element)
            else:
                for sel_element in new_selection:
                    if remove == True:
                        self.selection_preliminary_remove.add(sel_element)
                        self.redraw_set.add(sel_element)
                    else:
                        self.selection_preliminary.add(sel_element)
                        self.redraw_set.add(sel_element)
        else:
            self.redraw_set.update(self.selection)
            self.selection = None
            
    def get_selected(self, skip_space = False, selection = None):
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
            if not skip_space or self.ansi_image[y][x][0] != ord(' '):
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
            char_inverse = self.set_cell(char = char[0], fore = char[1], back = char[2], x = char_x, y = char_y)
            inverse.extend(char_inverse)
        return inverse
    
    def fill_selection(self, fill_char = None):
        """
        Fills the selection with a given character (default: space)
        
        If no selection, cursor is used.
        """
        if fill_char == None:
            fill_char = self.generate_ansi_char(' ', False, False, 0, 0)
            
        selection = self.selection
        if selection == None or len(selection) == 0:
            selection = [(self.cursor_x, self.cursor_y)]
        
        inverse = []
        for x, y in selection:
            inverse.extend(self.set_cell(x = x, y = y, char = fill_char[0], fore = fill_char[1], back = fill_char[2]))
        return inverse
        
    def shift_line(self, y = None, x = None, how_much = 1, fill_char = None):
        """
        Shifts a line to the left or right (starting at the given x),
        filling the holes with the given character (default: cursor, space).
        
        how_much can be negative to shift to the left.
        """
        if x == None:
            x = self.cursor_x
        
        if y == None:
            y = self.cursor_y
        
        if fill_char == None:
            fill_char = self.generate_ansi_char(' ', False, False, 0, 0)
        
        inverse = []
        for i in range(self.width):
            inverse.append((i, y, copy.deepcopy(self.ansi_image[y][i])))
            self.redraw_set.add((i, y))
        
        if how_much > 0:
            new_line = self.ansi_image[y][:x]
            for i in range(how_much):
                new_line.append(copy.deepcopy(fill_char))
            new_line += self.ansi_image[y][x:]
            self.ansi_image[y] = new_line[:self.width]
        
        if how_much < 0:
            new_line = self.ansi_image[y][:x]
            new_line += self.ansi_image[y][x - how_much:]
            for i in range(-how_much):
                new_line.append(copy.deepcopy(fill_char))
            self.ansi_image[y] = new_line[:self.width]
        
        self.is_dirty = True
        return inverse
    
    def shift_column(self, y = None, x = None, how_much = 1, fill_char = None):
        """
        Same, but columns
        """
        if x == None:
            x = self.cursor_x
        
        if y == None:
            y = self.cursor_y
        
        # Swap and transpose
        tmp = x
        x = y
        y = tmp
        image_transposed = list(map(list, zip(*self.ansi_image)))
        
        # Now, the code is nearly the same as row shift
        if fill_char == None:
            fill_char = self.generate_ansi_char(' ', False, False, 0, 0)
        
        inverse = []
        for i in range(self.height):
            inverse.append((y, i, copy.deepcopy(self.ansi_image[i][y])))
            self.redraw_set.add((y, i))
        
        if how_much > 0:
            new_line = image_transposed[y][:x]
            for i in range(how_much):
                new_line.append(copy.deepcopy(fill_char))
            new_line += image_transposed[y][x:]
            image_transposed[y] = new_line[:self.height]
        
        if how_much < 0:
            new_line = image_transposed[y][:x]
            new_line += image_transposed[y][x - how_much:]
            for i in range(-how_much):
                new_line.append(copy.deepcopy(fill_char))
            image_transposed[y] = new_line[:self.height]
        
        self.is_dirty = True
        self.ansi_image = list(map(list, zip(*image_transposed)))
        
        return inverse
    
    def generate_ansi_char(self, in_char, fg_bright, bg_bright, fg, bg, raw = False):
        """
        Generate ansi char as array: char idx, fg pal idx, bg pal idx
        """
        if fg_bright:
            fg += 8
        if bg_bright:
            bg += 8
        if raw == False:
            return [ord(in_char), fg, bg]
        else:
            return [in_char, fg, bg]
    
    def move_cursor(self, x = None, y = None, relative = True):
        """
        Change position of the cursor.
        
        Returns True if cursor moved, False if no.
        """
        new_x = x
        new_y = y
        self.redraw_set.add((self.cursor_x, self.cursor_y))
        
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
        self.redraw_set.add((self.cursor_x, self.cursor_y))
        
        return moved
    
    def set_write_allowed(self, char = None, fore = None, back = None):
        """
        Set or unset write-allow flags for character, foreground or background
        """
        if char != None:
            self.write_allowed[0] = char
            
        if fore != None:
            self.write_allowed[1] = fore
            
        if back != None:
            self.write_allowed[2] = back
        
    def set_cell(self, char = None, fore = None, back = None, x = None, y = None, ignore_allowed = False):
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
        
        if ignore_allowed == False and self.write_allowed[0] == False:
            char = None
            prev_val[2][0] = None
            
        if ignore_allowed == False and self.write_allowed[1] == False:
            fore = None
            prev_val[2][1] = None
            
        if ignore_allowed == False and self.write_allowed[2] == False:
            back = None
            prev_val[2][2] = None
            
        if char != None:
            prev_val[2][0] = self.ansi_image[y][x][0]
            self.ansi_image[y][x][0] = char
        
        if fore != None:
            prev_val[2][1] = self.ansi_image[y][x][1]
            self.ansi_image[y][x][1] = fore
            
        if back != None:
            prev_val[2][2] = self.ansi_image[y][x][2]
            self.ansi_image[y][x][2] = back
        
        self.redraw_set.add((x, y))
        
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
        self.have_cache = False
        
    def load_ans(self, ansi_path, wide_mode = False):
        """
        Loads and parses and ansi file. Documentation of parse_ans applies.
        
        wide_mode makes it so the parser doesn't insert line breaks at 80 characters.
        """
        with open(ansi_path, "rb") as f:
            ansi_data = f.read()
        self.parse_ans(ansi_data, wide_mode)
        self.steps_since_autosave = 0
        self.is_dirty = False
        
    def parse_ans(self, ansi_bytes, wide_mode = False):
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
        supported_controls = [ord('m'), ord('C'), ord('A'), ord('J'), ord('s'), ord('u'), ord('H')]
        while char_idx < len(ansi_bytes) and ansi_bytes[char_idx] != 0x1A:
            # Begin ansi escape
            if ansi_bytes[char_idx] == 0x1B:
                char_idx += 2 
                escape_param_str = ""
                escape_char = ""
                while not ansi_bytes[char_idx] in supported_controls:
                    escape_param_str += chr(ansi_bytes[char_idx])
                    char_idx += 1
                escape_char = chr(ansi_bytes[char_idx])
                escape_params = []
                if len(escape_param_str):
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
                    if len(escape_params) == 0:
                        continue
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
            if ansi_bytes[char_idx] == 13:
                char_idx += 1
                continue
            if ansi_bytes[char_idx] == 10:
                ansi_lines.append(ansi_line)
                ansi_line = []
                char_idx += 1
                continue
            
            # Normal character
            ansi_line.append(self.generate_ansi_char(
                ansi_bytes[char_idx], 
                current_fg_bright, 
                current_bg_bright, 
                current_fg, 
                current_bg,
                raw = True
            ))
            
            # If not wide mode and we're at 80 characters, break up the line
            if not wide_mode and len(ansi_line) == 80:
                ansi_lines.append(ansi_line)
                ansi_line = []
                char_idx += 1
                continue
            
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
        self.have_cache = False
        
    def str_to_bytes(self, string):
        """
        Basic string to list of bytes function. Valid only for printable < 128.
        """
        byte_list = []
        for char in string:
            byte_list.append(ord(char))
        return byte_list
    
    def add_sauce(self, title = "", author = "", group = ""):
        """
        Generate a SAUCE tag.
        
        Sauce tags look like:
        struct SAUCE
        {
            char           ID[5]; // "SAUCE"
            char           Version[2]; // "00"
            char           Title[35]; // title
            char           Author[20]; // author
            char           Group[20]; // group
            char           Date[8]; // "CCYYMMDD", e.g. "20130504"
            unsigned long  FileSize; // in bytes, nil legal
            unsigned char  DataType; // 1 for character-based
            unsigned char  FileType; // 1 for ANSI
            unsigned short TInfo1; // Character width: 8
            unsigned short TInfo2; // Nb. of lines
            unsigned short TInfo3; // 0
            unsigned short TInfo4; // 0
            unsigned char  Comments; // 0
            unsigned char  TFlags; // 00010011 - square pixel aspect, 8 pixel font, iCE colours
            char           TInfoS[22]; // Font name - "IBM VGA"
        };
        
        Full reference: http://www.acid.org/info/sauce/sauce.htm bless ACiD for documenting this so well y'all people own
        """
        sauce_bytes = [0x1a]
        sauce_bytes += self.str_to_bytes("SAUCE00")
        sauce_bytes += self.str_to_bytes(title.ljust(35))
        sauce_bytes += self.str_to_bytes(author.ljust(20))
        sauce_bytes += self.str_to_bytes(group.ljust(20))
        sauce_bytes += self.str_to_bytes(time.strftime("%Y%m%d"))
        sauce_bytes += [0, 0, 0, 0] # TODO make an effort to actually put file size here
        sauce_bytes += [1]
        sauce_bytes += [1]
        sauce_bytes += [self.width % 256, self.height // 256]
        sauce_bytes += [self.height % 256, self.width // 256]
        sauce_bytes += [0, 0]
        sauce_bytes += [0, 0]
        sauce_bytes += [0]
        sauce_bytes += [0b00010011]
        sauce_bytes += self.str_to_bytes("IBM VGA".ljust(22, '\0'))
        return sauce_bytes
    
    def to_ans(self):
        """
        Returns a byte-array text representation of the image.
        
        No effort is made to reduce size at this time.
        """
        ansi_bytes = []
        for y in range(0, self.height):
            for x in range(0, self.width):
                char_info = self.ansi_image[y][x]
            
                ansi_bytes += [0x1b] 
                ansi_bytes += self.str_to_bytes('[0;')
                    
                if char_info[1] >= 8:
                    ansi_bytes += self.str_to_bytes('1;')
                ansi_bytes += self.str_to_bytes(str((char_info[1] % 8) + 30) + ";")
                
                if char_info[2] >= 8:
                    ansi_bytes += self.str_to_bytes("5;")
                ansi_bytes += self.str_to_bytes(str((char_info[2] % 8) + 40))
                
                ansi_bytes += self.str_to_bytes("m")
                ansi_bytes += [char_info[0]]
            if self.width < 80: # If we're at 80 characters we omit the newline.
                ansi_bytes += [10]
        ansi_bytes += self.add_sauce()
        return bytearray(ansi_bytes)
    
    def save_ans(self, out_path):
        """
        Writes .ans file from this images contents
        """
        with open(out_path, "wb") as f:
            f.write(self.to_ans())
    
    def to_bitmap(self, transparent = False, cursor = False, area = None):
        """
        Returns pixel representation of this image as a PIL Image object
        
        Can be passed an area. If so, only character cells overlapping the requested area will be
        drawn. In this case the return value is a tuple of (real x start, real y start, bitmap image, actual size w, actual size h)
        """
        if self.have_cache == False or self.cache_params != [transparent, cursor]:
            self.ansi_bitmap = np.ones((self.char_size_y * self.height, self.char_size_x * self.width, 4))
            for y in range(0, self.height):
                for x in range(0, self.width):
                    self.redraw_set.add((x, y))
            self.have_cache = True
        self.cache_params = [transparent, cursor]
        
        for (x, y) in self.redraw_set:
            if x >= self.width or y >= self.height:
                continue
            
            char_info = self.ansi_image[y][x]
            char_col = self.ansi_graphics.coloured_char(char_info[0], char_info[1], char_info[2])
            self.ansi_bitmap[
                self.char_size_y * y : self.char_size_y * (y + 1),
                self.char_size_x * x : self.char_size_x * (x + 1),
                0:3
            ] = char_col
            
            # Make pixels transparent or no
            if transparent == True and char_info[0] == ord(' '):
                self.ansi_bitmap[
                    self.char_size_y * y : self.char_size_y * (y + 1),
                    self.char_size_x * x : self.char_size_x * (x + 1),
                    3
                ] = np.zeros((self.char_size_y, self.char_size_x))
            else:
                self.ansi_bitmap[
                    self.char_size_y * y : self.char_size_y * (y + 1),
                    self.char_size_x * x : self.char_size_x * (x + 1),
                    3
                ] = np.ones((self.char_size_y, self.char_size_x))
                
            # Draw cursor on top
            if cursor == True and x == self.cursor_x and y == self.cursor_y:
                for cursor_pix_y, cursor_pix_x in self.cursor_shape:
                    self.ansi_bitmap[self.char_size_y * y + cursor_pix_y, self.char_size_x * x + cursor_pix_x, 0:3] = \
                        1.0 - self.ansi_bitmap[self.char_size_y * y + cursor_pix_y, self.char_size_x * x + cursor_pix_x, 0:3]
                    self.ansi_bitmap[self.char_size_y * y + cursor_pix_y, self.char_size_x * x + cursor_pix_x, 3] = 1.0
        
        # Invert selection
        if cursor == True:
            full_selection = self.selection_preliminary
            if self.selection != None:
                full_selection = full_selection.union(self.selection)
            full_selection = full_selection.difference(self.selection_preliminary_remove)
            
            if len(full_selection) != 0:
                for x, y in full_selection:
                    if not (x, y) in self.redraw_set or x >= self.width or y >= self.height:
                        continue
                    self.ansi_bitmap[
                        self.char_size_y * y : self.char_size_y * (y + 1),
                        self.char_size_x * x : self.char_size_x * (x + 1),
                        0:3
                    ] = 1.0 - self.ansi_bitmap[
                        self.char_size_y * y : self.char_size_y * (y + 1),
                        self.char_size_x * x : self.char_size_x * (x + 1),
                        0:3
                    ]
                    
        redraw_start_x = self.width
        redraw_start_y = self.height
        redraw_end_x = 0
        redraw_end_y = 0
        for x, y in self.redraw_set:
            redraw_start_x = min(x, redraw_start_x)
            redraw_start_y = min(y, redraw_start_y)
            redraw_end_x = max(x, redraw_end_x)
            redraw_end_y = max(y, redraw_end_y)
            
        self.redraw_set = set()
        
        if area != None:
            start_x = min(area[0] // self.char_size_x, redraw_start_x)
            end_x = max((area[2] // self.char_size_x) + 1, redraw_end_y)
            
            start_y = min(area[1] // self.char_size_y, redraw_start_y)
            end_y = max((area[3] // self.char_size_y) + 1, redraw_end_y)
            
            return (
                start_x * self.char_size_x, 
                start_y * self.char_size_y, 
                Image.fromarray((self.ansi_bitmap[
                    start_y * self.char_size_y : end_y * self.char_size_y,
                    start_x * self.char_size_x : end_x * self.char_size_x
                ] * 255.0).astype('int8'), mode='RGBA'),
                self.char_size_x * self.width,
                self.char_size_y * self.height,
            )
        else:
            return Image.fromarray((self.ansi_bitmap * 255.0).astype('int8'), mode='RGBA')
    
    def deice(self):
        """
        Try to remove iCE colors from the image using closest visual matches
        and flipping fg/bg colors.
        """
        bg_color_conversion = [i if i < 8 else i % 8 for i in range(16)]

        # A function to find the best matching non-iCE character
        def find_best_char(in_char, fg, bg):
            # An expanded lookup table for character replacements
            char_conversion = {
                32: 176,  # Space to light shade
                176: 32,  # Light shade to space
                177: 178, # Medium shade to dark shade
                178: 177, # Dark shade to medium shade
                219: 178, # Solid block to dark shade
                220: 223, # Upper half block to lower half block
                221: 222, # Right half block to left half block
                222: 221, # Left half block to right half block
                223: 220, # Lower half block to upper half block
                254: 250, # Full block to small dot
                249: 250, # Small dot to small dot
            }

            if bg > 7:
                # Replace the character if necessary
                if in_char in char_conversion:
                    in_char = char_conversion[in_char]
                    # Swap fg and bg colors when replacing the character
                    fg, bg = bg, fg

                # Replace the background color with the closest non-iCE color
                bg = bg_color_conversion[bg]

            return in_char, fg, bg

        # Iterate through each pixel and replace iCE colors and characters
        for x in range(self.width):
            for y in range(self.height):
                in_char, fg, bg = self.ansi_image[y][x]
                self.ansi_image[y][x] = find_best_char(in_char, fg, bg)
                self.redraw_set.add((x, y))
        self.is_dirty = True

    def do_autosave(self):
        """
        Autosave occassionally. Call when adding/removing undo/redo steps
        """
        if not os.path.exists("autosaves"):
            os.mkdir("autosaves")
        self.steps_since_autosave += 1
        if self.steps_since_autosave >= self.autosave_steps:
            self.autosave_counter += 1
            if self.autosave_counter > self.autosave_max:
                self.autosave_counter = 0
            self.save_ans(f"autosaves/autosave_{self.autosave_counter}.ans")
            self.steps_since_autosave = 0