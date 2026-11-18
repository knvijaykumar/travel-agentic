import io
import json
import urllib.error
from unittest.mock import MagicMock, patch
import pytest

from backend.app.services.wikimedia_service import WikimediaService


def create_mock_urlopen_response(data: dict):
    """Helper to mock urllib.request.urlopen response."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    return mock_resp


def test_get_image_success_with_artist_and_license():
    """Verify image URL and cleaned attribution are returned when both artist and license exist."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "101": {
                    "index": 1,
                    "title": "File:Aguada Fort.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/a/b/Aguada_Fort.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {
                                "Artist": {"value": '<a href="http://example.com">John Doe</a>'},
                                "LicenseShortName": {"value": "CC BY-SA 4.0"},
                            },
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Aguada Fort")
        assert result is not None
        assert result["image_url"] == "https://upload.wikimedia.org/wikipedia/commons/a/b/Aguada_Fort.jpg"
        assert result["attribution"] == "John Doe (CC BY-SA 4.0)"


def test_get_image_artist_only():
    """Verify attribution formatting when only artist is present."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "102": {
                    "index": 1,
                    "title": "File:Fort.png",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/f/Fort.png",
                            "mime": "image/png",
                            "extmetadata": {
                                "Artist": {"value": "Jane Smith"},
                            },
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Fort")
        assert result is not None
        assert result["attribution"] == "Jane Smith"


def test_get_image_license_only():
    """Verify attribution formatting when only license is present."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "103": {
                    "index": 1,
                    "title": "File:Museum.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/m/Museum.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {
                                "LicenseShortName": {"value": "CC0"},
                            },
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Museum")
        assert result is not None
        assert result["attribution"] == "Licensed under CC0"


def test_get_image_no_attribution_does_not_invent():
    """Verify attribution is None when metadata has neither artist nor license."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "104": {
                    "index": 1,
                    "title": "File:Plain.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/p/Plain.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {},
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Plain Place")
        assert result is not None
        assert result["image_url"] == "https://upload.wikimedia.org/wikipedia/commons/p/Plain.jpg"
        assert result["attribution"] is None


def test_get_image_skips_non_image_files():
    """Verify non-image files (e.g., PDF) are skipped in favor of valid images."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "201": {
                    "index": 1,
                    "title": "File:Document.pdf",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/file.pdf",
                            "mime": "application/pdf",
                        }
                    ],
                },
                "202": {
                    "index": 2,
                    "title": "File:Photo.webp",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/photo.webp",
                            "mime": "image/webp",
                            "extmetadata": {
                                "LicenseShortName": {"value": "CC-BY 2.0"},
                            },
                        }
                    ],
                },
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Document and Photo")
        assert result is not None
        assert result["image_url"] == "https://upload.wikimedia.org/photo.webp"


def test_get_image_empty_results_returns_none():
    """Verify None is returned when query returns no pages."""
    service = WikimediaService()
    mock_data = {"query": {"pages": {}}}

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        assert service.get_image("Nonexistent Place 12345xyz") is None


def test_get_image_empty_or_whitespace_name():
    """Verify empty or whitespace-only place name returns None immediately."""
    service = WikimediaService()
    with patch("urllib.request.urlopen") as mock_urlopen:
        assert service.get_image("") is None
        assert service.get_image("   ") is None
        assert not mock_urlopen.called


def test_get_image_http_error_handled_safely():
    """Verify HTTP errors (e.g., 500, 404) return None safely."""
    service = WikimediaService()
    http_err = urllib.error.HTTPError(
        url="https://commons.wikimedia.org",
        code=500,
        msg="Internal Server Error",
        hdrs={},
        fp=io.BytesIO(b"server error"),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        assert service.get_image("Error Place") is None


def test_get_image_timeout_handled_safely():
    """Verify timeout errors return None safely without raising exceptions."""
    service = WikimediaService()
    with patch("urllib.request.urlopen", side_effect=TimeoutError("Request timed out")):
        assert service.get_image("Timeout Place") is None


def test_get_image_sends_descriptive_user_agent_header():
    """Verify that every request to Wikimedia Commons includes a descriptive User-Agent header."""
    service = WikimediaService()
    mock_data = {"query": {"pages": {}}}

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)) as mock_urlopen:
        service.get_image("Goa Chitra Museum")
        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert isinstance(req, urllib.request.Request)
        user_agent = req.get_header("User-agent")
        assert user_agent is not None
        assert "VirtualTravelAgent" in user_agent
        assert "contact:" in user_agent


def test_get_image_custom_user_agent():
    """Verify that a custom User-Agent can be configured."""
    custom_ua = "CustomTravelBot/2.0 (bot@custom.test)"
    service = WikimediaService(user_agent=custom_ua)
    mock_data = {"query": {"pages": {}}}

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)) as mock_urlopen:
        service.get_image("Museum")
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("User-agent") == custom_ua




def test_get_image_rejects_unrelated_andromeda_galaxy_for_techspots():
    """Verify that an unrelated result (e.g. Andromeda Galaxy for Techspots) is rejected."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "301": {
                    "index": 1,
                    "title": "File:Andromeda Galaxy with h-alpha.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/andromeda.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "Astrophotographer"}},
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Techspots")
        assert result is None


def test_get_image_skips_unrelated_first_result_and_selects_relevant_second():
    """Verify that the service skips an unrelated top match and picks a relevant second match."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "302": {
                    "index": 1,
                    "title": "File:Random Sunset Beach.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/sunset.jpg",
                            "mime": "image/jpeg",
                        }
                    ],
                },
                "303": {
                    "index": 2,
                    "title": "File:Techspots Electronic Centre.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/techspots.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "Local Guide"}},
                        }
                    ],
                },
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Techspots")
        assert result is not None
        assert result["image_url"] == "https://upload.wikimedia.org/techspots.jpg"
        assert result["attribution"] == "Local Guide"


def test_get_image_returns_none_when_every_candidate_is_irrelevant():
    """Verify None is returned when all candidates in search results lack term relevance."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "401": {
                    "index": 1,
                    "title": "File:Milky Way from Atacama.jpg",
                    "imageinfo": [{"url": "https://upload.wikimedia.org/milkyway.jpg", "mime": "image/jpeg"}],
                },
                "402": {
                    "index": 2,
                    "title": "File:NGC 1300 Spiral Galaxy.png",
                    "imageinfo": [{"url": "https://upload.wikimedia.org/ngc.png", "mime": "image/png"}],
                },
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        assert service.get_image("Techspots") is None


def test_get_image_handles_hyphens_and_special_characters():
    """Verify normalization handles hyphens, underscores, and ampersands in place and file titles."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "501": {
                    "index": 1,
                    "title": "File:Ashvek_Vintage-World_Nuvem_Goa.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/ashvek.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "Car Enthusiast"}},
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Ashvek Vintage world - Car Museum")
        assert result is not None
        assert result["image_url"] == "https://upload.wikimedia.org/ashvek.jpg"


def test_get_image_rejects_candidate_matching_only_generic_location_words():
    """Verify that a candidate matching only a location word (e.g. Goa) without distinctive tokens is rejected."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "601": {
                    "index": 1,
                    "title": "File:Calangute Beach North Goa.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/calangute.jpg",
                            "mime": "image/jpeg",
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        # "Techspots Goa" has distinctive token "techspots" and location token "goa".
        # Calangute beach title only matches "goa" (location), so it must be rejected!
        result = service.get_image("Techspots Goa")
        assert result is None


def test_get_image_decodes_html_entities_in_attribution():
    """Verify that HTML entities (e.g., &amp;, &#40;, &copy;) are cleanly decoded in attribution."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "701": {
                    "index": 1,
                    "title": "File:Aguada Fort View.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/aguada_view.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {
                                "Artist": {"value": "<p>&copy; John &amp; Jane Doe &#40;Photographers&#41;</p>"},
                                "LicenseShortName": {"value": "CC BY&#45;SA 4.0"},
                            },
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Aguada Fort")
        assert result is not None
        assert result["attribution"] == "© John & Jane Doe (Photographers) (CC BY-SA 4.0)"


def test_get_image_wax_world_museum_goa_rejects_mysore():
    """Verify that 'Melody World Wax Museum - Mysore' is rejected for 'Wax World Museum, Goa'."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "801": {
                    "index": 1,
                    "title": "File:Melody World Wax Museum - Mysore.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/mysore_wax.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "Mysore Photographer"}},
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Wax World Museum", city="Goa")
        assert result is None


def test_get_image_wax_world_museum_goa_accepts_old_goa():
    """Verify that 'Wax World Museum Old Goa' is accepted for 'Wax World Museum, Goa'."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "802": {
                    "index": 1,
                    "title": "File:Wax World Museum Old Goa.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/goa_wax.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {
                                "Artist": {"value": "Goa Guide"},
                                "LicenseShortName": {"value": "CC-BY 3.0"},
                            },
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Wax World Museum", city="Goa")
        assert result is not None
        assert result["image_url"] == "https://upload.wikimedia.org/goa_wax.jpg"
        assert result["attribution"] == "Goa Guide (CC-BY 3.0)"


def test_get_image_distinctive_name_without_city_accepted():
    """Verify distinctive place names like 'Aguada Fort' are accepted even without city in filename."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "803": {
                    "index": 1,
                    "title": "File:Aguada Fort.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/aguada_alone.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "Traveler"}},
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Aguada Fort", city="Goa")
        assert result is not None
        assert result["image_url"] == "https://upload.wikimedia.org/aguada_alone.jpg"


def test_get_image_distinctive_name_with_conflicting_location_rejected():
    """Verify distinctive place name is rejected if candidate explicitly specifies a conflicting location."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "804": {
                    "index": 1,
                    "title": "File:Aguada Fort - Lisbon.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/aguada_lisbon.jpg",
                            "mime": "image/jpeg",
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Aguada Fort", city="Goa")
        assert result is None


def test_get_image_tiered_search_order():
    """Verify tiered search: location-aware query is executed first, fallback query second."""
    service = WikimediaService()
    empty_resp = create_mock_urlopen_response({"query": {"pages": {}}})
    success_resp = create_mock_urlopen_response({
        "query": {
            "pages": {
                "805": {
                    "index": 1,
                    "title": "File:Wax World Museum Old Goa.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/wax_fallback.jpg",
                            "mime": "image/jpeg",
                        }
                    ],
                }
            }
        }
    })

    with patch("urllib.request.urlopen", side_effect=[empty_resp, success_resp]) as mock_urlopen:
        result = service.get_image("Wax World Museum", city="Goa")
        assert result is not None
        assert result["image_url"] == "https://upload.wikimedia.org/wax_fallback.jpg"
        assert mock_urlopen.call_count == 2
        # Check first query was location-aware ("Wax World Museum Goa")
        first_call_req = mock_urlopen.call_args_list[0][0][0]
        assert "Wax+World+Museum+Goa" in first_call_req.full_url
        # Check second query was fallback ("Wax World Museum")
        second_call_req = mock_urlopen.call_args_list[1][0][0]
        assert "Wax+World+Museum" in second_call_req.full_url


def test_get_image_parenthesized_location_conflict_rejected():
    """Verify that a candidate with conflicting location in parentheses is rejected."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "806": {
                    "index": 1,
                    "title": "File:Wax Museum (Mysore).jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/mysore_paren.jpg",
                            "mime": "image/jpeg",
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Wax World Museum", region="Goa")
        assert result is None


def test_get_image_preposition_location_conflict_rejected():
    """Verify that a candidate with conflicting location after preposition is rejected."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "807": {
                    "index": 1,
                    "title": "File:Wax Museum in Mysore.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/mysore_prep.jpg",
                            "mime": "image/jpeg",
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Wax World Museum", city="Panaji", region="Goa")
        assert result is None


def test_get_image_distinctive_place_with_photo_term_accepted():
    """Verify architectural/view descriptors after dash are not mistaken for location conflicts."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "808": {
                    "index": 1,
                    "title": "File:Aguada Fort - View from Lighthouse.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/aguada_lighthouse.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "Fort Fan"}},
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Aguada Fort", city="Goa")
        assert result is not None
        assert result["image_url"] == "https://upload.wikimedia.org/aguada_lighthouse.jpg"


def test_get_image_archiepiscopal_palace_goa_rejects_trujillo():
    """Verify 'Archiepiscopal Palace of Trujillo' is rejected for 'Archiepiscopal Palace, Goa'."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "901": {
                    "index": 1,
                    "title": "File:Archiepiscopal Palace of Trujillo.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/trujillo.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "Bernard Gagnon"}},
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Archiepiscopal Palace", city="Panaji", region="Goa")
        assert result is None


def test_get_image_police_shahid_smarak_jaipur_rejects_ahmedabad():
    """Verify 'Shahid Smarak Mahagujarat movement' is rejected for 'Police Shahid Smarak, Jaipur'."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "902": {
                    "index": 1,
                    "title": "File:Shahid Smarak Mahagujarat movement.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/ahmedabad_smarak.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "Snehrashmi"}},
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Police Shahid Smarak", city="Jaipur", region="Rajasthan")
        assert result is None


def test_get_image_gateway_of_india_with_photo_view_accepted():
    """Verify Gateway of India with complex photo caption containing 'view of ...' is accepted."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "903": {
                    "index": 1,
                    "title": "File:Panoramic view of Taj Palace Hotel and Taj Tower with the iconic Gateway of India in the background.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/gateway_mumbai.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "iMahesh"}},
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Gateway of India", city="Mumbai", region="Maharashtra")
        assert result is not None
        assert result["image_url"] == "https://upload.wikimedia.org/gateway_mumbai.jpg"


def test_get_image_mysuru_rail_museum_accepted():
    """Verify Mysuru Rail Museum with legitimate city match is accepted."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "904": {
                    "index": 1,
                    "title": "File:Mysuru Rail Museum - Rail Bus - 2.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/mysuru_rail.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "Ingo Mehling"}},
                        }
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        result = service.get_image("Mysuru Rail Museum", city="Mysuru", region="Karnataka")
        assert result is not None
        assert result["image_url"] == "https://upload.wikimedia.org/mysuru_rail.jpg"


def test_get_candidates_returns_multiple_valid_images_up_to_limit():
    """Verify get_candidates returns multiple sorted candidates up to limit."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "101": {
                    "index": 2,
                    "title": "File:Aguada Fort Bastion.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/aguada_2.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "Alice"}, "LicenseShortName": {"value": "CC-BY 4.0"}},
                        }
                    ],
                },
                "102": {
                    "index": 1,
                    "title": "File:Aguada Fort Main.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/aguada_1.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "Bob"}, "LicenseShortName": {"value": "CC0"}},
                        }
                    ],
                },
                "103": {
                    "index": 3,
                    "title": "File:Aguada Fort Lighthouse.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/aguada_3.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "Charlie"}},
                        }
                    ],
                },
                "104": {
                    "index": 4,
                    "title": "File:Aguada Fort Sunset.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/aguada_4.jpg",
                            "mime": "image/jpeg",
                            "extmetadata": {"Artist": {"value": "David"}},
                        }
                    ],
                },
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        candidates = service.get_candidates("Aguada Fort", city="Candolim", region="Goa", limit=2)
        assert len(candidates) == 2
        # Index 1 should come before index 2
        assert candidates[0]["image_url"] == "https://upload.wikimedia.org/aguada_1.jpg"
        assert candidates[0]["attribution"] == "Bob (CC0)"
        assert candidates[1]["image_url"] == "https://upload.wikimedia.org/aguada_2.jpg"
        assert candidates[1]["attribution"] == "Alice (CC-BY 4.0)"


def test_get_candidates_filters_conflicting_location():
    """Verify get_candidates filters out images explicitly tagged with a different city."""
    service = WikimediaService()
    mock_data = {
        "query": {
            "pages": {
                "201": {
                    "index": 1,
                    "title": "File:Melody World Wax Museum Mysore.jpg",
                    "imageinfo": [
                        {"url": "https://upload.wikimedia.org/wax_mysore.jpg", "mime": "image/jpeg"}
                    ],
                },
                "202": {
                    "index": 2,
                    "title": "File:Wax World Museum Goa Old Goa.jpg",
                    "imageinfo": [
                        {"url": "https://upload.wikimedia.org/wax_goa.jpg", "mime": "image/jpeg"}
                    ],
                },
            }
        }
    }

    with patch("urllib.request.urlopen", return_value=create_mock_urlopen_response(mock_data)):
        candidates = service.get_candidates("Wax World Museum", city="Panaji", region="Goa", limit=3)
        assert len(candidates) == 1
        assert candidates[0]["image_url"] == "https://upload.wikimedia.org/wax_goa.jpg"


def test_get_candidates_empty_input():
    """Verify get_candidates handles empty, whitespace, or non-positive limit inputs gracefully."""
    service = WikimediaService()
    assert service.get_candidates("") == []
    assert service.get_candidates("   ") == []
    assert service.get_candidates("Fort", limit=0) == []
    assert service.get_candidates("Fort", limit=-1) == []

