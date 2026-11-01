"""LINE Messaging API webhook endpoint."""
import json
import web
from common.log import logger


class LineWebhookHandler:
    """POST /line/webhook - receives events from LINE Platform."""

    def POST(self):
        try:
            signature = web.ctx.env.get("HTTP_X_LINE_SIGNATURE", "")
            if not signature:
                logger.warning("[Line] missing X-Line-Signature")
                raise web.HTTPError(
                    "400 Bad Request",
                    {"Content-Type": "application/json"},
                    json.dumps({"status": "error", "message": "missing signature"}),
                )

            body = web.data().decode("utf-8")
            logger.info(f"[Line] webhook received ({len(body)} bytes)")

            from channel.channel_factory import create_channel
            ch = create_channel("line")
            ch.handle_webhook(body, signature)

            return "OK"
        except web.HTTPError:
            raise
        except Exception as e:
            logger.error(f"[Line] webhook error: {e}")
            raise web.HTTPError(
                "500 Internal Server Error",
                {"Content-Type": "application/json"},
                json.dumps({"status": "error", "message": str(e)}),
            )

    def GET(self):
        return json.dumps({"status": "ok", "message": "LINE webhook endpoint"})
