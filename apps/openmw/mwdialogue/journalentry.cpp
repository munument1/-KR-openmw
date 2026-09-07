#include "journalentry.hpp"

#include <cstdint>
#include <stdexcept>

#include <components/esm3/journalentry.hpp>

#include <components/interpreter/defines.hpp>

#include "../mwbase/environment.hpp"
#include "../mwbase/world.hpp"

#include "../mwworld/esmstore.hpp"
#include "../mwworld/globals.hpp"

#include "../mwscript/interpretercontext.hpp"

namespace
{
    bool containsUtf8Hangul(std::string_view text)
    {
        const auto* bytes = reinterpret_cast<const unsigned char*>(text.data());
        for (std::size_t i = 0; i + 2 < text.size(); ++i)
        {
            if ((bytes[i] & 0xf0) != 0xe0 || (bytes[i + 1] & 0xc0) != 0x80 || (bytes[i + 2] & 0xc0) != 0x80)
                continue;

            const std::uint32_t codePoint = ((bytes[i] & 0x0f) << 12) | ((bytes[i + 1] & 0x3f) << 6)
                | (bytes[i + 2] & 0x3f);
            if ((codePoint >= 0x1100 && codePoint <= 0x11ff) || (codePoint >= 0x3130 && codePoint <= 0x318f)
                || (codePoint >= 0xac00 && codePoint <= 0xd7a3))
                return true;

            i += 2;
        }
        return false;
    }

    bool containsNonAscii(std::string_view text)
    {
        for (const unsigned char byte : text)
        {
            if (byte >= 0x80)
                return true;
        }
        return false;
    }

    void recoverLegacyKoreanJournalText(
        const ESM::RefId& topic, const ESM::RefId& infoId, std::string& savedText)
    {
        // Older Korean builds could save already-mojibaked journal strings. Only consider saved text that has
        // non-ASCII bytes but no Hangul, then require the same topic/INFO in the currently loaded content to contain
        // Hangul before replacing it. Normal Korean entries, plain ASCII entries and unrelated content are untouched.
        if (containsUtf8Hangul(savedText) || !containsNonAscii(savedText))
            return;

        const auto& dialogues = MWBase::Environment::get().getESMStore()->get<ESM::Dialogue>();
        const ESM::Dialogue* dialogue = dialogues.search(topic);
        if (!dialogue)
            return;

        for (const ESM::DialInfo& info : dialogue->mInfo)
        {
            if (info.mId != infoId || !containsUtf8Hangul(info.mResponse))
                continue;

            MWScript::InterpreterContext interpreterContext(nullptr, MWWorld::Ptr());
            savedText = Interpreter::fixDefinesDialog(info.mResponse, interpreterContext);
            return;
        }
    }
}

namespace MWDialogue
{
    Entry::Entry(const ESM::RefId& topic, const ESM::RefId& infoId, const MWWorld::Ptr& actor)
        : mInfoId(infoId)
    {
        const ESM::Dialogue* dialogue = MWBase::Environment::get().getESMStore()->get<ESM::Dialogue>().find(topic);

        for (ESM::Dialogue::InfoContainer::const_iterator iter(dialogue->mInfo.begin()); iter != dialogue->mInfo.end();
             ++iter)
            if (iter->mId == mInfoId)
            {
                if (actor.isEmpty())
                {
                    MWScript::InterpreterContext interpreterContext(nullptr, MWWorld::Ptr());
                    mText = Interpreter::fixDefinesDialog(iter->mResponse, interpreterContext);
                }
                else
                {
                    MWScript::InterpreterContext interpreterContext(&actor.getRefData().getLocals(), actor);
                    mText = Interpreter::fixDefinesDialog(iter->mResponse, interpreterContext);
                }

                return;
            }

        throw std::runtime_error("unknown info ID " + mInfoId.toDebugString() + " for topic " + topic.toDebugString());
    }

    Entry::Entry(const ESM::JournalEntry& record)
        : mInfoId(record.mInfo)
        , mText(record.mText)
        , mActorName(record.mActorName)
    {
    }

    const std::string& Entry::getText() const
    {
        return mText;
    }

    void Entry::write(ESM::JournalEntry& entry) const
    {
        entry.mInfo = mInfoId;
        entry.mText = mText;
        entry.mActorName = mActorName;
    }

    JournalEntry::JournalEntry(const ESM::RefId& topic, const ESM::RefId& infoId, const MWWorld::Ptr& actor)
        : Entry(topic, infoId, actor)
        , mTopic(topic)
    {
    }

    JournalEntry::JournalEntry(const ESM::JournalEntry& record)
        : Entry(record)
        , mTopic(record.mTopic)
    {
        recoverLegacyKoreanJournalText(mTopic, mInfoId, mText);
    }

    void JournalEntry::write(ESM::JournalEntry& entry) const
    {
        Entry::write(entry);
        entry.mTopic = mTopic;
    }

    JournalEntry JournalEntry::makeFromQuest(const ESM::RefId& topic, int index)
    {
        return JournalEntry(topic, idFromIndex(topic, index), MWWorld::Ptr());
    }

    const ESM::RefId& JournalEntry::idFromIndex(const ESM::RefId& topic, int index)
    {
        const ESM::Dialogue* dialogue = MWBase::Environment::get().getESMStore()->get<ESM::Dialogue>().find(topic);

        for (ESM::Dialogue::InfoContainer::const_iterator iter(dialogue->mInfo.begin()); iter != dialogue->mInfo.end();
             ++iter)
            if (iter->mData.mJournalIndex == index)
            {
                return iter->mId;
            }

        throw std::runtime_error("unknown journal index for topic " + topic.toDebugString());
    }

    StampedJournalEntry::StampedJournalEntry()
        : mDay(0)
        , mMonth(0)
        , mDayOfMonth(0)
    {
    }

    StampedJournalEntry::StampedJournalEntry(const ESM::RefId& topic, const ESM::RefId& infoId, int day, int month,
        int dayOfMonth, const MWWorld::Ptr& actor)
        : JournalEntry(topic, infoId, actor)
        , mDay(day)
        , mMonth(month)
        , mDayOfMonth(dayOfMonth)
    {
    }

    StampedJournalEntry::StampedJournalEntry(const ESM::JournalEntry& record)
        : JournalEntry(record)
        , mDay(record.mDay)
        , mMonth(record.mMonth)
        , mDayOfMonth(record.mDayOfMonth)
    {
    }

    void StampedJournalEntry::write(ESM::JournalEntry& entry) const
    {
        JournalEntry::write(entry);
        entry.mDay = mDay;
        entry.mMonth = mMonth;
        entry.mDayOfMonth = mDayOfMonth;
    }

    StampedJournalEntry StampedJournalEntry::makeFromQuest(
        const ESM::RefId& topic, int index, const MWWorld::Ptr& actor)
    {
        const int day = MWBase::Environment::get().getWorld()->getGlobalInt(MWWorld::Globals::sDaysPassed);
        const int month = MWBase::Environment::get().getWorld()->getGlobalInt(MWWorld::Globals::sMonth);
        const int dayOfMonth = MWBase::Environment::get().getWorld()->getGlobalInt(MWWorld::Globals::sDay);

        return StampedJournalEntry(topic, idFromIndex(topic, index), day, month, dayOfMonth, actor);
    }
}
