#include "hid_dev.h"

hid_key_t ascii_to_hid(uint8_t ascii) {
    hid_key_t k = {0, 0};
    
    // Lowercase a-z
    if (ascii >= 'a' && ascii <= 'z') k.code = (ascii - 'a' + 0x04);
    // Uppercase A-Z
    else if (ascii >= 'A' && ascii <= 'Z') { k.code = (ascii - 'A' + 0x04); k.modifier = 0x02; }
    // Numbers 1-9, then 0
    else if (ascii >= '1' && ascii <= '9') k.code = (ascii - '1' + 0x1e);
    else if (ascii == '0') k.code = 0x27;
    
    // Special Gaming Keys (Mapped to non-printable ASCII or specific characters)
    else if (ascii == ' ') k.code = 0x2c; // Space
    else if (ascii == '\t') k.code = 0x2b; // Tab
    else if (ascii == 0x1B) k.code = 0x29; // Escape (Esc)
    
    // Custom mapping for Arrows (You can send these via Python)
    // We can use common ANSI-like triggers
    else if (ascii == '^') k.code = 0x52; // Up Arrow
    else if (ascii == '|') k.code = 0x51; // Down Arrow (Vertical bar)
    else if (ascii == '<') k.code = 0x50; // Left Arrow
    else if (ascii == '>') k.code = 0x4f; // Right Arrow
    
    // Common symbols
    else if (ascii == '!') { k.code = 0x1e; k.modifier = 0x02; }
    else if (ascii == '?') { k.code = 0x38; k.modifier = 0x02; }
    
    return k;
}