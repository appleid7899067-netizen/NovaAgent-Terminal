from channel.chat_channel import ChatChannel
from channel.line.line_message import LineMessage
from bridge.context import Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf


class LineChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.token = conf().get("line_channel_access_token", "")
        self.secret = conf().get("line_channel_secret", "")
        self.webhook_path = conf().get("line_webhook_path", "/line/webhook")
        self._api = None
        self._handler = None

    def _get_api(self):
        if self._api is None:
            from linebot.v3.messaging import (
                Configuration,
                ApiClient,
                MessagingApi,
            )
            cfg = Configuration(access_token=self.token)
            self._api = MessagingApi(ApiClient(cfg))
        return self._api

    def startup(self):
        logger.info("[Line] starting LineChannel")

    def send(self, reply: Reply, context: Context):
        user_id = context.get("from_user_id") or context.get("receiver")
        if not user_id:
            logger.warning("[Line] send: no user_id")
            return
        try:
            from linebot.v3.messaging import PushMessageRequest, TextMessage
            api = self._get_api()
            text = reply.content if isinstance(reply.content, str) else str(reply.content)
            api.push_message(PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=text)],
            ))
        except Exception as e:
            logger.error(f"[Line] send error: {e}")

    def handle_webhook(self, body: str, signature: str):
        if self._handler is None:
            from linebot.v3 import WebhookHandler
            self._handler = WebhookHandler(self.secret)

            @self._handler.add("message", message="text")
            def _on_text(event, destination=None):
                msg = LineMessage(event)
                self.produce(msg)

        try:
            self._handler.handle(body, signature)
        except Exception as e:
            logger.error(f"[Line] webhook error: {e}")
            raise
