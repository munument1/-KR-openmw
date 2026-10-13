#ifndef OPENMW_MWDIALOGUE_LEGACYKOREANNAME_H
#define OPENMW_MWDIALOGUE_LEGACYKOREANNAME_H

#include <components/misc/utf8stream.hpp>

namespace MWDialogue
{
    // Verified legacy font components from saved names whose INFO explicitly names
    // the speaker. Unsupported vowels/finals are deliberately not guessed.
    inline std::string decodeLegacyKoreanName(std::string_view text)
    {
        Utf8Stream stream(text);
        std::string result;
        bool foundSyllable = false;
        while (!stream.eof())
        {
            auto initial = stream.consume();
            int leading = -1;
            if (initial >= 0x10 && initial <= 0x1f)
                leading = initial - 0x10;
            else if (initial == 0x0192) leading = 16;
            else if (initial == 0x2021) leading = 17;
            else if (initial == 0x00b0) leading = 18;
            else if (initial >= 0x20 && initial <= 0x7e)
            {
                result += static_cast<char>(initial);
                continue;
            }
            if (leading < 0 || stream.eof())
                return {};
            auto medial = stream.consume();
            int vowel;
            switch (medial)
            {
                case 0xa1: vowel = 0; break;
                case 0xaa: vowel = 5; break;
                case 0xb2: vowel = 6; break;
                case 0xb7: vowel = 8; break;
                case 0xbd: vowel = 12; break;
                case 0xbf: vowel = 13; break;
                case 0xc9: vowel = 18; break;
                case 0xd6: vowel = 20; break;
                default: return {};
            }
            if (stream.eof())
                return {};
            int final;
            switch (stream.consume())
            {
                case 0x7f: final = 0; break;
                case 0xe1: final = 4; break;
                case 0xe6: final = 8; break;
                case 0xf4: final = 21; break;
                case 0xf7: final = 23; break;
                default: return {};
            }
            unsigned syllable = 0xac00 + (leading * 21 + vowel) * 28 + final;
            result += static_cast<char>(0xe0 | (syllable >> 12));
            result += static_cast<char>(0x80 | ((syllable >> 6) & 0x3f));
            result += static_cast<char>(0x80 | (syllable & 0x3f));
            foundSyllable = true;
        }
        return foundSyllable ? result : std::string();
    }
}
#endif
