// Small binary-protocol adapter around YAMPT's unmodified topic_tagger_t.
// Build with yampt.core/source/{creator/topic_tagger,utility/keyword_trie}.cpp.
#include "creator/topic_tagger.hpp"
#include <cstdint>
#include <fstream>
#include <stdexcept>

static uint32_t readCount(std::istream& in)
{
    uint32_t n = 0;
    if (!in.read(reinterpret_cast<char*>(&n), sizeof(n)))
        throw std::runtime_error("Truncated input");
    return n;
}

static std::string readString(std::istream& in)
{
    const auto n = readCount(in);
    if (n > 16 * 1024 * 1024)
        throw std::runtime_error("Oversized string");
    std::string s(n, '\0');
    if (!in.read(s.data(), n))
        throw std::runtime_error("Truncated string");
    return s;
}

int main(int argc, char** argv)
{
    if (argc != 3)
        return 2;
    std::ifstream in(argv[1], std::ios::binary);
    std::ofstream out(argv[2], std::ios::binary);
    if (!in || !out)
        return 3;
    dict_t dictionary;
    auto count = readCount(in);
    while (count--)
    {
        auto name = readString(in);
        dictionary[rec_type_t::dial].records.push_back({name, name, name, status_t::translated});
    }
    topic_tagger_t tagger;
    tagger.seed_topics(dictionary);
    std::vector<std::pair<std::string,std::string>> inflections;
    count = readCount(in);
    while (count--)
    {
        auto phrase = readString(in);
        auto topic = readString(in);
        inflections.emplace_back(std::move(phrase),std::move(topic));
    }
    tagger.seed_inflections(inflections);
    count = readCount(in);
    out.write(reinterpret_cast<const char*>(&count), sizeof(count));
    while (count--)
    {
        const auto result = tagger.tag_line(readString(in));
        const uint32_t size = static_cast<uint32_t>(result.text.size());
        out.write(reinterpret_cast<const char*>(&size), sizeof(size));
        out.write(result.text.data(), size);
    }
    return out ? 0 : 4;
}
