from aiohttp import web
import aiohttp
class PastabinApp():
    def get_app(self):
        async def handler(request):
            result = ""
            for e in dir(request):
                result += e + ' : ' + str(getattr(request, e)) + '\n'

            return web.Response(text="This is the handler for " + result)

        pastabin = web.Application()
        pastabin.router.add_get('/res', handler, name='name')
        pastabin.router.add_get('/', lambda r: aiohttp.web.HTTPFound('index.html'))

        pastabin.router.add_static('/', 'pastabin/static')

        return pastabin