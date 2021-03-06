from AnsiImage import AnsiImage

class AnsiPalette:
    """
    Manages a palette of coloured ansi characters
    """
    
    def __init__(self, ansi_graphics, palette_file):
        """
        Just stores a graphics object to work with.
        """
        self.graphics = ansi_graphics
        self.cur_fore = 15 # White
        self.cur_back = 0 # Black
        self.char_idx = 0
        self.invalid = [0, 8, 9, 10, 13, 26, 27, 255] # These will break acidview
        self.char_palettes = AnsiImage(self.graphics, min_line_len = 12)
        self.char_palettes.load_ans(palette_file)
        self.select_char_sequence(5)
    
    def change_graphics(self, graphics):
        """
        Change the ansi graphics used
        """
        self.graphics = graphics
    
    def set_fore(self, fore, relative = False):
        """
        Sets the foreground colour
        """
        if relative == False:
            self.cur_fore = 0
        self.cur_fore += fore
        self.cur_fore = max(0, min(self.cur_fore, 15))
        
    def fore(self):
        """
        Returns the current foreground colour
        """
        return self.cur_fore
    
    def set_back(self, back, relative = False):
        """
        Sets the background colour
        """
        if relative == False:
            self.cur_back = 0
        self.cur_back += back
        self.cur_back = max(0, min(self.cur_back, 15))
        
    def back(self):
        """
        Returns the current background colour
        """
        return self.cur_back
    
    def set_char_sequence(self, char_sequence):
        """
        Sets the palette character sequence directly
        """
        self.chars = char_sequence
        if len(self.chars) > 12:
            self.chars = self.chars[:12]
            
        if self.char_idx >= len(char_sequence):
            self.char_idx = 0
    
    def select_char_sequence(self, index, relative = False):
        """
        Select a palette from the character palettes
        """
        if relative == False:
            self.char_sequence_index = 0
        self.char_sequence_index += index
        self.char_sequence_index = max(0, min(self.char_sequence_count() - 1, self.char_sequence_index))
        new_palette = []
        for x in range(0, 12):
            char, _, _ = self.char_palettes.get_cell(x, self.char_sequence_index)
            new_palette.append(char)
        self.chars = new_palette
    
    def get_char_sequence_image(self, index):
        """
        Returns an image of one of the character sequences
        """
        char_image = AnsiImage(self.graphics)
        char_image.clear_image(12, 1)
        for i in range(12):
            char, _, _ = self.char_palettes.get_cell(i, index)
            char_image.set_cell(x = i, y = 0, char = char, back = self.cur_back, fore = self.cur_fore)
        return char_image.to_bitmap()
    
    def char_sequence_count(self):
        """
        Return how many selectable character sequences exist
        """
        return self.char_palettes.get_size()[1]
    
    def set_char_idx(self, char_idx):
        """
        Sets the current character index
        """
        self.char_idx = char_idx
        
    def get_char(self, idx = None, from_seq = False):
        """
        Gets the character at the given index with the appropriate colours
        Active char is returned if none specified
        """
        if idx == None:
            idx = self.char_idx
            
        if from_seq == True:
            return [self.chars[idx], self.fore(), self.back()]
        else:
            if idx in self.invalid:
                idx = ord(' ')
            return [idx, self.fore(), self.back()]
    
    def get_char_image(self, idx = None, from_seq = False):
        """
        Returns an image of a single character
        """
        char = self.get_char(idx, from_seq)
        char_image = AnsiImage(self.graphics)
        char_image.clear_image(1, 1)
        char_image.set_cell(x = 0, y = 0, fore = char[1], back = char[2], char = char[0])
        return char_image.to_bitmap()
    
    def get_palette_image(self):
        """
        Returns a 8x2 palette, with 16x16 square characters
        """
        pal_image = AnsiImage(self.graphics)
        pal_image.clear_image(16, 2)
        
        pal_idx = 0
        for y in range(0, 2):
            for x in range(0, 16, 2):
                fore_col = 15
                if pal_idx >= 8:
                    fore_col = 0
                
                fore_char = ' '
                if pal_idx == self.fore():
                    fore_char = 'f'
                
                back_char = ' '
                if pal_idx == self.back():
                    back_char = 'b'
                    
                pal_image.set_cell(char = ord(fore_char), fore = fore_col, back = pal_idx, x = x, y = y)
                pal_image.set_cell(char = ord(back_char), fore = fore_col, back = pal_idx, x = x + 1, y = y)
                pal_idx += 1
                    
        return pal_image.to_bitmap()
        
    
    def get_character_image(self, width = 32, fore = None, back = None):
        """
        Returns a character selection image
        """
        height = int(256 / width)
        if height < 256 / width:
            height += 1
            
        sel_image = AnsiImage(self.graphics)
        sel_image.clear_image(width, height)
        
        if fore == None:
            fore = self.fore()
        
        if back == None:
            back = self.back()
        
        char_idx = 0
        for y in range(0, height):
            for x in range(0, width):
                if char_idx < 256 and not char_idx in self.invalid:
                    sel_image.set_cell(char = char_idx, fore = fore, back = back, x = x, y = y)
                else:
                    sel_image.set_cell(char = ord(' '), fore = fore, back = back, x = x, y = y)
                char_idx += 1
                    
        sel_image.move_cursor(self.char_idx % width, self.char_idx // width, False)
        return sel_image.to_bitmap(cursor = True, transparent = True)
    
