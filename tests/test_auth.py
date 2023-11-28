from urllib.parse import urlparse



def test_login_redirect(auth):
    response = auth.login()
    assert response.status_code == 200
    assert b'Logged in successfully.' in response.data


def test_login_valid_credentials(auth):
    response = auth.login(password='incorrect_password')
    assert response.status_code == 200
    assert b'Invalid email or password.' in response.data


def test_login_redirect_next_page(auth):
    next_page = 'https://127.0.0.1:5000/home'
    response = auth.login(next=next_page)
    
    # Check that the response indicates a redirection
    assert response.status_code == 302

    # Extract the path from the Location header
    location_path = response.headers['Location']
    parsed_url = urlparse(location_path)
    location_path = parsed_url.path

    # Extract the path from the next_page URL
    parsed_next_url = urlparse(next_page)
    expected_path = parsed_next_url.path

    # Check that the extracted paths match
    assert location_path == expected_path