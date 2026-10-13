#include <apps/openmw/mwgui/journalindex.hpp>
#include <iostream>

int main()
{
    using namespace MWGui;
    // Every modern Hangul syllable belongs to exactly one of the 14 displayed groups.
    for (unsigned c = 0xac00; c <= 0xd7a3; ++c)
    {
        unsigned matches = 0;
        for (auto initial : koreanJournalInitials)
            matches += journalIndexMatches(c, initial);
        if (matches != 1 || journalIndexMatches(c, '*') || journalIndexMatches(c, '#'))
            return 1;
    }
    for (unsigned c = 'A'; c <= 'Z'; ++c)
        if (!journalIndexMatches(c, '*') || !journalIndexMatches(c, c + 32) || journalIndexMatches(c, '#'))
            return 2;
    if (!journalIndexMatches('3', '#') || !journalIndexMatches(0x4e00, '#')
        || !journalIndexMatches(0x1101, 0x3131) || !journalIndexMatches(0x3149, 0x3148))
        return 3;
    std::cout << "PASS: 11172 Hangul syllables, tense initials, Latin case, other characters\n";
}
