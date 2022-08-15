import json
import websockets


class EventHandlerError(Exception):

    def __init__(self, message: str = "There is no handler for this event") -> None:
        self.message = message
        super().__init__(self.message)


class WebSocket:

    def __init__(self, host, port) -> None:
        self.host: str = host
        self.port: int = port
        self.events = dict()
        self.event_data = None
        self.response = None

    def add_event(self, func) -> None:
        self.events.update({func.__name__: func})

    async def serve(self) -> websockets.WebSocketServer:
        await websockets.serve(self.processor, self.host, self.port, ping_interval=None)

    async def processor(self, websocket) -> None:
        async for message in websocket:
            self.event_data = json.loads(message)
            await self.process_event()
            await websocket.send(self.response)

    async def process_event(self) -> None:
        func = self.events.get(self.event_data.get("event"))
        data = self.event_data.get("data")

        if not func:
            raise EventHandlerError()

        self.response = await func(data) if data else await func()
