from web.app import _is_plain_site_care_request, _plain_site_care_response


class DummyRequest:
    def __init__(self, host: str):
        self.headers = {"host": host}


def test_plain_site_care_host_matches_custom_domain():
    assert _is_plain_site_care_request(DummyRequest("plainsitecare.com"))
    assert _is_plain_site_care_request(DummyRequest("www.plainsitecare.com:443"))
    assert not _is_plain_site_care_request(DummyRequest("moreauarena.com"))


def test_plain_site_care_response_uses_static_site_files():
    response = _plain_site_care_response("/")
    assert response.status_code == 200
    assert str(response.path).endswith("web/static/plain-site-care/index.html")

    missing = _plain_site_care_response("/missing")
    assert missing.status_code == 404
    assert str(missing.path).endswith("web/static/plain-site-care/404.html")
