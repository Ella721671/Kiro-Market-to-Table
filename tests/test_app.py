"""
Tests for Main/app.py
=====================
Covers all 11 correctness properties (via Hypothesis) and all named
example-based unit tests from the design document.

Property tests are tagged with:
    # Feature: streamlit-app-ui, Property N: <property name>
"""

import base64
import sys
import tempfile
import types
from pathlib import Path

import pytest
from hypothesis import given, settings
import hypothesis.strategies as st

# ---------------------------------------------------------------------------
# Shared test fixtures / constants
# ---------------------------------------------------------------------------

# Minimal structurally-valid 1×1 red PNG (67 bytes).
MINIMAL_PNG = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk length + type
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # width=1, height=1
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # bit depth, color type, ...
    0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
    0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
    0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC,
    0x33, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
    0x44, 0xAE, 0x42, 0x60, 0x82,
])

# ---------------------------------------------------------------------------
# Lightweight Streamlit stub so app.py can be imported without a running
# Streamlit server.  We replace 'streamlit' in sys.modules before the first
# import of app.py.
# ---------------------------------------------------------------------------

def _make_streamlit_stub() -> types.ModuleType:
    """Return a minimal mock of the streamlit module."""
    stub = types.ModuleType("streamlit")

    # Decorators / functions used at module-import time
    def _cache_data(**kwargs):
        def decorator(fn):
            return fn
        return decorator

    stub.cache_data = _cache_data
    stub.markdown = lambda *a, **kw: None
    stub.session_state = {}

    # Attributes that app.py references at module level
    stub.set_page_config = lambda **kw: None

    return stub


# Install the stub before importing app so the top-level st.cache_data call
# and the assets-dir mkdir guard work without a real Streamlit runtime.
if "streamlit" not in sys.modules:
    sys.modules["streamlit"] = _make_streamlit_stub()

# Now we can safely import the module under test.
_main_dir = str(Path(__file__).resolve().parent.parent / "Main")
if _main_dir not in sys.path:
    sys.path.insert(0, _main_dir)

import app  # noqa: E402  (import after sys.path manipulation is intentional)


# ---------------------------------------------------------------------------
# Section 2 unit tests — get_base64_image
# ---------------------------------------------------------------------------

class TestGetBase64Image:
    """Unit tests for get_base64_image (Requirements 5.6)."""

    def test_get_base64_image_returns_none_missing(self, tmp_path, monkeypatch):
        """get_base64_image returns None when no asset file exists for the name."""
        # Redirect assets dir to an empty temporary directory.
        fake_assets = tmp_path / "assets"
        fake_assets.mkdir()
        # Point app.__file__ at tmp_path so get_base64_image resolves assets there.
        monkeypatch.setattr(app, "__file__", str(tmp_path / "app.py"))

        result = app.get_base64_image("completely_nonexistent_commodity_xyz")
        assert result is None

    def test_get_base64_image_returns_uri_present(self, tmp_path, monkeypatch):
        """get_base64_image returns a data:image/ URI when a PNG exists in assets."""
        # Create Main/assets/ under tmp_path and place a minimal valid PNG there.
        fake_assets = tmp_path / "assets"
        fake_assets.mkdir()

        # Minimal 1×1 red PNG bytes (67 bytes, structurally valid).
        minimal_png = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk length + type
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # width=1, height=1
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # bit depth, color type, ...
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
            0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC,
            0x33, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
            0x44, 0xAE, 0x42, 0x60, 0x82,
        ])
        (fake_assets / "wheat.png").write_bytes(minimal_png)

        # Redirect app.__file__ so get_base64_image finds the asset in tmp_path/assets.
        monkeypatch.setattr(app, "__file__", str(tmp_path / "app.py"))

        result = app.get_base64_image("wheat")

        assert result is not None, "Expected a data URI, got None"
        assert result.startswith("data:image/"), (
            f"Expected URI to start with 'data:image/', got: {result[:30]!r}"
        )

    # Feature: streamlit-app-ui, Property 9: Base64 Image Round-Trip Integrity
    @settings(max_examples=100)
    @given(st.sampled_from(app.COMMODITY_KEYS))
    def test_property9_base64_round_trip(self, commodity_name):
        """Validates: Requirements 5.3, 5.6

        For any commodity key, when a matching PNG exists in assets/, the return
        value of get_base64_image must start with 'data:image/' and its base64
        payload must decode without error.
        """
        # Feature: streamlit-app-ui, Property 9: Base64 Image Round-Trip Integrity
        with tempfile.TemporaryDirectory() as tmpdir:
            assets_dir = Path(tmpdir) / "assets"
            assets_dir.mkdir()
            (assets_dir / f"{commodity_name}.png").write_bytes(MINIMAL_PNG)

            original_file = app.__file__
            app.__file__ = str(Path(tmpdir) / "app.py")
            try:
                result = app.get_base64_image(commodity_name)
            finally:
                app.__file__ = original_file

        assert result is not None, (
            f"get_base64_image returned None for '{commodity_name}' even though a PNG exists"
        )
        assert result.startswith("data:image/"), (
            f"URI does not start with 'data:image/' for '{commodity_name}': {result[:40]!r}"
        )
        # Verify the base64 payload decodes without error
        b64_part = result.split(",", 1)[1]
        base64.b64decode(b64_part)  # raises binascii.Error if the payload is invalid


# ---------------------------------------------------------------------------
# Property 10 — Theme CSS Colour Token Consistency
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(st.booleans())
def test_property10_css_token_consistency(is_burnout):
    # Feature: streamlit-app-ui, Property 10: Theme CSS Colour Token Consistency
    # Validates: Requirements 2.2, 2.3
    if is_burnout:
        primary          = app.COLOUR_TOKENS["warm_ochre"]    # #D99B21
        deep             = app.COLOUR_TOKENS["deep_roasted"]  # #5A3E0A
        opposing_primary = app.COLOUR_TOKENS["sage_olive"]    # #838921
        opposing_deep    = app.COLOUR_TOKENS["deep_forest"]   # #3A3D0E
    else:
        primary          = app.COLOUR_TOKENS["sage_olive"]    # #838921
        deep             = app.COLOUR_TOKENS["deep_forest"]   # #3A3D0E
        opposing_primary = app.COLOUR_TOKENS["warm_ochre"]    # #D99B21  — also hardcoded as over-budget colour
        opposing_deep    = app.COLOUR_TOKENS["deep_roasted"]  # #5A3E0A

    captured: list[str] = []
    sys.modules["streamlit"].markdown = lambda content, **kw: captured.append(content)

    app.inject_theme_css(primary=primary, deep=deep, is_burnout=is_burnout)
    css = "\n".join(captured)

    assert primary in css, f"Expected primary {primary} in CSS"
    assert deep in css, f"Expected deep {deep} in CSS"

    # opposing_deep must never appear regardless of mode.
    assert opposing_deep not in css, (
        f"Opposing deep {opposing_deep} should not appear in CSS"
    )

    # opposing_primary is only safe to assert absent in burnout mode.
    # In calm mode, #D99B21 (warm_ochre) is hardcoded as the over-budget bar
    # fill colour and will always be present in the CSS output.
    if is_burnout:
        assert opposing_primary not in css, (
            f"Opposing primary {opposing_primary} should not appear in CSS when burnout=True"
        )


# ---------------------------------------------------------------------------
# Section 3 unit tests — inject_theme_css
# ---------------------------------------------------------------------------

class TestInjectThemeCss:
    """Unit tests for inject_theme_css (Requirements 2.2, 2.3)."""

    def test_inject_theme_css_calm_tokens(self):
        """Calm mode: Sage Olive tokens present, Warm Ochre deep token absent in CSS."""
        captured = []
        import sys
        sys.modules["streamlit"].markdown = lambda content, **kw: captured.append(content)

        app.inject_theme_css(
            primary=app.COLOUR_TOKENS["sage_olive"],   # #838921
            deep=app.COLOUR_TOKENS["deep_forest"],     # #3A3D0E
            is_burnout=False,
        )
        css = "\n".join(captured)

        assert app.COLOUR_TOKENS["sage_olive"] in css    # #838921 must be present
        assert app.COLOUR_TOKENS["deep_forest"] in css   # #3A3D0E must be present
        # Warm Ochre deep must NOT appear (it's not the over-budget value)
        assert app.COLOUR_TOKENS["deep_roasted"] not in css  # #5A3E0A must be absent

    def test_inject_theme_css_burnout_tokens(self):
        """Burnout mode: Warm Ochre tokens present, Sage Olive tokens absent in CSS."""
        captured = []
        import sys
        sys.modules["streamlit"].markdown = lambda content, **kw: captured.append(content)

        app.inject_theme_css(
            primary=app.COLOUR_TOKENS["warm_ochre"],    # #D99B21
            deep=app.COLOUR_TOKENS["deep_roasted"],     # #5A3E0A
            is_burnout=True,
        )
        css = "\n".join(captured)

        assert app.COLOUR_TOKENS["warm_ochre"] in css    # #D99B21 must be present
        assert app.COLOUR_TOKENS["deep_roasted"] in css  # #5A3E0A must be present
        # Sage Olive primary and deep must NOT appear
        assert app.COLOUR_TOKENS["sage_olive"] not in css    # #838921 must be absent
        assert app.COLOUR_TOKENS["deep_forest"] not in css   # #3A3D0E must be absent


# ---------------------------------------------------------------------------
# Section 3 property tests — compute_checkout (Property 1)
# ---------------------------------------------------------------------------

from decimal import Decimal  # noqa: E402 (grouped with section)

# Strategy: list of (float price >=0, int qty 0..99, bool cupboard)
_item_strategy = st.tuples(
    st.floats(min_value=0.0, max_value=99.99, allow_nan=False, allow_infinity=False),
    st.integers(min_value=0, max_value=99),
    st.booleans(),
)


@settings(max_examples=100)
@given(st.lists(_item_strategy, min_size=0, max_size=20))
def test_property1_checkout_precision(items):
    # Feature: streamlit-app-ui, Property 1: Checkout Total Round-Trip Precision
    # Validates: Requirements 10.2
    basket = [
        {
            "commodity": f"item_{i}",
            "estimated_price_gbp": price,
            "prep_time_mins": 0,
        }
        for i, (price, qty, cupboard) in enumerate(items)
    ]
    session_state = {
        f"test_item_{i}_qty": qty
        for i, (price, qty, cupboard) in enumerate(items)
    }
    session_state.update({
        f"test_item_{i}_cupboard": cupboard
        for i, (price, qty, cupboard) in enumerate(items)
    })
    mode = "test"

    total, _, _ = app.compute_checkout(basket, session_state, mode)

    expected = sum(
        Decimal(str(price)) * qty
        for price, qty, cupboard in items
        if not cupboard and qty > 0
    )
    assert total == expected, f"Expected {expected}, got {total}"


# ---------------------------------------------------------------------------
# Property 2 — Cupboard Exclusion Invariant
# ---------------------------------------------------------------------------

from decimal import Decimal as _Decimal


@settings(max_examples=100)
@given(
    st.lists(
        st.tuples(
            st.floats(min_value=0.01, max_value=99.99, allow_nan=False, allow_infinity=False),
            st.integers(min_value=1, max_value=99),
            st.booleans(),
        ),
        min_size=1, max_size=20,
    )
)
def test_property2_cupboard_exclusion(items):
    # Feature: streamlit-app-ui, Property 2: Cupboard Exclusion Invariant
    # Validates: Requirements 7.9, 10.2
    # At least one item must be in the cupboard; skip the test if none are.
    from hypothesis import assume
    assume(any(cupboard for _, _, cupboard in items))

    mode = "test"
    basket = [
        {
            "commodity": f"item_{i}",
            "estimated_price_gbp": price,
            "prep_time_mins": 0,
        }
        for i, (price, qty, cupboard) in enumerate(items)
    ]
    session_state = {}
    for i, (price, qty, cupboard) in enumerate(items):
        session_state[f"{mode}_item_{i}_qty"] = qty
        session_state[f"{mode}_item_{i}_cupboard"] = cupboard

    total_with_cupboard, _, _ = app.compute_checkout(basket, session_state, mode)

    # The expected total is the sum of price * qty for all non-cupboard items.
    expected = sum(
        _Decimal(str(price)) * qty
        for price, qty, cupboard in items
        if not cupboard
    )
    assert total_with_cupboard == expected, (
        f"Expected total {expected} but got {total_with_cupboard}. "
        f"Cupboard items must be excluded from checkout total."
    )


# ---------------------------------------------------------------------------
# Property 3 — Zero Quantity Exclusion Invariant
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(
    st.lists(
        st.tuples(
            st.floats(min_value=0.01, max_value=99.99, allow_nan=False, allow_infinity=False),
            st.integers(min_value=0, max_value=99),
            st.booleans(),
        ),
        min_size=1, max_size=20,
    )
)
def test_property3_zero_qty_exclusion(items):
    # Feature: streamlit-app-ui, Property 3: Zero Quantity Exclusion Invariant
    # Validates: Requirements 7.5, 7.6, 9.2
    from hypothesis import assume
    assume(any(qty == 0 for _, qty, _ in items))

    mode = "test"
    basket = [
        {"commodity": f"item_{i}", "estimated_price_gbp": price, "prep_time_mins": 0}
        for i, (price, qty, cupboard) in enumerate(items)
    ]
    session_state = {}
    for i, (price, qty, cupboard) in enumerate(items):
        session_state[f"{mode}_item_{i}_qty"] = qty
        session_state[f"{mode}_item_{i}_cupboard"] = cupboard

    total, _, count = app.compute_checkout(basket, session_state, mode)

    # Zero-qty items should not contribute to total
    expected = sum(
        Decimal(str(price)) * qty
        for price, qty, cupboard in items
        if qty > 0 and not cupboard
    )
    assert total == expected, (
        f"Expected {expected} but got {total}. Zero-qty items must be excluded."
    )
    # Also verify item count excludes zero-qty items
    expected_count = sum(1 for _, qty, cupboard in items if qty > 0 and not cupboard)
    assert count == expected_count


# ---------------------------------------------------------------------------
# Section 3 unit tests — compute_checkout (Task 3.6)
# ---------------------------------------------------------------------------

class TestComputeCheckout:
    """Unit tests for compute_checkout (Requirements 7.5, 7.6, 7.9, 10.2)."""

    def test_compute_checkout_excludes_cupboard(self):
        """Items with cupboard=True are excluded from checkout total."""
        basket = [
            {"commodity": "wheat", "estimated_price_gbp": 1.50, "prep_time_mins": 5},
            {"commodity": "rice",  "estimated_price_gbp": 2.00, "prep_time_mins": 10},
        ]
        session_state = {
            "test_wheat_qty": 2,
            "test_wheat_cupboard": True,   # excluded
            "test_rice_qty": 1,
            "test_rice_cupboard": False,   # included
        }
        total, prep, count = app.compute_checkout(basket, session_state, "test")
        assert total == Decimal("2.00")
        assert prep == 10
        assert count == 1

    def test_compute_checkout_excludes_zero_qty(self):
        """Items with qty=0 are excluded from checkout total."""
        basket = [
            {"commodity": "corn",  "estimated_price_gbp": 0.80, "prep_time_mins": 3},
            {"commodity": "oats",  "estimated_price_gbp": 1.20, "prep_time_mins": 6},
        ]
        session_state = {
            "test_corn_qty": 0,     # excluded
            "test_corn_cupboard": False,
            "test_oats_qty": 3,     # included
            "test_oats_cupboard": False,
        }
        total, prep, count = app.compute_checkout(basket, session_state, "test")
        assert total == Decimal("3.60")
        assert prep == 6
        assert count == 1
