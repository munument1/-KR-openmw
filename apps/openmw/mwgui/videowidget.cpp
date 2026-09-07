#include "videowidget.hpp"

#include <osg-ffmpeg-videoplayer/videoplayer.hpp>

#include <algorithm>
#include <cstdio>
#include <string_view>

#include <MyGUI_RenderManager.h>
#include <MyGUI_TextBox.h>

#include <osg/Texture2D>

#include <components/debug/debuglog.hpp>
#include <components/myguiplatform/myguitexture.hpp>
#include <components/vfs/manager.hpp>

#include "../mwsound/movieaudiofactory.hpp"

namespace MWGui
{
    namespace
    {
        void trimLineEnd(std::string& line)
        {
            while (!line.empty() && (line.back() == '\r' || line.back() == '\n'))
                line.pop_back();
        }

        bool parseSrtTime(std::string_view value, double& seconds)
        {
            int hours = 0;
            int minutes = 0;
            int wholeSeconds = 0;
            int milliseconds = 0;
            const std::string text(value);
            if (std::sscanf(text.c_str(), "%d:%d:%d,%d", &hours, &minutes, &wholeSeconds, &milliseconds) != 4
                && std::sscanf(text.c_str(), "%d:%d:%d.%d", &hours, &minutes, &wholeSeconds, &milliseconds) != 4)
                return false;

            seconds = hours * 3600.0 + minutes * 60.0 + wholeSeconds + milliseconds / 1000.0;
            return true;
        }

        bool parseSrtRange(const std::string& line, double& start, double& end)
        {
            const std::size_t arrow = line.find("-->");
            if (arrow == std::string::npos)
                return false;

            std::string_view left(line.data(), arrow);
            std::string_view right(line.data() + arrow + 3, line.size() - arrow - 3);
            while (!left.empty() && left.front() == ' ')
                left.remove_prefix(1);
            while (!left.empty() && left.back() == ' ')
                left.remove_suffix(1);
            while (!right.empty() && right.front() == ' ')
                right.remove_prefix(1);
            while (!right.empty() && right.back() == ' ')
                right.remove_suffix(1);
            return parseSrtTime(left, start) && parseSrtTime(right, end);
        }
    }

    VideoWidget::VideoWidget()
        : mVFS(nullptr)
        , mSubtitleShadow(nullptr)
        , mSubtitleText(nullptr)
    {
        mPlayer = std::make_unique<Video::VideoPlayer>();
        setNeedKeyFocus(true);

        mSubtitleShadow = createWidget<MyGUI::TextBox>("SandText", MyGUI::IntCoord(), MyGUI::Align::Default);
        mSubtitleText = createWidget<MyGUI::TextBox>("SandText", MyGUI::IntCoord(), MyGUI::Align::Default);
        for (MyGUI::TextBox* text : { mSubtitleShadow, mSubtitleText })
        {
            text->setNeedMouseFocus(false);
            text->setNeedKeyFocus(false);
            text->setTextAlign(MyGUI::Align::HCenter | MyGUI::Align::Bottom);
            text->getSubWidgetText()->setWordWrap(true);
            text->setVisible(false);
        }
        mSubtitleShadow->setTextColour(MyGUI::Colour::Black);
        mSubtitleText->setTextColour(MyGUI::Colour::White);
    }

    VideoWidget::~VideoWidget() = default;

    void VideoWidget::setVFS(const VFS::Manager* vfs)
    {
        mVFS = vfs;
    }

    void VideoWidget::playVideo(const std::string& video)
    {
        mPlayer->setAudioFactory(new MWSound::MovieAudioFactory());

        Files::IStreamPtr videoStream;
        try
        {
            videoStream = mVFS->get(video);
        }
        catch (std::exception& e)
        {
            Log(Debug::Error) << "Failed to open video: " << e.what();
            return;
        }

        mPlayer->playVideo(std::move(videoStream), video);
        loadSubtitles(video);

        osg::ref_ptr<osg::Texture2D> texture = mPlayer->getVideoTexture();
        if (!texture)
            return;

        mTexture = std::make_unique<MyGUIPlatform::OSGTexture>(texture);

        setRenderItemTexture(mTexture.get());
        // Both the widget and the video frame are Y-down, so this UV is not inverted
        getSubWidgetMain()->_setUVSet(MyGUI::FloatRect(0.f, 0.f, 1.f, 1.f));
    }

    int VideoWidget::getVideoWidth()
    {
        return mPlayer->getVideoWidth();
    }

    int VideoWidget::getVideoHeight()
    {
        return mPlayer->getVideoHeight();
    }

    bool VideoWidget::update()
    {
        const bool playing = mPlayer->update();
        if (playing)
            updateSubtitle();
        else
            setSubtitleCaption({});
        return playing;
    }

    void VideoWidget::commitFrame()
    {
        mPlayer->commitFrame();
    }

    void VideoWidget::stop()
    {
        setSubtitleCaption({});
        mSubtitles.clear();
        mPlayer->close();
    }

    void VideoWidget::loadSubtitles(const std::string& video)
    {
        mSubtitles.clear();
        setSubtitleCaption({});

        const std::size_t dot = video.find_last_of('.');
        if (dot == std::string::npos)
            return;

        std::string subtitlePath = video.substr(0, dot) + ".srt";
        Files::IStreamPtr subtitleStream;
        try
        {
            subtitleStream = mVFS->get(subtitlePath);
        }
        catch (const std::exception&)
        {
            return;
        }

        std::string line;
        bool firstLine = true;
        while (std::getline(*subtitleStream, line))
        {
            trimLineEnd(line);
            if (firstLine)
            {
                firstLine = false;
                if (line.size() >= 3 && static_cast<unsigned char>(line[0]) == 0xef
                    && static_cast<unsigned char>(line[1]) == 0xbb
                    && static_cast<unsigned char>(line[2]) == 0xbf)
                    line.erase(0, 3);
            }
            if (line.empty())
                continue;

            std::string timing = line;
            if (timing.find("-->") == std::string::npos)
            {
                if (!std::getline(*subtitleStream, timing))
                    break;
                trimLineEnd(timing);
            }

            SubtitleCue cue;
            if (!parseSrtRange(timing, cue.mStart, cue.mEnd))
                continue;

            std::string textLine;
            while (std::getline(*subtitleStream, textLine))
            {
                trimLineEnd(textLine);
                if (textLine.empty())
                    break;
                if (!cue.mText.empty())
                    cue.mText += '\n';
                cue.mText += textLine;
            }

            if (!cue.mText.empty() && cue.mEnd >= cue.mStart)
                mSubtitles.push_back(std::move(cue));
        }

        if (!mSubtitles.empty())
            Log(Debug::Info) << "Loaded " << mSubtitles.size() << " subtitles from " << subtitlePath;
    }

    void VideoWidget::updateSubtitle()
    {
        const double time = mPlayer->getCurrentTime();
        std::string caption;
        for (const SubtitleCue& cue : mSubtitles)
        {
            if (time >= cue.mStart && time <= cue.mEnd)
            {
                caption = cue.mText;
                break;
            }
        }
        setSubtitleCaption(caption);
    }

    void VideoWidget::setSubtitleCaption(const std::string& caption)
    {
        if (caption == mSubtitleCaption)
            return;

        mSubtitleCaption = caption;
        const bool visible = !caption.empty();
        mSubtitleShadow->setCaption(caption);
        mSubtitleText->setCaption(caption);
        mSubtitleShadow->setVisible(visible);
        mSubtitleText->setVisible(visible);
    }

    void VideoWidget::layoutSubtitle()
    {
        if (!mSubtitleText || !mSubtitleShadow)
            return;

        const int width = getWidth();
        const int height = getHeight();
        const int marginX = std::max(12, width / 16);
        const int marginBottom = std::max(10, height / 24);
        const int boxHeight = std::max(50, height / 4);
        const int boxTop = std::max(0, height - marginBottom - boxHeight);
        const int boxWidth = std::max(1, width - marginX * 2);
        const int shadowOffset = std::max(1, height / 360);
        const unsigned int fontHeight = static_cast<unsigned int>(std::clamp(height / 24, 18, 48));

        mSubtitleShadow->setCoord(marginX + shadowOffset, boxTop + shadowOffset, boxWidth, boxHeight);
        mSubtitleText->setCoord(marginX, boxTop, boxWidth, boxHeight);
        mSubtitleShadow->setFontHeight(fontHeight);
        mSubtitleText->setFontHeight(fontHeight);
    }

    void VideoWidget::pause()
    {
        mPlayer->pause();
    }

    void VideoWidget::resume()
    {
        mPlayer->play();
    }

    bool VideoWidget::isPaused() const
    {
        return mPlayer->isPaused();
    }

    bool VideoWidget::hasAudioStream()
    {
        return mPlayer->hasAudioStream();
    }

    void VideoWidget::autoResize(bool stretch)
    {
        MyGUI::IntSize screenSize = MyGUI::RenderManager::getInstance().getViewSize();
        if (getParent())
            screenSize = getParent()->getSize();

        if (getVideoHeight() > 0 && !stretch)
        {
            double imageaspect = static_cast<double>(getVideoWidth()) / getVideoHeight();

            int leftPadding = std::max(0, static_cast<int>(screenSize.width - screenSize.height * imageaspect) / 2);
            int topPadding = std::max(0, static_cast<int>(screenSize.height - screenSize.width / imageaspect) / 2);

            setCoord(leftPadding, topPadding, screenSize.width - leftPadding * 2, screenSize.height - topPadding * 2);
        }
        else
            setCoord(0, 0, screenSize.width, screenSize.height);

        layoutSubtitle();
    }

}
