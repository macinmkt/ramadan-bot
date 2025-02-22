/app/bot.py:67: DeprecationWarning: There is no current event loop

  loop = asyncio.get_event_loop()

Traceback (most recent call last):

  File "/opt/venv/lib/python3.12/site-packages/telegram/_bot.py", line 547, in initialize

    await self.get_me()

  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_extbot.py", line 1677, in get_me

    return await super().get_me(

           ^^^^^^^^^^^^^^^^^^^^^

  File "/opt/venv/lib/python3.12/site-packages/telegram/_bot.py", line 334, in decorator

    result = await func(*args, **kwargs)  # skipcq: PYL-E1102

             ^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/opt/venv/lib/python3.12/site-packages/telegram/_bot.py", line 692, in get_me

    result = await self._post(

             ^^^^^^^^^^^^^^^^^

  File "/opt/venv/lib/python3.12/site-packages/telegram/_bot.py", line 422, in _post

    return await self._do_post(

           ^^^^^^^^^^^^^^^^^^^^

    return self.__run(

           ^^^^^^^^^^^

  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_extbot.py", line 306, in _do_post

  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_application.py", line 881, in __run

    return await super()._do_post(

    raise exc

           ^^^^^^^^^^^^^^^^^^^^^^^

  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_application.py", line 870, in __run

    loop.run_until_complete(self.initialize())

  File "/root/.nix-profile/lib/python3.12/asyncio/base_events.py", line 687, in run_until_complete

  File "/opt/venv/lib/python3.12/site-packages/telegram/_bot.py", line 453, in _do_post

    return future.result()

    return await request.post(

           ^^^^^^^^^^^^^^^

           ^^^^^^^^^^^^^^^^^^^

  File "/opt/venv/lib/python3.12/site-packages/telegram/request/_baserequest.py", line 165, in post

  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_application.py", line 376, in initialize

    result = await self._request_wrapper(

    await self.bot.initialize()

             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_extbot.py", line 252, in initialize

  File "/opt/venv/lib/python3.12/site-packages/telegram/request/_baserequest.py", line 326, in _request_wrapper

    await super().initialize()

  File "/opt/venv/lib/python3.12/site-packages/telegram/_bot.py", line 549, in initialize

    raise InvalidToken(f"The token `{self._token}` was rejected by the server.") from exc

    raise InvalidToken(message)

telegram.error.InvalidToken: The token `YOUR_BOT_TOKEN` was rejected by the server.

Task was destroyed but it is pending!

telegram.error.InvalidToken: Not Found
