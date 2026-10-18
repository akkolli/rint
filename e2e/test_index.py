from .utils import TEST_URL, visible


class TestIndex:
    def test_rint_brand_and_visitor_navigation(self, selenium):
        selenium.get(TEST_URL)
        assert visible(selenium, '#nav a[aria-label="Rint home"]')
        assert "Rint" in selenium.title
        assert visible(selenium, '#nav a[href="/login"]').text == "Sign in"
        assert (
            visible(selenium, '#nav a[href="/register"]').text == "Join Rint"
        )
