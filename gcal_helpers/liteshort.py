from pyshorteners.base import BaseShortener
from pyshorteners.exceptions import ShorteningErrorException


class Shortener(BaseShortener):
    """
    Liteshort shortener implementation
    See https://git.ikl.sh/132ikl/liteshort

    Args:
        domain (str): the domain hosting the Liteshort instance

    Example:

        >>> import pyshorteners
        >>> s = pyshorteners.Shortener('domain=https://s.example.com')
        >>> s.liteshort.short('http://www.google.com')
        'http://s.example.com/TEST'

        There are other operations supported, but this 
        implementation ignores them. There is no expand 
        function -- Liteshort just does the redirect when 
        the shortlink is visited.
    """

    domain = ""

    def short(self, url):
        """Short implementation for Liteshort
        Args:
            url (str): the URL you want to shorten

        Returns:
            str: The shortened URL.

        Raises:
            ShorteningErrorException: If the API Returns an error as response
        """
        url = self.clean_url(url)
        response = self._post(
          self.domain,
          data={"long": url},
          headers={"Accept": "application/json"},
          )
        if not response.ok:
            raise ShorteningErrorException(response.content)
        else:
            data = response.json();
            
            if not data.get("success") or not data["success"]:
               
                raise ShorteningErrorException(response.content)

            elif not data.get("result"):
                raise ShorteningErrorException(response.content)

            else:
                return data["result"].strip()
            

