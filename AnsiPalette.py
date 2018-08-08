from AnsiImage import AnsiImage

class AnsiPalette:
    """
    Manages a palette of coloured ansi characters
    """
    
    def __init__(self, ansi_graphics):
        """
        Just stores a graphics object to work with.
        """
        self.graphics = ansi_graphics
        self.cur_fore = 15 # White
        self.cur_back = 0 # Black
        self.char_idx = 0
        self.chars = [176, 177, 178, 219, 223, 220, 221, 222, 254, 249, 32, 32] # Pablodraw default
        
    def set_fore(self, fore):
        """
        Sets the foreground colour
        """
        self.cur_fore = fore
        
    def fore(self):
        """
        Returns the current foreground colour
        """
        return self.cur_fore
    
    def set_back(self, back):
        """
        Sets the background colour
        """
        self.cur_back = back
        
    def back(self):
        """
        Returns the current background colour
        """
        return self.cur_back
    
    def set_char_sequence(self, char_sequence):
        """
        Sets the palette character sequence
        """
        self.chars = char_sequence
        if len(self.chars) > 12:
            self.chars = self.chars[:12]
            
        if self.char_idx >= len(char_sequence):
            self.char_idx = 0
            
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
            return [idx, self.fore(), self.back()]
    
    def get_char_image(self, idx = None, from_seq = False):
        """
        Returns an image of a single character
        """
        char = self.get_char(idx, from_seq)
        char_image = AnsiImage()
        char_image.clear_image(1, 1)
        char_image.set_cell(x = 0, y = 0, fore = char[1], back = char[2], char = char[0])
        return char_image.to_bitmap(self.graphics)
    
    def get_palette_image(self):
        """
        Returns a 8x2 palette, with 16x16 square characters
        """
        pal_image = AnsiImage()
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
                    
        return pal_image.to_bitmap(self.graphics)
        
    
    def get_character_image(self, width = 32, fore = None, back = None):
        """
        Returns a character selection image
        """
        height = int(256 / width)
        if height < 256 / width:
            height += 1
            
        sel_image = AnsiImage()
        sel_image.clear_image(width, height)
        
        if fore == None:
            fore = self.fore()
        
        if back == None:
            back = self.back()
        
        char_idx = 0
        for y in range(0, height):
            for x in range(0, width):
                if char_idx < 256:
                    sel_image.set_cell(char = char_idx, fore = fore, back = back, x = x, y = y)
                    char_idx += 1
                    
        sel_image.move_cursor(self.char_idx % width, self.char_idx // width, False)
        return sel_image.to_bitmap(self.graphics, cursor = True, transparent = True)
    
