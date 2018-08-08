import numpy as np

class AnsiGraphics:
    """
    This class manages ansi fonts and colours.
    """
    
    # VGA Palette
    VGA_PAL = [
        np.array([0, 0, 0]) / 255.0,
        np.array([170, 0, 0]) / 255.0,
        np.array([0, 170, 0]) / 255.0,
        np.array([170, 85, 0]) / 255.0,
        np.array([0, 0, 170]) / 255.0,
        np.array([170, 0, 170]) / 255.0,
        np.array([0, 170, 170]) / 255.0,
        np.array([170, 170, 170]) / 255.0,
        np.array([85, 85, 85]) / 255.0,
        np.array([255, 85, 85]) / 255.0,
        np.array([85, 255, 85]) / 255.0,
        np.array([255, 255, 85]) / 255.0,
        np.array([85, 85, 255]) / 255.0,
        np.array([255, 85, 255]) / 255.0,
        np.array([85, 255, 255]) / 255.0,
        np.array([255, 255, 255]) / 255.0
    ];
    
    def __init__(self, font_file):
        """
        Reads the font to use and prepares it for usage.
        Fonts are files with a sequence of bits specifying 8x16 characters.
        """
        # Read the font
        f = open("vga.fnt", "rb")
        in_bits = []
        try:
            byte = f.read(1)
            while len(byte) != 0:
                bin_str = bin(int.from_bytes(byte, 'little'))[2:]
                for bit in bin_str.zfill(8):
                    in_bits.append(bit)
                byte = f.read(1)
        finally:
            f.close()
        
        # Split into chars
        self.font_chars = []
        for i in range(0, 256):
            char_bits = np.array(in_bits[i * 16 * 8 : (i + 1) * 16 * 8])
            char_bits = char_bits.reshape(16, 8).astype(float)
            self.font_chars.append(char_bits)
            
        # It's 2018 and memory is cheap, so lets precompute every possible fore/back/char combination
        self.colour_chars = []
        for char_idx in range(0, 256):
            fg_chars = []
            for fg_idx in range(0, 16):
                bg_chars = []
                for bg_idx in range(0, 16):
                    char_base = self.font_chars[char_idx][:]
                    char_col = np.zeros((char_base.shape[0], char_base.shape[1], 3))
                    char_col[np.where(char_base == 1)] = AnsiGraphics.VGA_PAL[fg_idx]
                    char_col[np.where(char_base == 0)] = AnsiGraphics.VGA_PAL[bg_idx]
                    bg_chars.append(char_col)
                fg_chars.append(bg_chars)
            self.colour_chars.append(fg_chars)
            
    def vga_colour(self, pal_idx):
        """
        Returns the VGA palette colour with the given index as an RGP triplet.
        """
        return AnsiGraphics.VGA_PAL[idx]
    
    def char_bitmap(self, char_idx):
        """
        Returns the font character with the given index as a binary bitmap.
        """
        return self.font_chars[idx]
    
    def coloured_char(self, char_idx, fg_idx, bg_idx):
        """
        Returns the font character with the given index and given fore and back colours as an RGP bitmap.
        """
        return self.colour_chars[char_idx][fg_idx][bg_idx]
    