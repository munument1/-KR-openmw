#ifndef OPENMW_MWGUI_JOURNALINDEX_H
#define OPENMW_MWGUI_JOURNALINDEX_H

#include <array>
#include <components/misc/utf8stream.hpp>

namespace MWGui
{
    inline constexpr std::array<Utf8Stream::UnicodeChar, 14> koreanJournalInitials{
        0x3131, 0x3134, 0x3137, 0x3139, 0x3141, 0x3142, 0x3145,
        0x3147, 0x3148, 0x314a, 0x314b, 0x314c, 0x314d, 0x314e };

    constexpr Utf8Stream::UnicodeChar koreanJournalInitial(Utf8Stream::UnicodeChar first)
    {
        constexpr std::array<unsigned, 19> groups{ 0, 0, 1, 2, 2, 3, 4, 5, 5, 6, 6, 7, 8, 8, 9, 10, 11, 12, 13 };
        if (first >= 0xac00 && first <= 0xd7a3)
            return koreanJournalInitials[groups[(first - 0xac00) / (21 * 28)]];
        if (first >= 0x1100 && first <= 0x1112)
            return koreanJournalInitials[groups[first - 0x1100]];
        for (auto initial : koreanJournalInitials)
            if (first == initial)
                return initial;
        switch (first)
        {
            case 0x3132: return 0x3131;
            case 0x3138: return 0x3137;
            case 0x3143: return 0x3142;
            case 0x3146: return 0x3145;
            case 0x3149: return 0x3148;
            default: return 0;
        }
    }

    inline bool journalIndexMatches(Utf8Stream::UnicodeChar first, Utf8Stream::UnicodeChar selected)
    {
        first = Utf8Stream::toLowerUtf8(first);
        if (selected == '*')
            return first >= 'a' && first <= 'z';
        if (selected == '#')
            return !koreanJournalInitial(first) && !(first >= 'a' && first <= 'z');
        if (koreanJournalInitial(selected))
            return koreanJournalInitial(first) == koreanJournalInitial(selected);
        return first == Utf8Stream::toLowerUtf8(selected);
    }
}
#endif
