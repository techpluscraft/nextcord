"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations
from typing import Dict, List, Optional, TYPE_CHECKING, Any, Tuple, Union, Callable

if TYPE_CHECKING:
    from aiohttp import ClientResponse, ClientWebSocketResponse

    try:
        from requests import Response

        _ResponseType = Union[ClientResponse, Response]
    except ModuleNotFoundError:
        _ResponseType = ClientResponse

    from .interactions import Interaction
    from .types.snowflake import Snowflake, SnowflakeList
    from .abc import GuildChannel
    from .threads import Thread

__all__ = (
    'DiscordException',
    'InvalidCommandType',
    'ClientException',
    'NoMoreItems',
    'GatewayNotFound',
    'HTTPException',
    'Forbidden',
    'NotFound',
    'DiscordServerError',
    'InvalidData',
    'InvalidArgument',
    'LoginFailure',
    'ConnectionClosed',
    'PrivilegedIntentsRequired',
    'InteractionResponded',
    'ApplicationError',
    'ApplicationCheckFailure',
    'ApplicationCheckAnyFailure',
    'ApplicationNoPrivateMessage',
    'ApplicationMissingRole',
    'ApplicationMissingAnyRole',
    'ApplicationBotMissingRole',
    'ApplicationBotMissingAnyRole',
    'ApplicationMissingPermissions',
    'ApplicationBotMissingPermissions',
    'ApplicationPrivateMessageOnly',
    'ApplicationNotOwner',
    'ApplicationNSFWChannelRequired'
)


class DiscordException(Exception):
    """Base exception class for nextcord

    Ideally speaking, this could be caught to handle any exceptions raised from this library.
    """

    pass


class ClientException(DiscordException):
    """Exception that's raised when an operation in the :class:`Client` fails.

    These are usually for exceptions that happened due to user input.
    """

    pass


class InvalidCommandType(ClientException):
    """Raised when an unhandled Application Command type is encountered."""
    pass


class NoMoreItems(DiscordException):
    """Exception that is raised when an async iteration operation has no more items."""

    pass


class GatewayNotFound(DiscordException):
    """An exception that is raised when the gateway for Discord could not be found"""

    def __init__(self):
        message = 'The gateway to connect to discord was not found.'
        super().__init__(message)


def _flatten_error_dict(d: Dict[str, Any], key: str = '') -> Dict[str, str]:
    items: List[Tuple[str, str]] = []
    for k, v in d.items():
        new_key = key + '.' + k if key else k

        if isinstance(v, dict):
            try:
                _errors: List[Dict[str, Any]] = v['_errors']
            except KeyError:
                items.extend(_flatten_error_dict(v, new_key).items())
            else:
                items.append((new_key, ' '.join(x.get('message', '') for x in _errors)))
        else:
            items.append((new_key, v))

    return dict(items)


class HTTPException(DiscordException):
    """Exception that's raised when an HTTP request operation fails.

    Attributes
    ------------
    response: :class:`aiohttp.ClientResponse`
        The response of the failed HTTP request. This is an
        instance of :class:`aiohttp.ClientResponse`. In some cases
        this could also be a :class:`requests.Response`.

    text: :class:`str`
        The text of the error. Could be an empty string.
    status: :class:`int`
        The status code of the HTTP request.
    code: :class:`int`
        The Discord specific error code for the failure.
    """

    def __init__(self, response: _ResponseType, message: Optional[Union[str, Dict[str, Any]]]):
        self.response: _ResponseType = response
        self.status: int = response.status  # type: ignore
        self.code: int
        self.text: str
        if isinstance(message, dict):
            self.code = message.get('code', 0)
            base = message.get('message', '')
            errors = message.get('errors')
            if errors:
                errors = _flatten_error_dict(errors)
                helpful = '\n'.join('In %s: %s' % t for t in errors.items())
                self.text = base + '\n' + helpful
            else:
                self.text = base
        else:
            self.text = message or ''
            self.code = 0

        fmt = '{0.status} {0.reason} (error code: {1})'
        if len(self.text):
            fmt += ': {2}'

        super().__init__(fmt.format(self.response, self.code, self.text))


class Forbidden(HTTPException):
    """Exception that's raised for when status code 403 occurs.

    Subclass of :exc:`HTTPException`
    """

    pass


class NotFound(HTTPException):
    """Exception that's raised for when status code 404 occurs.

    Subclass of :exc:`HTTPException`
    """

    pass


class DiscordServerError(HTTPException):
    """Exception that's raised for when a 500 range status code occurs.

    Subclass of :exc:`HTTPException`.

    .. versionadded:: 1.5
    """

    pass


class InvalidData(ClientException):
    """Exception that's raised when the library encounters unknown
    or invalid data from Discord.
    """

    pass


class InvalidArgument(ClientException):
    """Exception that's raised when an argument to a function
    is invalid some way (e.g. wrong value or wrong type).

    This could be considered the analogous of ``ValueError`` and
    ``TypeError`` except inherited from :exc:`ClientException` and thus
    :exc:`DiscordException`.
    """

    pass


class LoginFailure(ClientException):
    """Exception that's raised when the :meth:`Client.login` function
    fails to log you in from improper credentials or some other misc.
    failure.
    """

    pass


class ConnectionClosed(ClientException):
    """Exception that's raised when the gateway connection is
    closed for reasons that could not be handled internally.

    Attributes
    -----------
    code: :class:`int`
        The close code of the websocket.
    reason: :class:`str`
        The reason provided for the closure.
    shard_id: Optional[:class:`int`]
        The shard ID that got closed if applicable.
    """

    def __init__(self, socket: ClientWebSocketResponse, *, shard_id: Optional[int], code: Optional[int] = None):
        # This exception is just the same exception except
        # reconfigured to subclass ClientException for users
        self.code: int = code or socket.close_code or -1
        # aiohttp doesn't seem to consistently provide close reason
        self.reason: str = ''
        self.shard_id: Optional[int] = shard_id
        super().__init__(f'Shard ID {self.shard_id} WebSocket closed with {self.code}')


class PrivilegedIntentsRequired(ClientException):
    """Exception that's raised when the gateway is requesting privileged intents
    but they're not ticked in the developer page yet.

    Go to https://discord.com/developers/applications/ and enable the intents
    that are required. Currently these are as follows:

    - :attr:`Intents.members`
    - :attr:`Intents.presences`

    Attributes
    -----------
    shard_id: Optional[:class:`int`]
        The shard ID that got closed if applicable.
    """

    def __init__(self, shard_id: Optional[int]):
        self.shard_id: Optional[int] = shard_id
        msg = (
            'Shard ID %s is requesting privileged intents that have not been explicitly enabled in the '
            'developer portal. It is recommended to go to https://discord.com/developers/applications/ '
            'and explicitly enable the privileged intents within your application\'s page. If this is not '
            'possible, then consider disabling the privileged intents instead.'
        )
        super().__init__(msg % shard_id)


class InteractionResponded(ClientException):
    """Exception that's raised when sending another interaction response using
    :class:`InteractionResponse` when one has already been done before.

    An interaction can only respond once.

    .. versionadded:: 2.0

    Attributes
    -----------
    interaction: :class:`Interaction`
        The interaction that's already been responded to.
    """

    def __init__(self, interaction: Interaction):
        self.interaction: Interaction = interaction
        super().__init__('This interaction has already been responded to before')

class ApplicationError(DiscordException):
    r"""The base exception type for all command related errors.

    This inherits from :exc:`nextcord.DiscordException`.

    This exception and exceptions inherited from it are handled
    in a special way as they are caught and passed into a special event
    from :class:`.Bot`\, :func:`.on_command_error`.
    """
    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        if message is not None:
            # clean-up @everyone and @here mentions
            m = message.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
            super().__init__(m, *args)
        else:
            super().__init__(*args)

class ApplicationError(DiscordException):
    r"""The base exception type for all application command related errors.

    This inherits from :exc:`nextcord.DiscordException`.

    This exception and exceptions inherited from it are handled
    in a special way as they are caught and passed into a special event
    from :class:`.Bot`\, :func:`.on_application_command_error`.
    """
    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        if message is not None:
            # clean-up @everyone and @here mentions
            m = message.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
            super().__init__(m, *args)
        else:
            super().__init__(*args)

class ApplicationCheckFailure(ApplicationError):
    """Exception raised when the predicates in :attr:`.ApplicationCommand.checks` have failed.

    This inherits from :exc:`ApplicationError`
    """
    pass

class ApplicationCheckAnyFailure(ApplicationCheckFailure):
    """Exception raised when all predicates in :func:`check_any` fail.

    This inherits from :exc:`ApplicationCheckFailure`.

    Attributes
    ------------
    errors: List[:class:`ApplicationCheckFailure`]
        A list of errors that were caught during execution.
    checks: List[Callable[[:class:`Interaction`], :class:`bool`]]
        A list of check predicates that failed.
    """

    def __init__(self, checks: List[ApplicationCheckFailure], errors: List[Callable[[Interaction], bool]]) -> None:
        self.checks: List[ApplicationCheckFailure] = checks
        self.errors: List[Callable[[Interaction], bool]] = errors
        super().__init__('You do not have permission to run this command.')

class ApplicationNoPrivateMessage(ApplicationCheckFailure):
    """Exception raised when an operation does not work in private message
    contexts.

    This inherits from :exc:`ApplicationCheckFailure`
    """

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or 'This command cannot be used in private messages.')

class ApplicationMissingRole(ApplicationCheckFailure):
    """Exception raised when the command invoker lacks a role to run a command.

    This inherits from :exc:`ApplicationCheckFailure`

    .. versionadded:: 1.1

    Attributes
    -----------
    missing_role: Union[:class:`str`, :class:`int`]
        The required role that is missing.
        This is the parameter passed to :func:`~.checks.has_role`.
    """
    def __init__(self, missing_role: Snowflake) -> None:
        self.missing_role: Snowflake = missing_role
        message = f'Role {missing_role!r} is required to run this command.'
        super().__init__(message)

class ApplicationMissingAnyRole(ApplicationCheckFailure):
    """Exception raised when the command invoker lacks any of
    the roles specified to run a command.

    This inherits from :exc:`ApplicationCheckFailure`

    Attributes
    -----------
    missing_roles: List[Union[:class:`str`, :class:`int`]]
        The roles that the invoker is missing.
        These are the parameters passed to :func:`~.commands.has_any_role`.
    """
    def __init__(self, missing_roles: SnowflakeList) -> None:
        self.missing_roles: SnowflakeList = missing_roles

        missing = [f"'{role}'" for role in missing_roles]

        if len(missing) > 2:
            fmt = '{}, or {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' or '.join(missing)

        message = f"You are missing at least one of the required roles: {fmt}"
        super().__init__(message)

class ApplicationBotMissingRole(ApplicationCheckFailure):
    """Exception raised when the bot's member lacks a role to run a command.

    This inherits from :exc:`ApplicationCheckFailure`

    .. versionadded:: 1.1

    Attributes
    -----------
    missing_role: Union[:class:`str`, :class:`int`]
        The required role that is missing.
        This is the parameter passed to :func:`~.commands.has_role`.
    """
    def __init__(self, missing_role: Snowflake) -> None:
        self.missing_role: Snowflake = missing_role
        message = f'Bot requires the role {missing_role!r} to run this command'
        super().__init__(message)

class ApplicationBotMissingAnyRole(ApplicationCheckFailure):
    """Exception raised when the bot's member lacks any of
    the roles specified to run a command.

    This inherits from :exc:`ApplicationCheckFailure`

    .. versionadded:: 1.1

    Attributes
    -----------
    missing_roles: List[Union[:class:`str`, :class:`int`]]
        The roles that the bot's member is missing.
        These are the parameters passed to :func:`~.commands.has_any_role`.

    """
    def __init__(self, missing_roles: SnowflakeList) -> None:
        self.missing_roles: SnowflakeList = missing_roles

        missing = [f"'{role}'" for role in missing_roles]

        if len(missing) > 2:
            fmt = '{}, or {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' or '.join(missing)

        message = f"Bot is missing at least one of the required roles: {fmt}"
        super().__init__(message)

class ApplicationMissingPermissions(ApplicationCheckFailure):
    """Exception raised when the command invoker lacks permissions to run a
    command.

    This inherits from :exc:`ApplicationCheckFailure`

    Attributes
    -----------
    missing_permissions: List[:class:`str`]
        The required permissions that are missing.
    """
    def __init__(self, missing_permissions: List[str], *args: Any) -> None:
        self.missing_permissions: List[str] = missing_permissions

        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_permissions]

        if len(missing) > 2:
            fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = f'You are missing {fmt} permission(s) to run this command.'
        super().__init__(message, *args)

class ApplicationBotMissingPermissions(ApplicationCheckFailure):
    """Exception raised when the bot's member lacks permissions to run a
    command.

    This inherits from :exc:`ApplicationCheckFailure`

    Attributes
    -----------
    missing_permissions: List[:class:`str`]
        The required permissions that are missing.
    """
    def __init__(self, missing_permissions: List[str], *args: Any) -> None:
        self.missing_permissions: List[str] = missing_permissions

        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_permissions]

        if len(missing) > 2:
            fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = f'Bot requires {fmt} permission(s) to run this command.'
        super().__init__(message, *args)

class ApplicationPrivateMessageOnly(ApplicationCheckFailure):
    """Exception raised when an operation does not work outside of private
    message contexts.

    This inherits from :exc:`ApplicationCheckFailure`
    """
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or 'This command can only be used in private messages.')


class ApplicationNotOwner(ApplicationCheckFailure):
    """Exception raised when the message author is not the owner of the bot.

    This inherits from :exc:`ApplicationCheckFailure`
    """
    pass

class ApplicationNSFWChannelRequired(ApplicationCheckFailure):
    """Exception raised when a channel does not have the required NSFW setting.

    This inherits from :exc:`ApplicationCheckFailure`.

    .. versionadded:: 1.1

    Parameters
    -----------
    channel: Union[:class:`.abc.GuildChannel`, :class:`.Thread`]
        The channel that does not have NSFW enabled.
    """
    def __init__(self, channel: Union[GuildChannel, Thread]) -> None:
        self.channel: Union[GuildChannel, Thread] = channel
        super().__init__(f"Channel '{channel}' needs to be NSFW for this command to work.")
