from rain.ext.redis.base import BaseMix


class ScriptMix(BaseMix):
	async def eval(self, script, numberkeys, keys, args):
		assert len(keys) == numberkeys
		return await self._send(b'EVAL', script, numberkeys, *keys, *args)

	async def evalsha(self, sha, numberkeys, keys, args):
		assert len(keys) == numberkeys
		return await self._send(b'EVALSHA', sha, numberkeys, *keys, *args)

	async def script_exists(self, sha):
		return await self._send(b'SCRIPT EXISTS', sha)

	async def script_flush(self):
		return await self._send(b'SCRIPT FLUSH')

	async def script_kill(self):
		return await self._send(b'SCRIPT KILL')

	async def script_load(self, script):
		return await self._send(b'SCRIPT LOAD', script)
