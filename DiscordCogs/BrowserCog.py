from html.parser import HTMLParser
from typing import Optional

from aiohttp import ClientError, ClientSession, ClientTimeout
from discord.ext.commands import Cog, Context, command

from Config.Embeds import VEmbeds
from Config.Helper import Helper
from Music.VulkanBot import VulkanBot


class _SimplePageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.__in_title = False
        self.__title_parts: list[str] = []
        self.description: Optional[str] = None

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag == 'title':
            self.__in_title = True

        if tag == 'meta' and self.description is None:
            attributes = {name.lower(): value for name, value in attrs}
            if attributes.get('name') == 'description':
                self.description = attributes.get('content')

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == 'title':
            self.__in_title = False

    def handle_data(self, data: str) -> None:
        if self.__in_title:
            cleaned = data.strip()
            if cleaned:
                self.__title_parts.append(cleaned)

    @property
    def title(self) -> str:
        title = ' '.join(self.__title_parts).strip()
        return title if title else 'Untitled page'


class BrowserCog(Cog):
    """Cog to preview webpages inside Discord."""

    def __init__(self, bot: VulkanBot):
        self.__bot = bot
        self.__embeds = VEmbeds()

    @command(name='browse', help=Helper().HELP_BROWSE, description=Helper().HELP_BROWSE_LONG, aliases=['web', 'website'])
    async def browse(self, ctx: Context, *, url: str) -> None:
        normalized_url = self.__normalize_url(url)

        try:
            html = await self.__fetch_html(normalized_url)
        except Exception:
            embed = self.__embeds.WEB_PREVIEW_ERROR()
            await ctx.send(embed=embed)
            return

        page_parser = self.__parse_html(html)
        embed = self.__embeds.WEB_PREVIEW(normalized_url, page_parser.title, page_parser.description)
        await ctx.send(embed=embed)

    async def __fetch_html(self, url: str) -> str:
        timeout = ClientTimeout(total=10)
        async with ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status >= 400:
                    raise ClientError(f'Response status {response.status}')
                text = await response.text(errors='ignore')
        return text[:100000]

    def __parse_html(self, html: str) -> _SimplePageParser:
        parser = _SimplePageParser()
        parser.feed(html)
        parser.close()
        return parser

    def __normalize_url(self, url: str) -> str:
        cleaned = url.strip()
        if not cleaned.lower().startswith(('http://', 'https://')):
            cleaned = f'https://{cleaned}'
        return cleaned


def setup(bot):
    bot.add_cog(BrowserCog(bot))
