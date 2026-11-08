"""Unit tests for HLS and DASH manifest parsing."""

from app.engine.media.manifest_parser import ManifestParser
from app.engine.media.models import MediaVariant


def test_parse_hls_multivariant() -> None:
    hls_sample = """#EXTM3U
#EXT-X-VERSION:6
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio-aac",NAME="English",DEFAULT=YES,URI="audio/en/playlist.m3u8"
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,CODECS="avc1.4d401e,mp4a.40.2",AUDIO="audio-aac"
360p/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720,CODECS="avc1.4d401f,mp4a.40.2",AUDIO="audio-aac"
720p/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",AUDIO="audio-aac"
1080p/playlist.m3u8
"""
    base_url = "https://example.com/stream/master.m3u8"
    variants = ManifestParser.parse_hls(hls_sample, base_url=base_url)

    # 3 video variants + 1 audio variant
    assert len(variants) == 4

    # Highest quality first
    v_top = variants[0]
    assert v_top.quality_label == "1080p"
    assert v_top.resolution == "1920x1080"
    assert v_top.width == 1920
    assert v_top.height == 1080
    assert v_top.bitrate_bps == 5000000
    assert v_top.url == "https://example.com/stream/1080p/playlist.m3u8"
    assert not v_top.is_audio_only
    assert not v_top.is_drm_protected

    # Audio variant
    v_audio = [v for v in variants if v.is_audio_only][0]
    assert "Audio" in v_audio.quality_label
    assert v_audio.url == "https://example.com/stream/audio/en/playlist.m3u8"
    assert v_audio.container == "m4a"


def test_parse_hls_drm_detection() -> None:
    hls_drm = """#EXTM3U
#EXT-X-VERSION:5
#EXT-X-KEY:METHOD=SAMPLE-AES,URI="skd://fairplay.license"
#EXT-X-STREAM-INF:BANDWIDTH=1500000,RESOLUTION=1280x720
720p.m3u8
"""
    variants = ManifestParser.parse_hls(hls_drm, base_url="https://example.com/")
    assert len(variants) == 1
    assert variants[0].is_drm_protected is True


def test_parse_dash_mpd() -> None:
    dash_sample = """<?xml version="1.0" encoding="utf-8"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" minBufferTime="PT1.5S" type="static" mediaPresentationDuration="PT30S">
  <Period>
    <AdaptationSet mimeType="video/mp4" contentType="video">
      <Representation id="video_720" bandwidth="2000000" width="1280" height="720" codecs="avc1.4d401f" />
      <Representation id="video_1080" bandwidth="4500000" width="1920" height="1080" codecs="avc1.640028" />
    </AdaptationSet>
    <AdaptationSet mimeType="audio/mp4" contentType="audio">
      <Representation id="audio_en" bandwidth="128000" codecs="mp4a.40.2" />
    </AdaptationSet>
  </Period>
</MPD>
"""
    variants = ManifestParser.parse_dash(dash_sample, base_url="https://example.com/manifest.mpd")
    assert len(variants) == 3

    top_v = variants[0]
    assert top_v.quality_label == "1080p"
    assert top_v.resolution == "1920x1080"
    assert top_v.height == 1080
    assert top_v.bitrate_bps == 4500000

    audio_v = [v for v in variants if v.is_audio_only][0]
    assert "audio_en" in audio_v.quality_label


def test_media_variant_display_title() -> None:
    v = MediaVariant(
        id="test_1",
        url="https://example.com/video.mp4",
        quality_label="1080p",
        container="mp4",
        resolution="1920x1080",
        bitrate_bps=4500000,
        estimated_size_bytes=52428800,
    )
    title = v.display_title
    assert "1080p" in title
    assert "MP4" in title
    assert "1920x1080" in title
    assert "4500 kbps" in title
    assert "50.0 MB" in title

