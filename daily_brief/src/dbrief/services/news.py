from os import getenv
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from dbrief.constants import INTEREST_STORY_FETCH_LIMIT
from pydantic import BaseModel, model_validator

from loguru import logger
from curl_cffi.requests import Session

from dbrief.config import URLs
from dbrief.services.external_comms import get, create_session



class GNUser(BaseModel):
    id: int
    avatar: Optional[str]
    category: str
    email: Optional[str]
    extensionDate: Optional[str]
    fullname: str
    subscriptionStatus: str  
    localNews: Dict[str, Any]
    topFeedEdition: str
    leftColor: str
    rightColor: str
    subscribedUntil: Optional[str]
    registered: Optional[str]
    imageMode: Optional[str] 
    utmSource: Optional[str]
    utmMedium: Optional[str]
    utmCampaign: Optional[str]
    utmContent: Optional[str]
    utmTerm: Optional[str]
    subscriptionWillRenew: Optional[bool]
    subscriptionInfoText: Optional[str]
    trialStart: Optional[str]
    institutionalUser: Optional[bool]
    instVerifPending: Optional[bool]
    newlyRegistered: Optional[bool]
    stripeCustomerId: Optional[str]
    timeZoneId: Optional[str]


class GNLoginResponse(BaseModel):
    user: GNUser
    session: str


class GroundNewsCredentials(BaseModel):
    id_token: str
    refresh_token: str
    expires_in: int
    expires_at: str
    valid_since: Optional[str]
    last_login_at: Optional[str]
    last_refresh_at: Optional[str]
    registered: Optional[bool]
    login_token: Optional[str]

    @model_validator(mode="before")
    def set_expires_at(cls, values):
        if isinstance(values, dict):
            # calculate when the id token will expire if this is not already set
            expires_in = values.get("expires_in")
            if values["expires_at"] is None and expires_in is not None:
                expiry_td = timedelta(seconds=int(expires_in))
                values["expires_at"] = str((datetime.now() + expiry_td).timestamp())
        return values


class Interest(BaseModel):
    id: str
    type: str
    name: str
    icon: str
    slug: str
    pinned: bool
    youFollow: bool
    youSubToPns: bool

class GroundNewsService:
    _session: Optional[Session] = None


    def get_story(self, story_id: str) -> Dict[str, Any]:
        endpoint = URLs['GN'].endpoints.story
        url = self._build_url(endpoint, id=story_id)

        return self._fetch(url).get("event", {})

    
    def get_interest_feed_stories(self, interest_id: str) -> Dict[str, Any]:
        endpoint = URLs['GN'].endpoints.interest_feed
        url = self._build_url(
            endpoint,
            id=interest_id,
            limit=INTEREST_STORY_FETCH_LIMIT,
            offset=0
        )
        return self._fetch(url).get("eventIds", {})


    def get_interest_top_stories(self, interest_id: str) -> Dict[str, Any]:
        endpoint = URLs['GN'].endpoints.interest_top_stories
        url = self._build_url(
            endpoint, 
            id=interest_id,
            limit=INTEREST_STORY_FETCH_LIMIT,
            offset=0
        )
        return self._fetch(url).get("eventIds", {})

    
    def get_subscribed(self) -> list[Interest]:
        endpoint = URLs['GN'].endpoints.subscribed_topics
        url = self._build_url(endpoint)
        res: list[Dict[str, Any]] = self._fetch(url)
        logger.debug(f"Fetched subscribed topics: {res}")
        if res is None or len(res) == 0:
            logger.warning("No subscribed topics found.")
            return []
        return [Interest(**item) for item in res]


    def _fetch(self, url: str) -> Any:
        self.session.headers.update({
            "Authorization": getenv("GN_LOGIN_TOKEN")
        })
        data = get(url, session=self.session)
        if data is None:
            raise RuntimeError("Failed to retrieve data from Ground News API")
        return data


    def _build_url(self, endpoint: str, id: str = "", **kwargs) -> str:
        url = f"{URLs['GN'].base_url}{endpoint}"
        if id:
            url = url.replace(":id", id)
        # fill placeholders denoted by :<key>
        for key, value in kwargs.items():
            if "?" in url:
                url += f"&{key}={value}"
            else:
                url += f"?{key}={value}"    
        return url


    def build_gn_headers(self) -> Dict[str, str]:
        """Build headers for Ground News API requests."""
        headers = {}
        headers["Accept"] = "*/*"
        headers["Accept-Language"] = "en-US,en;q=0.9"
        headers["Accept-Encoding"] = "gzip, deflate, br, zstd"
        headers["Referer"] = "https://ground.news/"
        headers["Content-Type"] = "application/json"
        headers["X-GN-V"] = "web"
        headers["Origin"] = "https://ground.news"
        headers["Sec-GPC"] = "1"
        headers["Sec-Fetch-Dest"] = "empty"
        headers["Sec-Fetch-Mode"] = "cors"
        headers["Sec-Fetch-Site"] = "same-site"
        headers["Priority"] = "u=4"
        return headers


    @property
    def session(self) -> Session:
        """Create a session for making requests to Ground News API."""
        if self._session is None:
            self._session = create_session(headers=self.build_gn_headers())
        return self._session



NewsService = GroundNewsService()