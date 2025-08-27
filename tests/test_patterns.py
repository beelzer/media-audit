"""Tests for pattern matching."""

from media_audit.domain.patterns import (
    MediaPatterns,
    get_patterns,
)

# Import predefined patterns directly from module
from media_audit.domain.patterns.patterns import (
    EMBY_PATTERNS,
    JELLYFIN_PATTERNS,
    PLEX_PATTERNS,
)


def test_plex_patterns():
    """Test Plex pattern definitions."""
    assert "^poster\\." in PLEX_PATTERNS.poster_patterns
    assert "^folder\\." in PLEX_PATTERNS.poster_patterns
    assert "^fanart\\." in PLEX_PATTERNS.background_patterns
    assert "-trailer\\." in PLEX_PATTERNS.trailer_patterns


def test_jellyfin_patterns():
    """Test Jellyfin pattern definitions."""
    assert "^poster\\." in JELLYFIN_PATTERNS.poster_patterns
    assert "^backdrop\\." in JELLYFIN_PATTERNS.background_patterns
    assert "^banner\\." in JELLYFIN_PATTERNS.banner_patterns


def test_emby_patterns():
    """Test Emby pattern definitions."""
    assert "^folder\\." in EMBY_PATTERNS.poster_patterns
    assert "^backdrop\\." in EMBY_PATTERNS.background_patterns
    assert "^extrafanart/.*" in EMBY_PATTERNS.background_patterns


def test_get_patterns_default():
    """Test getting default (combined) patterns."""
    patterns = get_patterns()

    # Should have patterns from all presets
    assert len(patterns.poster_patterns) > 0
    assert len(patterns.background_patterns) > 0


def test_get_patterns_specific():
    """Test getting specific profile patterns."""
    patterns = get_patterns(["plex"])

    # Should only have Plex patterns
    assert "^poster\\." in patterns.poster_patterns
    assert "^folder\\." in patterns.poster_patterns


def test_get_patterns_multiple():
    """Test getting multiple profile patterns."""
    patterns = get_patterns(["plex", "jellyfin"])

    # Should have patterns from both
    assert "^poster\\." in patterns.poster_patterns
    assert "^backdrop\\." in patterns.background_patterns


def test_pattern_compilation():
    """Test pattern compilation to regex."""
    patterns = MediaPatterns(
        poster_patterns=[r"^poster\."],
        background_patterns=[r"^fanart\."],
    )

    compiled = patterns.compile_patterns()

    assert len(compiled.poster_re) == 1
    assert len(compiled.background_re) == 1

    # Test regex matching
    assert compiled.poster_re[0].match("poster.jpg")
    assert not compiled.poster_re[0].match("movie.jpg")
    assert compiled.background_re[0].match("fanart.png")
    assert not compiled.background_re[0].match("backdrop.png")
