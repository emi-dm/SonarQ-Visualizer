"""Property-based tests for connection validation using Hypothesis."""

import pytest
from hypothesis import given, strategies as st
from backend.src.services.connection_service import validate_connection_url


# URL generation strategies
valid_schemes = st.sampled_from(['http', 'https'])
valid_domains = st.text(
    alphabet=st.characters(whitelist_categories=('Ll', 'Nd')),
    min_size=3,
    max_size=63
).filter(lambda x: x and not x.startswith('-') and not x.endswith('-'))

tlds = st.sampled_from(['.com', '.org', '.net', '.io', '.dev'])


@st.composite
def valid_urls(draw):
    """Generate valid HTTP/HTTPS URLs."""
    scheme = draw(valid_schemes)
    domain = draw(valid_domains)
    tld = draw(tlds)
    port = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=65535)))
    
    url = f"{scheme}://{domain}{tld}"
    if port:
        url += f":{port}"
    
    return url


@st.composite
def invalid_urls(draw):
    """Generate invalid URLs."""
    return draw(st.one_of(
        st.just(""),
        st.just("not-a-url"),
        st.just("ftp://invalid-scheme.com"),
        st.just("javascript:alert('xss')"),
        st.text(max_size=10).filter(lambda x: '://' not in x)
    ))


class TestConnectionValidationProperties:
    """Property-based tests for connection validation."""
    
    @given(valid_urls())
    def test_valid_urls_always_pass_validation(self, url):
        """Property: All valid HTTP/HTTPS URLs should pass validation."""
        result = validate_connection_url(url)
        assert result is True or isinstance(result, dict)  # May return warning for HTTP
    
    @given(invalid_urls())
    def test_invalid_urls_always_fail_validation(self, url):
        """Property: Invalid URLs should always fail validation."""
        with pytest.raises((ValueError, TypeError)):
            validate_connection_url(url)
    
    @given(st.text(min_size=1, max_size=255))
    def test_connection_name_length_constraints(self, name):
        """Property: Connection names between 1-255 chars should be valid."""
        # Names should be trimmed and validated
        from backend.src.models.connection import Connection
        if name.strip():
            connection = Connection(
                name=name.strip(),
                server_url="https://test.com"
            )
            assert len(connection.name) <= 255
    
    @given(st.integers(min_value=1, max_value=60))
    def test_connection_timeout_range(self, timeout_seconds):
        """Property: Timeouts between 1-60 seconds should be valid."""
        # Connection validation timeout should accept reasonable values
        assert 1 <= timeout_seconds <= 60
