"""Exercise RedFox media-host checks without network access."""

import os
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import redfox_download as redfox


def dns_answers(*addresses):
    rows = [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (ip, 443))
            for ip in addresses]
    return patch.object(redfox.socket, "getaddrinfo", return_value=rows)


class MediaHostTests(unittest.TestCase):
    def test_different_media_hosts_with_synthetic_dns(self):
        for host, ip in (("media-one.example.com", "198.18.0.1"), ("cdn-two.example.org", "198.19.2.1")):
            with self.subTest(host=host), dns_answers(ip):
                redfox.require_public_https("https://" + host + "/asset")

    def test_other_cdn_with_public_dns(self):
        with dns_answers("1.1.1.1"):
            redfox.require_public_https("https://media-one.example.com/video")

    def test_private_answers_and_literal_synthetic_address_are_rejected(self):
        for host, addresses in (
            ("media-one.example.com", ("10.0.0.2",)),
            ("media-one.example.com", ("198.18.0.1", "10.0.0.2")),
            ("127.0.0.1", ("127.0.0.1",)),
            ("198.18.0.1", ("198.18.0.1",)),
        ):
            with self.subTest(host=host, addresses=addresses), dns_answers(*addresses):
                with self.assertRaises(redfox.DownloadError) as error:
                    redfox.require_public_https("https://" + host + "/asset")
                self.assertEqual(str(error.exception), "invalid_media_url")

    def test_local_hostname_is_rejected_even_with_synthetic_dns(self):
        with dns_answers("198.18.0.1"), self.assertRaises(redfox.DownloadError):
            redfox.require_public_https("https://localhost/video")

    def test_proxy_only_dns_respects_no_proxy(self):
        url = "https://media-one.example.com/video"
        with patch.dict(os.environ, {"https_proxy": "http://proxy.example.org:8080"}, clear=True):
            with patch.object(redfox.socket, "getaddrinfo", side_effect=socket.gaierror()):
                redfox.require_public_https(url)
                os.environ["no_proxy"] = "media-one.example.com"
                with self.assertRaises((redfox.DownloadError, socket.gaierror)):
                    redfox.require_public_https(url)

    def test_each_redirect_rechecks_its_destination(self):
        redirect = redfox.MediaRedirect()
        request = Request("https://media-one.example.com/video")
        target = "https://cdn-two.example.org/asset"
        with dns_answers("198.18.0.1"):
            request = redirect.redirect_request(request, None, 302, "", {}, target)
        self.assertEqual(request.full_url, target)
        with dns_answers("127.0.0.1"), self.assertRaises(redfox.DownloadError):
            redirect.redirect_request(request, None, 302, "", {}, "https://other.example.net/asset")


if __name__ == "__main__":
    unittest.main()
